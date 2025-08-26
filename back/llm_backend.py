"""
Label Studio ML backend built on top of a Whisper ASR pipeline.
This module exposes a simple model that can be served through the
``label-studio-ml`` framework.  The model uses a Hugging Face
``transformers`` pipeline to perform automatic speech recognition and
returns the transcribed text in Label Studio's expected format.
The class implements the two hooks expected by Label Studio:
``predict``
    Runs inference for a list of tasks and returns predictions.
``fit``
    Stub required by the base class; training is not implemented here.
The previous version of this file contained indentation mistakes and was
missing return statements which prevented the server from starting and,
consequently, Label Studio could not link to the backend.  This rewrite
provides a clean and fully functional implementation.
"""
from __future__ import annotations
from label_studio_ml.model import LabelStudioMLBase
from transformers import pipeline
import os
from typing import List, Dict, Any


class LLMInteractiveModel(LabelStudioMLBase):
    """Minimal ASR model for Label Studio integration."""
    
    def __init__(
        self,
        hf_token: str | None = None,
        model_name: str = "openai/whisper-small",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        # Configure authentication for private models if a token is provided
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token
        # Create the ASR pipeline.  ``use_auth_token`` is omitted because the
        # public ``openai/whisper-small`` checkpoint does not require it, but
        # the environment variable above allows the user to specify it when
        # needed.
        self.transcriber = pipeline(
            "automatic-speech-recognition",
            model=model_name,
        )

    # ------------------------------------------------------------------
    # Label Studio hooks
    # ------------------------------------------------------------------
    def predict(self, tasks: List[Dict[str, Any]], **kwargs: Any) -> List[Dict[str, Any]]:
        """Generate transcriptions for the supplied tasks."""
        results: List[Dict[str, Any]] = []
        for task in tasks:
            audio_path = task.get("data", {}).get("audio")
            if not audio_path:
                # Skip tasks without audio; Label Studio expects an empty list
                # for tasks that cannot be processed
                continue
            try:
                transcription = self.transcriber(audio_path)["text"]
            except Exception as exc:  # pragma: no cover - safety net
                transcription = f"[ERROR: {exc}]"
            results.append(
                {
                    "result": [
                        {
                            "from_name": "transcription",
                            "to_name": "audio",
                            "type": "textarea",
                            "value": {"text": [transcription]},
                        }
                    ]
                }
            )
        return results

    def fit(self, completions: List[Dict[str, Any]], workdir: str | None = None, **kwargs: Any) -> Dict[str, Any]:
        """Dummy ``fit`` implementation required by ``LabelStudioMLBase``."""
        # Training is out of scope for this demo backend; return an empty
        # dictionary to satisfy the interface.
        return {}
