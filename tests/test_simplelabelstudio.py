import os
from unittest import mock

import simplelabelstudio as sls


@mock.patch("simplelabelstudio.messagebox.showinfo")
@mock.patch("simplelabelstudio.subprocess.Popen")
@mock.patch("simplelabelstudio.subprocess.run")
def test_create_env(mock_run, mock_popen, mock_info, tmp_path, monkeypatch):
    """Creating an environment should invoke uv commands and start server."""
    # Ensure a predictable directory is used
    monkeypatch.setattr(sls.tempfile, "mkdtemp", lambda prefix: str(tmp_path))

    sls.env_dir = None
    sls.server_process = None

    sls.create_env()

    # The environment directory should be recorded
    assert sls.env_dir == str(tmp_path)

    # uv venv and uv pip install should be called
    expected = [
        mock.call(["uv", "venv", str(tmp_path)], check=True),
        mock.call(["uv", "pip", "install", "label-studio"], check=True, cwd=str(tmp_path)),
    ]
    assert mock_run.call_args_list[:2] == expected

    # Server process should be started
    mock_popen.assert_called_once()


@mock.patch("simplelabelstudio.messagebox.showinfo")
@mock.patch("simplelabelstudio.subprocess.run")
@mock.patch("simplelabelstudio.shutil.which", return_value="/usr/bin/uv")
def test_check_env(mock_which, mock_run, mock_info, tmp_path, monkeypatch):
    """Check should report uv path and installation status."""
    # Pretend an environment exists
    sls.env_dir = str(tmp_path)
    python_exe = os.path.join(str(tmp_path), "bin", "python")

    # Simulate successful check of label-studio
    mock_run.return_value = mock.Mock()

    result = sls.check_env()

    assert "/usr/bin/uv" in result
    assert f"env dir: {tmp_path}" in result
    assert "label-studio installed: True" in result

    # Ensure subprocess.run was called with the expected python executable
    mock_run.assert_called_with(
        [python_exe, "-m", "label_studio", "--version"],
        check=True,
        stdout=mock.ANY,
        stderr=mock.ANY,
    )


@mock.patch("simplelabelstudio.messagebox.showinfo")
def test_stop_and_delete(mock_info, tmp_path, monkeypatch):
    """Stopping and deleting should clean up resources."""
    # Set up fake environment and running process
    sls.env_dir = str(tmp_path)
    fake_process = mock.Mock()
    sls.server_process = fake_process

    # Patch rmtree so no real deletion happens
    with mock.patch("simplelabelstudio.shutil.rmtree") as mock_rm:
        sls.delete_env()

    # Process should be terminated
    fake_process.terminate.assert_called_once()

    # Environment should be removed
    mock_rm.assert_called_with(str(tmp_path))
    assert sls.env_dir is None
    assert sls.server_process is None
