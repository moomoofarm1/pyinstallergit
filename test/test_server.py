import sys
from pathlib import Path
import types
import importlib

# Ensure project root is on path
sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_server_initialises_app(monkeypatch):
    """Server should expose app created by init_app with configured model."""
    sentinel_app = object()
    def init_app(model):
        init_app.model = model
        return sentinel_app

    # Create fake label_studio_ml package with api and model submodules
    model_module = types.SimpleNamespace(LabelStudioMLBase=object)
    ls_module = types.ModuleType("label_studio_ml")
    ls_module.api = types.SimpleNamespace(init_app=init_app)
    ls_module.model = model_module
    monkeypatch.setitem(sys.modules, "label_studio_ml", ls_module)
    monkeypatch.setitem(sys.modules, "label_studio_ml.api", ls_module.api)
    monkeypatch.setitem(sys.modules, "label_studio_ml.model", model_module)

    import back.llm_backend as backend

    class DummyModel:
        def __init__(self, hf_token=None, model_name="openai/whisper-small"):
            self.hf_token = hf_token
            self.model_name = model_name

    monkeypatch.setattr(backend, "LLMInteractiveModel", DummyModel)
    monkeypatch.setenv("HF_TOKEN", "abc123")

    if "server" in sys.modules:
        del sys.modules["server"]
    server = importlib.import_module("server")

    assert server.app is sentinel_app
    assert isinstance(init_app.model, DummyModel)
    assert init_app.model.hf_token == "abc123"
    assert init_app.model.model_name == "openai/whisper-small"


if __name__ == "__main__":  # pragma: no cover - manual test runner
    import pytest
    raise SystemExit(pytest.main([__file__]))
