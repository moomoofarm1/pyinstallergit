from fastapi import FastAPI
from label_studio_ml.api import register_model
from back.llm_backend import LLMInteractiveModel

app = FastAPI()

model = LLMInteractiveModel()
register_model(app, model)