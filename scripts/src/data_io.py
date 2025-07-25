# ===================== src/data_io.py =====================
import torch
from datasets import load_dataset, Audio
import random

def download_unlabeled_pool(limit=30):
    ds = load_dataset("ami_iwslt/ami", "sdm", split="train[:5%]")
    ds = ds.cast_column("audio", Audio())
    ds = ds.shuffle(seed=123)
    return [ds[i] for i in range(min(limit, len(ds)))]


def annotate_segments_interactive(items):
    """Placeholder: simulate human labeling (2 speakers random). Replace with Label Studio client."""
    labeled = []
    for ex in items:
        duration = ex["audio"]["array"].shape[0] / ex["audio"]["sampling_rate"]
        # random segments
        n = random.randint(1, 3)
        segs = []
        for _ in range(n):
            s = random.uniform(0, duration - 0.5)
            e = min(duration, s + random.uniform(0.3, 1.0))
            segs.append({"start": s, "end": e, "speaker_id": random.randint(0, 1)})
        ex["segments"] = segs
        labeled.append(ex)
    return labeled


def segments_from_dataset(ex):
    # Fallback: make fake segments
    dur = ex["audio"]["array"].shape[0] / ex["audio"]["sampling_rate"]
    mid = dur / 2
    return [
        {"start": 0.0, "end": mid, "speaker_id": 0},
        {"start": mid, "end": dur, "speaker_id": 1},
    ]


def segments_to_frame_labels(examples, processor, frame_hz=50):
    arrays = [e["audio"]["array"] for e in examples]
    sr = examples[0]["audio"]["sampling_rate"]
    enc = processor(arrays, sampling_rate=sr, return_tensors="pt", padding=True)
    labels = []
    for e in examples:
        duration = e["audio"]["array"].shape[0] / sr
        n_frames = int(duration * frame_hz)
        y = torch.full((n_frames,), -100, dtype=torch.long)
        for seg in e["segments"]:
            s = int(seg["start"] * frame_hz)
            en = int(seg["end"] * frame_hz)
            y[s:en] = seg["speaker_id"]
        labels.append(y)
    max_len = max(l.shape[0] for l in labels)
    ypad = torch.stack([torch.nn.functional.pad(l, (0, max_len-l.shape[0]), value=-100) for l in labels])
    enc["labels"] = ypad
    return enc


def make_rttm_from_segments(ds, out_path):
    """Write simple RTTM file for predictions (or ground truth)."""
    with open(out_path, "w") as f:
        for i, ex in enumerate(ds):
            utt_id = f"utt{i}"
            for seg in ex.get("segments", []):
                dur = seg["end"] - seg["start"]
                speaker = f"spk{seg['speaker_id']}"
                f.write(f"SPEAKER {utt_id} 1 {seg['start']:.3f} {dur:.3f} <NA> <NA> {speaker} <NA>\n")
