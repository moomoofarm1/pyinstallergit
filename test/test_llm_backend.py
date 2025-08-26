import sys
from pathlib import Path
import os
import types

# Ensure project root is on path
sys.path.append(str(Path(__file__).resolve().parents[1]))


def dummy_pipeline(task, model):
    assert task == "automatic-speech-recognition"
    assert model == "openai/whisper-small"
    return lambda path: {"text": f"transcribed {path}"}


def prepare_model(monkeypatch):
    model_module = types.SimpleNamespace(LabelStudioMLBase=object)
    ls_module = types.ModuleType("label_studio_ml")
    ls_module.model = model_module
    monkeypatch.setitem(sys.modules, "label_studio_ml", ls_module)
    monkeypatch.setitem(sys.modules, "label_studio_ml.model", model_module)
    import back.llm_backend as backend
    monkeypatch.setattr(backend, "pipeline", dummy_pipeline)
    return backend.LLMInteractiveModel


def test_predict_transcribes_audio(monkeypatch):
    LLMInteractiveModel = prepare_model(monkeypatch)
    model = LLMInteractiveModel()
    tasks = [{"data": {"audio": "clip.wav"}}, {"data": {}}]
    result = model.predict(tasks)
    assert result == [
        {
            "result": [
                {
                    "from_name": "transcription",
                    "to_name": "audio",
                    "type": "textarea",
                    "value": {"text": ["transcribed clip.wav"]},
                }
            ]
        }
    ]


def test_fit_returns_empty_dict(monkeypatch):
    LLMInteractiveModel = prepare_model(monkeypatch)
    model = LLMInteractiveModel()
    assert model.fit([], None) == {}


def test_hf_token_sets_env(monkeypatch):
    LLMInteractiveModel = prepare_model(monkeypatch)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    LLMInteractiveModel(hf_token="xyz")
    assert os.environ["HF_TOKEN"] == "xyz"
