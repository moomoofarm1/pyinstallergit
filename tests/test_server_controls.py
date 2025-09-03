from pathlib import Path
from unittest.mock import patch, MagicMock

from communication.server_manager import ServerManager, ServerType
from ui.main_window import AudioProcessingApp


def test_prepare_server_startup_creates_env(tmp_path, monkeypatch):
    """ServerManager should create environment automatically when starting."""
    manager = ServerManager()
    manager.diarization_venv = tmp_path / "dia"

    called = {}

    def fake_setup():
        called["setup"] = True
        bin_dir = manager.diarization_venv / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "python").touch()

    monkeypatch.setattr(manager, "_setup_diarization_environment", fake_setup)

    python_path, script_path = manager._prepare_server_startup(ServerType.DIARIZATION)

    assert called.get("setup") is True
    assert Path(python_path).exists()
    assert script_path.endswith("diarization/server.py")


@patch("tkinter.Tk")
def test_audio_processing_app_stop_servers(mock_tk):
    """Stop server methods should invoke ServerManager and update status."""

    def fake_setup_ui(self):
        class DummyVar:
            def __init__(self):
                self.value = ""

            def set(self, v):
                self.value = v

        self.diarization_status_var = DummyVar()
        self.transcription_status_var = DummyVar()
        self.start_diarization_server_btn = MagicMock()
        self.stop_diarization_server_btn = MagicMock()
        self.start_transcription_server_btn = MagicMock()
        self.stop_transcription_server_btn = MagicMock()

    with patch.object(AudioProcessingApp, "setup_ui", fake_setup_ui), \
         patch.object(AudioProcessingApp, "setup_logging_display", return_value=None):
        app = AudioProcessingApp()
        with patch.object(app.server_manager, "stop_diarization_server") as mock_stop_d, \
             patch.object(app.server_manager, "stop_transcription_server") as mock_stop_t:
            app.stop_diarization_server()
            app.stop_transcription_server()
            mock_stop_d.assert_called_once()
            mock_stop_t.assert_called_once()
            assert app.diarization_status_var.value == "Server: Stopped | Browser: Not opened"
            assert app.transcription_status_var.value == "Server: Stopped | Browser: Not opened"
