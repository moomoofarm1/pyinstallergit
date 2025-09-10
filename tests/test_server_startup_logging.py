import sys
import logging

from communication.server_manager import ServerManager, ServerType

def test_logs_subprocess_output_on_startup_failure(tmp_path, caplog, monkeypatch):
    script = tmp_path / "fail.py"
    script.write_text(
        "import sys\nprint('stdout msg')\nprint('stderr msg', file=sys.stderr)\nsys.exit(1)\n"
    )

    sm = ServerManager()

    def fake_prepare(self, server_type):
        return sys.executable, str(script)

    monkeypatch.setattr(ServerManager, "_prepare_server_startup", fake_prepare)
    monkeypatch.setattr(ServerManager, "_wait_for_server_startup", lambda self, st, t: False)

    sm.configs[ServerType.DIARIZATION].working_directory = tmp_path

    with caplog.at_level(logging.ERROR):
        assert sm._start_server(ServerType.DIARIZATION) is False

    info = sm.get_server_info(ServerType.DIARIZATION)
    assert info is not None and info.state.name == "ERROR"
    assert "stdout msg" in info.error_message
    assert "stderr msg" in info.error_message
