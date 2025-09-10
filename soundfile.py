"""Minimal soundfile compatibility layer.

This module provides a very small subset of the :mod:`soundfile` interface
implemented using :mod:`scipy.io.wavfile`.  The real soundfile package is a
heavy dependency that is not always available in constrained environments, so
these helpers offer just enough functionality for the test-suite and example
code.  Only the :func:`write` and :func:`read` functions are implemented.
"""

import numpy as np
from scipy.io import wavfile


def write(file, data, samplerate):
    """Write a NumPy array to a WAV file.

    Parameters
    ----------
    file: str or path-like
        Destination file path.
    data: array-like
        Audio samples to write.  The input is converted to a NumPy array to
        ensure ``scipy`` receives the expected data type.
    samplerate: int
        Sample rate of ``data`` in Hertz.
    """
    # Ensure data is a NumPy array; scipy expects this format
    data = np.asarray(data)
    # Delegate the actual writing to scipy's WAV helper
    wavfile.write(file, samplerate, data)


def read(file):
    """Read a WAV file.

    Parameters
    ----------
    file: str or path-like
        Path to the WAV file to read.

    Returns
    -------
    tuple
        A two-tuple of ``(data, samplerate)`` where ``data`` is a NumPy array
        of audio samples and ``samplerate`` is the sample rate in Hertz.
    """
    # ``wavfile.read`` returns ``samplerate`` first; reorder to match
    samplerate, data = wavfile.read(file)
    return data, samplerate
