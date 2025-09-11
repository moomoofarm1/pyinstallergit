import os
from unittest import mock

import simplelabelstudio as sls


@mock.patch("simplelabelstudio.messagebox.showinfo")
@mock.patch("simplelabelstudio.subprocess.Popen")
@mock.patch("simplelabelstudio.subprocess.run")
def test_start_env(mock_run, mock_popen, mock_info, tmp_path, monkeypatch):
    """Start button should create env, install package and launch server."""

    monkeypatch.setattr(sls.tempfile, "mkdtemp", lambda prefix: str(tmp_path))

    sls.env_dir = None
    sls.server_process = None


    sls.start_env()

    assert sls.env_dir == str(tmp_path)


    expected = [
        mock.call(["uv", "venv", str(tmp_path)], check=True),
        mock.call(["uv", "pip", "install", "label-studio"], check=True, cwd=str(tmp_path)),
    ]
    assert mock_run.call_args_list[:2] == expected



    mock_popen.assert_called_once()


@mock.patch("simplelabelstudio.messagebox.showinfo")
@mock.patch("simplelabelstudio.subprocess.run")

def test_check_env(mock_run, mock_info, tmp_path):
    """Check reports env path and installation status."""
    sls.env_dir = str(tmp_path)
    python_exe = os.path.join(str(tmp_path), "bin", "python")


    mock_run.return_value = mock.Mock()

    result = sls.check_env()


    assert f"env dir: {tmp_path}" in result
    assert "label-studio installed: True" in result


    mock_run.assert_called_with(
        [python_exe, "-m", "label_studio", "--version"],
        check=True,
        stdout=mock.ANY,
        stderr=mock.ANY,
    )


@mock.patch("simplelabelstudio.messagebox.showinfo")

def test_stop_env(mock_info, tmp_path):
    """Stop should terminate server and delete environment."""

    sls.env_dir = str(tmp_path)
    fake_process = mock.Mock()
    sls.server_process = fake_process


    with mock.patch("simplelabelstudio.shutil.rmtree") as mock_rm:
        sls.stop_env()

    fake_process.terminate.assert_called_once()

    mock_rm.assert_called_with(str(tmp_path))
    assert sls.env_dir is None
    assert sls.server_process is None
