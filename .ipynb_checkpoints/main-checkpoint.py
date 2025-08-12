print('hello world')

# main.py
from fastapi import FastAPI
from label_studio_ml.api import register_model
from llm_backend import LLMInteractiveModel

app = FastAPI()

# Register your model using the Label Studio ML backend
model = LLMInteractiveModel()
register_model(app, model)
