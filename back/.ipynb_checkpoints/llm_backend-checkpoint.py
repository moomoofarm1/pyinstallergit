from label_studio_ml.model import LabelStudioMLBase
from transformers import pipeline
import os

class LLMInteractiveModel(LabelStudioMLBase):
    def __init__(self, hf_token: str = None, model_name: str = "openai/whisper-small", **kwargs):
        super().__init__(**kwargs)
        print("Whisper model initializing...")

        # Use Hugging Face token if provided
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token

        self.transcriber = pipeline(
            "automatic-speech-recognition",
            model=model_name
            #,use_auth_token=hf_token  # TODO: some Whisper checkpoints require auth
        )

        print(f"Loaded Whisper model: {model_name}")

    def predict(self, tasks, **kwargs):
        """Transcribe audio from Label Studio tasks"""
        results = []
        for task in tasks:
            audio_path = task['data'].get('audio')  # LS provides audio URL/path

            if not audio_path:
                continue

            # Hugging Face pipeline supports file paths and URLs
            transcription = self.transcriber(audio_path)["text"]

            results.append({
                'result': [{
                    'from_name': 'transcription',
                    'to_name': 'audio',
                    'type': 'textarea',
                    'value': {
                        'text': [transcription]
                    }
                }]
            })

        return results

    def fit(self, completions, workdir=None, **kwargs):
        # Optional fine-tuning could go here
        return {}