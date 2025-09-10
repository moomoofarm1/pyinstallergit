import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from communication.server_manager import ServerManager, ServerType


@pytest.mark.parametrize(
    "server_type, venv_attr, setup_method",
    [
        (ServerType.DIARIZATION, "diarization_venv", "_setup_diarization_environment"),
        (ServerType.TRANSCRIPTION, "transcription_venv", "_setup_transcription_environment"),
    ],
)
def test_environment_created_on_start(tmp_path, server_type, venv_attr, setup_method):
    sm = ServerManager()
    # Redirect venv paths to temporary directory
    sm.venv_dir = tmp_path / "venvs"
    setattr(sm, venv_attr, sm.venv_dir / server_type.value)

    # Create dummy server script location
    work_dir = tmp_path / server_type.value
    work_dir.mkdir()
    (work_dir / "server.py").write_text("print('hello')")
    sm.configs[server_type].working_directory = work_dir

    mock_process = MagicMock()
    mock_process.pid = 1234
    mock_process.stdout = None
    mock_process.stderr = None

    dummy_script = work_dir / "server.py"

    with patch.object(sm, setup_method) as mock_setup_env, \
         patch.object(sm, "_ensure_runtime_dependencies"), \
         patch.object(sm, "_start_health_monitor"), \
         patch.object(sm, "_wait_for_server_startup", return_value=True), \
         patch.object(sm, "_prepare_server_startup", return_value=("python", str(dummy_script))), \
         patch("communication.server_manager.subprocess.Popen", return_value=mock_process):

        def create_dummy_env():
            python_path = getattr(sm, venv_attr) / ("Scripts" if os.name == "nt" else "bin") / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.touch()
        mock_setup_env.side_effect = create_dummy_env

        if server_type == ServerType.DIARIZATION:
            assert sm.start_diarization_server(with_label_studio=False)
        else:
            assert sm.start_transcription_server()

        mock_setup_env.assert_called_once()


def test_label_studio_environment_created_on_diarization_start(tmp_path):
    sm = ServerManager()
    sm.venv_dir = tmp_path / "venvs"
    sm.diarization_venv = sm.venv_dir / "diarization"
    sm.label_studio_venv = sm.venv_dir / "label_studio"

    # Create dummy server script location
    work_dir = tmp_path / "diarization"
    work_dir.mkdir()
    (work_dir / "server.py").write_text("print('hello')")
    sm.configs[ServerType.DIARIZATION].working_directory = work_dir

    mock_process = MagicMock()
    mock_process.pid = 1234
    mock_process.stdout = None
    mock_process.stderr = None

    dummy_script = work_dir / "server.py"

    with patch.object(sm, "_setup_diarization_environment") as mock_setup_diar, \
         patch.object(sm, "_setup_label_studio_environment") as mock_setup_ls, \
         patch.object(sm, "_start_label_studio_server", return_value=True), \
         patch.object(sm, "_ensure_runtime_dependencies"), \
         patch.object(sm, "_start_health_monitor"), \
         patch.object(sm, "_wait_for_server_startup", return_value=True), \
         patch.object(sm, "_prepare_server_startup", return_value=("python", str(dummy_script))), \
         patch("communication.server_manager.subprocess.Popen", return_value=mock_process):

        def create_dummy_diar_env():
            python_path = sm.diarization_venv / ("Scripts" if os.name == "nt" else "bin") / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.touch()

        def create_dummy_ls_env():
            python_path = sm.label_studio_venv / ("Scripts" if os.name == "nt" else "bin") / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.touch()

        mock_setup_diar.side_effect = create_dummy_diar_env
        mock_setup_ls.side_effect = create_dummy_ls_env

        assert sm.start_diarization_server(with_label_studio=True)
        mock_setup_ls.assert_called_once()
