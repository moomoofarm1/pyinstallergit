# from fastapi import FastAPI
# from label_studio_ml.api import register_model
# from back.llm_backend import LLMInteractiveModel

# app = FastAPI()

# model = LLMInteractiveModel()
# register_model(app, model)

from fastapi import FastAPI
from back.llm_backend import LLMInteractiveModel

app = FastAPI()
model = LLMInteractiveModel()

@app.get("/health")
def health():
    return {"status": "UP"}

@app.post("/predict")
def predict(tasks: list):
    return model.predict(tasks)