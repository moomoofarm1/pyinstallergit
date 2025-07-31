from pyannote.audio import Pipeline

# Load the pretrained pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token= hf_token)

# send pipeline to GPU (when available)
import torch
pipeline.to(torch.device("cuda" if torch.cuda.is_available() else "cpu")) # the script can be used to test GPU.

# Key: ONLY !!!!!!!!!!! for research ONLY !!!!!!!!!!!!!!!!
# Apply the pipeline to your audio file
diarization = pipeline("noisereduce_patient.wav")

# Print the results
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")

# write to RTTM
with open("noisereduce_patient_pyannoteaudio.rttm", "w") as f:
    diarization.write_rttm(f)
