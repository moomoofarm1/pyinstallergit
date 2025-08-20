# from fastapi import FastAPI
# from label_studio_ml.api import register_model # register_model not work
# from back.llm_backend import LLMInteractiveModel

# app = FastAPI()

# model = LLMInteractiveModel()
# register_model(app, model)

import os
from label_studio_ml.api import init_app
from back.llm_backend import LLMInteractiveModel

# Read Hugging Face token from environment (recommended way)
HF_TOKEN = os.getenv("HF_TOKEN", None)

# Initialize model with optional token
model = LLMInteractiveModel(hf_token=HF_TOKEN, model_name="openai/whisper-small")

# Wrap into FastAPI app
app = init_app(model=model)