# ===================== src/active_learning_diarization.py =====================
import os
import random
from label_studio_sdk import Client
from transformers import AutoProcessor, AutoModelForAudioFrameClassification
import torch
from data_io import (download_unlabeled_pool, annotate_segments_interactive,
                     segments_to_frame_labels)
from metrics import diarization_metrics

MODEL_ID = "syvai/speaker-diarization-3.1"


def run_active_learning(iterations, query_k, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForAudioFrameClassification.from_pretrained(MODEL_ID)

    labeled = []  # list of dicts with audio + frame_labels
    pool = download_unlabeled_pool(limit=30)

    for it in range(iterations):
        # Fine-tune on current labeled set if any
        if labeled:
            train_batch = segments_to_frame_labels(labeled, processor)
            loss = _one_step_update(model, train_batch)
            print(f"[IT {it}] fine-tune loss={loss:.4f}, labeled={len(labeled)}")

        # Score pool with uncertainty
        scores = []
        for ex in pool:
            inputs = processor(ex["audio"]["array"], sampling_rate=ex["audio"]["sampling_rate"], return_tensors="pt")
            with torch.no_grad():
                logits = model(**inputs).logits
            prob = torch.softmax(logits, -1).max().item()
            scores.append((1 - prob))  # uncertainty
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


def _one_step_update(model, batch):
    model.train()
    optim = torch.optim.AdamW(model.parameters(), lr=1e-5)
    optim.zero_grad()
    out = model(**batch)
    out.loss.backward()
    optim.step()
    return out.loss.item()
