import librosa
import soundfile as sf
import noisereduce as nr
import numpy as np
from tqdm import tqdm

# === Utility Function ===
def parse_timestamp(time_str):
    """
    Convert 'hh:mm:ss:xx' timestamp to seconds.
    - xx represents hundredths of a second (i.e., 10ms units).
    """
    h, m, s, hs = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s + hs / 100.0

# === Configurable Parameters ===
input_file = "6. session_noisyvr.MP3"
output_file = "noisereduce_patient.wav"
noise_start_time = "00:18:27:50"  # NEW format, hh:mm:ss:xx, xx = 1/100 seconds. The time is determined through audacity.
noise_end_time   = "00:18:29:80"  # NEW format
block_duration_sec = 10        # ~10 sec processing blocks

# === Convert to seconds ===
noise_start_sec = parse_timestamp(noise_start_time)
noise_end_sec = parse_timestamp(noise_end_time)

# === Load MP3 ===
y, rate = librosa.load(input_file, sr=None, mono=False)
if y.ndim == 1:
    y = np.expand_dims(y, axis=0)
else:
    y = y

num_channels, total_samples = y.shape
block_size = int(rate * block_duration_sec)

# === Get noise profile ===
noise_start = int(noise_start_sec * rate)
noise_end = int(noise_end_sec * rate)
noise_profile = y[:, noise_start:noise_end]

# === Write output file in blocks ===
with sf.SoundFile(output_file, mode="w", samplerate=rate, channels=num_channels) as of:
    for start in tqdm(range(0, total_samples, block_size)):
        end = min(start + block_size, total_samples)
        block = y[:, start:end]

        clean_block = []
        for ch in range(num_channels):
            clean = nr.reduce_noise(
                y=block[ch],
                y_noise=noise_profile[ch],
                sr=rate,
                prop_decrease=1.0 # Try grid, 0.7, 1.0 is too strong for denoising
                #use_tensorflow=False  # Use classic STFT-based spectral gating
            )
            clean_block.append(clean)

        clean_block = np.stack(clean_block, axis=0)

        # Pad if needed
        if clean_block.shape[1] < block_size:
            pad = block_size - clean_block.shape[1]
            clean_block = np.pad(clean_block, ((0, 0), (0, pad)), mode='constant')

        of.write(clean_block.T)
