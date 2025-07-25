# ===================== src/finetune_diarization.py =====================
import os
from datasets import load_dataset, Audio
from transformers import AutoProcessor, AutoModelForAudioFrameClassification, TrainingArguments, Trainer
import torch
from metrics import diarization_metrics
from data_io import make_rttm_from_segments, segments_from_dataset

MODEL_ID = "syvai/speaker-diarization-3.1"


def prepare_dataset(sample_hours=0.1):
    """Download a tiny public dataset with speaker labels (AMI small subset via HF)."""
    ds = load_dataset("ami_iwslt/ami", "sdm", split="train[:2%]")  # tiny subset
    # ensure audio column
    if "audio" not in ds.column_names:
        ds = ds.cast_column("audio", Audio())
    return ds


def collate_fn(batch, processor):
    inputs = [b["audio"]["array"] for b in batch]
    sr = batch[0]["audio"]["sampling_rate"]
    # Dummy frame labels built earlier
    labels = [torch.tensor(b["frame_labels"]) for b in batch]
    encoded = processor(inputs, sampling_rate=sr, return_tensors="pt", padding=True)
    max_len = max(l.shape[0] for l in labels)
    y = torch.stack([torch.nn.functional.pad(l, (0, max_len - l.shape[0]), value=-100) for l in labels])
    encoded["labels"] = y
    return encoded


def create_frame_labels(example, frame_hz=50):
    """
    Convert segment-level speaker annotations to frame-level ids.
    Expect example["segments"] = list of {"start","end","speaker_id"} in seconds.
    """
    duration = example["audio"]["array"].shape[0] / example["audio"]["sampling_rate"]
    n_frames = int(duration * frame_hz)
    labels = torch.full((n_frames,), -100, dtype=torch.long)
    for seg in example.get("segments", []):
        s = int(seg["start"] * frame_hz)
        e = int(seg["end"] * frame_hz)
        labels[s:e] = seg["speaker_id"]
    example["frame_labels"] = labels.numpy()
    return example


def run_finetune(epochs, batch_size, lr, output_dir, sample_hours):
    os.makedirs(output_dir, exist_ok=True)
    ds = prepare_dataset(sample_hours)

    # Build fake segments if none available (AMI has them, otherwise we fallback)
    if "segments" not in ds.column_names:
        ds = ds.map(lambda ex: {"segments": segments_from_dataset(ex)}, desc="gen segments")

    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForAudioFrameClassification.from_pretrained(MODEL_ID)

    ds = ds.map(lambda ex: create_frame_labels(ex), desc="frame labels")
    ds_train = ds.shuffle(seed=42).select(range(min(20, len(ds))))
    ds_eval = ds.shuffle(seed=123).select(range(min(5, len(ds))))

    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=lr,
        num_train_epochs=epochs,
        logging_steps=5,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        report_to=[]
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_train,
        eval_dataset=ds_eval,
        data_collator=lambda b: collate_fn(b, processor),
        compute_metrics=lambda p: diarization_metrics(p, frame_hz=50)
    )

    trainer.train()
    trainer.evaluate()
    trainer.save_model(output_dir)

    # Export RTTM for eval set
    rttm_path = os.path.join(output_dir, "pred_eval.rttm")
    make_rttm_from_segments(ds_eval, rttm_path)
    print(f"Saved predictions RTTM to {rttm_path}")
