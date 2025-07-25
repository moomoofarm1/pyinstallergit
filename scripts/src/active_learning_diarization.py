# ===================== src/active_learning_diarization.py =====================
import os
from label_studio_sdk import Client
from transformers import AutoProcessor, AutoModelForAudioFrameClassification
import torch
from torch.utils.data import DataLoader
from data_io import (
    download_unlabeled_pool,
    annotate_segments_interactive,
    segments_to_frame_labels,
    annotate_segments_labelstudio,
)
from metrics import diarization_metrics

MODEL_ID = "syvai/speaker-diarization-3.1"


def run_active_learning(
    iterations,
    query_k,
    output_dir,
    batch_size=2,
    lr=1e-5,
    fine_tune_epochs=1,
    ls_url=None,
    ls_token=None,
    project_id=None,
    model_id=MODEL_ID,
):
    os.makedirs(output_dir, exist_ok=True)
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForAudioFrameClassification.from_pretrained(model_id)

    client = None
    project = None
    if ls_token and project_id:
        client = Client(url=ls_url, api_key=ls_token)
        project = client.get_project(project_id)

    labeled = []  # list of dicts with audio + frame_labels
    pool = download_unlabeled_pool(limit=30)

    for it in range(iterations):
        # Fine-tune on current labeled set if any
        if labeled:
            loss = _fine_tune_model(
                model, processor, labeled,
                epochs=fine_tune_epochs,
                batch_size=batch_size,
                lr=lr,
            )
            print(f"[IT {it}] fine-tune loss={loss:.4f}, labeled={len(labeled)}")

        # Score pool with uncertainty
        scores = []
        for ex in pool:
            scores.append(_uncertainty_score(model, processor, ex))
        # pick top-k uncertain
        idxs = sorted(range(len(pool)), key=lambda i: scores[i], reverse=True)[:query_k]
        to_label = [pool[i] for i in idxs]

        # Send to Label Studio or simple CLI labeling
        if project:
            newly_labeled = annotate_segments_labelstudio(to_label, project)
        else:
            newly_labeled = annotate_segments_interactive(to_label)
        labeled.extend(newly_labeled)

        # remove from pool
        pool = [p for j, p in enumerate(pool) if j not in idxs]

    # Final evaluation (if we had GT in labeled examples)
    if any("frame_labels_true" in ex for ex in labeled):
        preds = []
        trues = []
        for ex in labeled:
            preds.append(ex["frame_labels"])
            trues.append(ex["frame_labels_true"])
        metric = diarization_metrics((torch.tensor(preds), torch.tensor(trues)), frame_hz=50)
        print("Final AL metric:", metric)

    model.save_pretrained(output_dir)


def _fine_tune_model(model, processor, labeled, epochs, batch_size, lr):
    """Fine-tune on labeled segments using a DataLoader."""
    loader = DataLoader(
        labeled,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda b: segments_to_frame_labels(b, processor),
    )
    optim = torch.optim.AdamW(model.parameters(), lr=lr)
    loss = None
    for _ in range(epochs):
        for batch in loader:
            model.train()
            optim.zero_grad()
            out = model(**batch)
            out.loss.backward()
            optim.step()
            loss = out.loss.item()
    return loss


def _uncertainty_score(model, processor, example):
    inputs = processor(example["audio"]["array"], sampling_rate=example["audio"]["sampling_rate"], return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits.squeeze(0)
    probs = torch.softmax(logits, dim=-1)
    mean_conf = probs.max(dim=-1).values.mean().item()
    return 1 - mean_conf


