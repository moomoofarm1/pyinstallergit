import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from communication.server_manager import ServerManager, ServerType


def test_diarization_environment_created_on_start(tmp_path):
    sm = ServerManager()
    sm.venv_dir = tmp_path / "venvs"
    sm.diarization_venv = sm.venv_dir / "diarization"
    sm.labelstudio_venv = sm.venv_dir / "labelstudio"

    work_dir = tmp_path / "diarization"
    work_dir.mkdir()
    (work_dir / "server.py").write_text("print('hello')")
    sm.configs[ServerType.DIARIZATION].working_directory = work_dir

    mock_process = MagicMock()
    mock_process.pid = 1234
    mock_process.stdout = None
    mock_process.stderr = None
    dummy_script = work_dir / "server.py"

    with patch.object(sm, "_setup_diarization_environment") as mock_setup_backend, \
         patch.object(sm, "_setup_labelstudio_environment") as mock_setup_label, \
         patch.object(sm, "_ensure_runtime_dependencies"), \
         patch.object(sm, "_start_health_monitor"), \
         patch.object(sm, "_wait_for_server_startup", return_value=True), \
         patch.object(sm, "_prepare_server_startup", return_value=("python", str(dummy_script))), \
         patch.object(sm, "_start_label_studio_server", return_value=True), \
         patch("communication.server_manager.subprocess.Popen", return_value=mock_process):

        def create_backend_env():
            python_path = sm.diarization_venv / ("Scripts" if os.name == "nt" else "bin") / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.touch()

        def create_label_env():
            python_path = sm.labelstudio_venv / ("Scripts" if os.name == "nt" else "bin") / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.touch()

        mock_setup_backend.side_effect = create_backend_env
        mock_setup_label.side_effect = create_label_env

        assert sm.start_diarization_server(with_label_studio=True)
        mock_setup_backend.assert_called_once()
        mock_setup_label.assert_called_once()


def test_transcription_environment_created_on_start(tmp_path):
    sm = ServerManager()
    sm.venv_dir = tmp_path / "venvs"
    sm.transcription_venv = sm.venv_dir / "transcription"

    work_dir = tmp_path / "transcription"
    work_dir.mkdir()
    (work_dir / "server.py").write_text("print('hello')")
    sm.configs[ServerType.TRANSCRIPTION].working_directory = work_dir

    mock_process = MagicMock()
    mock_process.pid = 1234
    mock_process.stdout = None
    mock_process.stderr = None
    dummy_script = work_dir / "server.py"

    with patch.object(sm, "_setup_transcription_environment") as mock_setup_env, \
         patch.object(sm, "_ensure_runtime_dependencies"), \
         patch.object(sm, "_start_health_monitor"), \
         patch.object(sm, "_wait_for_server_startup", return_value=True), \
         patch.object(sm, "_prepare_server_startup", return_value=("python", str(dummy_script))), \
         patch("communication.server_manager.subprocess.Popen", return_value=mock_process):

        def create_dummy_env():
            python_path = sm.transcription_venv / ("Scripts" if os.name == "nt" else "bin") / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.touch()

        mock_setup_env.side_effect = create_dummy_env

        assert sm.start_transcription_server()
        mock_setup_env.assert_called_once()
