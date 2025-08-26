"""
FastAPI application exposing the Label Studio ML backend.
The server simply wraps :class:`back.llm_backend.LLMInteractiveModel`
into a FastAPI app using ``label-studio-ml``'s helper ``init_app``.  When
running, this server can be registered with a local Label Studio instance
as an ML backend.
"""
from __future__ import annotations
import os
from label_studio_ml.api import init_app
from back.llm_backend import LLMInteractiveModel

# ---------------------------------------------------------------------------
# Model initialisation
# ---------------------------------------------------------------------------
# Allow users to pass a Hugging Face token via the environment.  Some
# Whisper checkpoints are gated and require authentication.
HF_TOKEN = os.getenv("HF_TOKEN")

# Instantiate the Whisper based backend model
model = LLMInteractiveModel(
    hf_token=HF_TOKEN,
    model_name="openai/whisper-small",
)

# Wrap the model into a FastAPI app that exposes the ``/predict`` and
# ``/train`` endpoints expected by Label Studio.
app = init_app(model=model)
