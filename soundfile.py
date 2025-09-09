import numpy as np
from scipy.io import wavfile


def write(file, data, samplerate):
    """Minimal replacement for soundfile.write using scipy.io.wavfile."""
    data = np.asarray(data)
    wavfile.write(file, samplerate, data)


def read(file):
    """Minimal replacement for soundfile.read using scipy.io.wavfile."""
    samplerate, data = wavfile.read(file)
    return data, samplerate
