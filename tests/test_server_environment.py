import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from communication.server_manager import ServerManager, ServerType


def _create_dummy_env(path: Path) -> None:
    python_path = path / ("Scripts" if os.name == "nt" else "bin") / "python"
    python_path.parent.mkdir(parents=True, exist_ok=True)
    python_path.touch()


def test_diarization_environment_created_on_start(tmp_path):
    sm = ServerManager()
    sm.venv_dir = tmp_path / "venvs"
    sm.label_studio_venv = sm.venv_dir / "label_studio"
    sm.diarization_venv = sm.venv_dir / "diarization"

    work_dir = tmp_path / "diarization"
    work_dir.mkdir()
    (work_dir / "server.py").write_text("print('hello word')")
    sm.configs[ServerType.DIARIZATION].working_directory = work_dir

    mock_process = MagicMock(pid=1234, stdout=None, stderr=None)
    dummy_script = work_dir / "server.py"

    with patch.object(sm, "_setup_label_studio_environment") as mock_ls_env, \
         patch.object(sm, "_setup_diarization_backend_environment") as mock_back_env, \
         patch.object(sm, "_start_label_studio_server", return_value=True), \
         patch.object(sm, "_ensure_runtime_dependencies"), \
         patch.object(sm, "_start_health_monitor"), \
         patch.object(sm, "_wait_for_server_startup", return_value=True), \
         patch.object(sm, "_prepare_server_startup", return_value=("python", str(dummy_script))), \
         patch("communication.server_manager.subprocess.Popen", return_value=mock_process):

        mock_ls_env.side_effect = lambda: _create_dummy_env(sm.label_studio_venv)
        mock_back_env.side_effect = lambda: _create_dummy_env(sm.diarization_venv)

        assert sm.start_diarization_server(with_label_studio=True)

        mock_ls_env.assert_called_once()
        mock_back_env.assert_called_once()


def test_transcription_environment_created_on_start(tmp_path):
    sm = ServerManager()
    sm.venv_dir = tmp_path / "venvs"
    sm.transcription_venv = sm.venv_dir / "transcription"

    work_dir = tmp_path / "transcription"
    work_dir.mkdir()
    (work_dir / "server.py").write_text("print('hello')")
    sm.configs[ServerType.TRANSCRIPTION].working_directory = work_dir

    mock_process = MagicMock(pid=1234, stdout=None, stderr=None)
    dummy_script = work_dir / "server.py"

    with patch.object(sm, "_setup_transcription_environment") as mock_setup_env, \
         patch.object(sm, "_ensure_runtime_dependencies"), \
         patch.object(sm, "_start_health_monitor"), \
         patch.object(sm, "_wait_for_server_startup", return_value=True), \
         patch.object(sm, "_prepare_server_startup", return_value=("python", str(dummy_script))), \
         patch("communication.server_manager.subprocess.Popen", return_value=mock_process):

        mock_setup_env.side_effect = lambda: _create_dummy_env(sm.transcription_venv)

        assert sm.start_transcription_server()

        mock_setup_env.assert_called_once()

