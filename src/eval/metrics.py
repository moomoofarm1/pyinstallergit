# ===================== src/metrics.py =====================
import torch

def diarization_metrics(pred_tuple, frame_hz=50):
    """
    Compute simple DER (diarization error rate) approximation from frame labels.
    pred_tuple: Trainer passes EvalPrediction with logits & labels, but we allow (preds, labels) as well.
    """
    if isinstance(pred_tuple, tuple):
        preds, labels = pred_tuple
    else:
        logits, labels = pred_tuple.predictions, pred_tuple.label_ids
        preds = torch.from_numpy(logits).argmax(-1)
        labels = torch.from_numpy(labels)

    mask = labels != -100
    total = mask.sum().item()
    if total == 0:
        return {"DER": 0.0}
    errors = (preds[mask] != labels[mask]).sum().item()
    der = errors / total
    return {"DER": der}
