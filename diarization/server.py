"""Simple diarization backend server printing Hello world."""

from fastapi import FastAPI
import uvicorn
import logging
import os

app = FastAPI()


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root():
    """Return greeting message."""
    return {"message": "Hello world"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Hello world")
    host = os.environ.get("ALF_SERVER_HOST", "127.0.0.1")
    port = int(os.environ.get("ALF_SERVER_PORT", "9091"))
    uvicorn.run(app, host=host, port=port)
