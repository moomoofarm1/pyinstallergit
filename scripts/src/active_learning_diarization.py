# ===================== src/active_learning_diarization.py =====================
import os
from label_studio_sdk import Client
from transformers import AutoProcessor, AutoModelForAudioFrameClassification
import torch
from data_io import (download_unlabeled_pool, annotate_segments_interactive,
                     segments_to_frame_labels)
from metrics import diarization_metrics

MODEL_ID = "syvai/speaker-diarization-3.1"


def run_active_learning(iterations, query_k, output_dir, batch_size=2, lr=1e-5, fine_tune_epochs=1):
    os.makedirs(output_dir, exist_ok=True)
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForAudioFrameClassification.from_pretrained(MODEL_ID)

    labeled = []  # list of dicts with audio + frame_labels
    pool = download_unlabeled_pool(limit=30)

    for it in range(iterations):
        # Fine-tune on current labeled set if any
        if labeled:
            loss = None
            for _ in range(fine_tune_epochs):
                for batch in _create_batches(labeled, batch_size, processor):
                    loss = _one_step_update(model, batch, lr)
            print(f"[IT {it}] fine-tune loss={loss:.4f}, labeled={len(labeled)}")

        # Score pool with uncertainty
        scores = []
        for ex in pool:
            scores.append(_uncertainty_score(model, processor, ex))
        # pick top-k uncertain
        idxs = sorted(range(len(pool)), key=lambda i: scores[i], reverse=True)[:query_k]
        to_label = [pool[i] for i in idxs]

        # Send to Label Studio or simple CLI labeling
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


def _one_step_update(model, batch, lr=1e-5):
    model.train()
    optim = torch.optim.AdamW(model.parameters(), lr=lr)
    optim.zero_grad()
    out = model(**batch)
    out.loss.backward()
    optim.step()
    return out.loss.item()


def _uncertainty_score(model, processor, example):
    inputs = processor(example["audio"]["array"], sampling_rate=example["audio"]["sampling_rate"], return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits.squeeze(0)
    probs = torch.softmax(logits, dim=-1)
    mean_conf = probs.max(dim=-1).values.mean().item()
    return 1 - mean_conf


def _create_batches(examples, batch_size, processor):
    for i in range(0, len(examples), batch_size):
        yield segments_to_frame_labels(examples[i:i + batch_size], processor)
