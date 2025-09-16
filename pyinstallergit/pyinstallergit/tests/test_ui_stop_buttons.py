from unittest.mock import MagicMock

from ui.main_window import AudioProcessingApp


class DummyVar:
    def __init__(self):
        self.value = ""

    def set(self, val):
        self.value = val


def test_stop_buttons_call_server_manager():
    app = AudioProcessingApp.__new__(AudioProcessingApp)
    app.server_manager = MagicMock()
    app.diarization_status_var = DummyVar()
    app.diarization_start_btn = MagicMock()
    app.diarization_stop_btn = MagicMock()
    app.stop_diarization_server()
    app.server_manager.stop_diarization_server.assert_called_once()

    app.server_manager = MagicMock()
    app.transcription_status_var = DummyVar()
    app.transcription_start_btn = MagicMock()
    app.transcription_stop_btn = MagicMock()
    app.stop_transcription_server()
    app.server_manager.stop_transcription_server.assert_called_once()
