import sys
from pathlib import Path
import pytest

# Ensure project root is on path for importing 'front'
sys.path.append(str(Path(__file__).resolve().parents[1]))

from front import gui

def test_run_gui_headless(monkeypatch, capsys):
    """Ensure run_gui handles TclError gracefully."""
    def fake_Tk():
        raise gui.tk.TclError("no display name and no $DISPLAY")
    monkeypatch.setattr(gui.tk, "Tk", fake_Tk)
    gui.run_gui()
    captured = capsys.readouterr()
    assert "Tkinter GUI cannot be started" in captured.out


if __name__ == "__main__":  # pragma: no cover - manual test runner
    raise SystemExit(pytest.main([__file__]))
