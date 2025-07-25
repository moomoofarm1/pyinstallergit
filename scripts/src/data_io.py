# ===================== src/data_io.py =====================
import os
import random
import tempfile
from typing import List, Dict

import torch

def download_unlabeled_pool(limit: int = 30):
    """Download a small pool of unlabeled audio examples."""
    from datasets import load_dataset, Audio

    ds = load_dataset("ami_iwslt/ami", "sdm", split="train[:5%]")
    ds = ds.cast_column("audio", Audio())
    ds = ds.shuffle(seed=123)
    return [ds[i] for i in range(min(limit, len(ds)))]


def annotate_segments_interactive(items: List[Dict]):
    """Simple CLI labeling fallback generating random segments."""
    labeled = []
    for ex in items:
        duration = ex["audio"]["array"].shape[0] / ex["audio"]["sampling_rate"]
        n = random.randint(1, 3)
        segs = []
        for _ in range(n):
            s = random.uniform(0, duration - 0.5)
            e = min(duration, s + random.uniform(0.3, 1.0))
            segs.append({"start": s, "end": e, "speaker_id": random.randint(0, 1)})
        ex["segments"] = segs
        labeled.append(ex)
    return labeled


def annotate_segments_labelstudio(items: List[Dict], project) -> List[Dict]:
    """Send audio segments to Label Studio and wait for annotations."""
    from scipy.io import wavfile

    tasks = []
    paths = []
    for idx, ex in enumerate(items):
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        wavfile.write(path, ex["audio"]["sampling_rate"], ex["audio"]["array"])
        tasks.append({"data": {"audio": path}})
        paths.append(path)

    task_ids = project.import_tasks(tasks)
    print(f"Imported {len(task_ids)} tasks to project {project.id}. Label them in the UI then press Enter to continue.")
    input("Press Enter after labeling...")

    labeled = []
    for tid, ex, audio_path in zip(task_ids, items, paths):
        task = project.get_task(tid)
        anns = task.get("annotations") or []
        if not anns:
            continue
        segments = []
        for res in anns[0].get("result", []):
            if res.get("type") == "labels":
                seg = {
                    "start": res["value"].get("start", 0.0),
                    "end": res["value"].get("end", 0.0),
                    "speaker_id": _label_to_id(res["value"].get("labels", ["0"])[0]),
                }
                segments.append(seg)
        ex["segments"] = segments
        labeled.append(ex)
        os.remove(audio_path)
    return labeled


def _label_to_id(label: str) -> int:
    try:
        return int(label.strip().split()[-1])
    except Exception:
        digits = "".join(ch for ch in label if ch.isdigit())
        return int(digits) if digits else 0


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
