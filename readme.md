# ALF - Audio Label Frontend

A Label Studio integration with Whisper for automatic speech transcription.

## Project Structure

```
project_root/
├── main.py              # Entry point
├── server.py           # FastAPI ML backend server
├── requirements.txt    # Python dependencies
├── setup.py           # Setup script
├── front/
│   └── gui.py         # Tkinter GUI controller
└── back/
    └── llm_backend.py # Whisper ML backend
```

## Setup

1. **Install dependencies:**
   ```bash
   python setup.py
   ```

2. **Set Hugging Face token (optional):**
   ```bash
   export HF_TOKEN=your_token_here
   ```

## Usage

1. **Start the application:**
   ```bash
   python main.py
   ```

2. **Use the GUI to:**
   - Click "Step 1. Install and start label-studio" (installs Label Studio on port 8080)
   - Click "Start ALF" (starts ML backend on port 9090)
   - Go to http://localhost:8080 to create annotation projects
   - Configure your Label Studio project to use the ML backend at http://localhost:9090

3. **When finished:**
   - Click "Stop ALF & Exit" to stop the ML backend
   - Click "Final step. stop and uninstall label-studio" to clean up

## Features

- **GUI Control:** Easy start/stop of both Label Studio and the ML backend
- **Cross-platform:** Works on Windows, Linux, and macOS
- **Whisper Integration:** Automatic speech recognition using OpenAI's Whisper model
- **Label Studio ML Backend:** Seamless integration with Label Studio's annotation interface

## Ports

- **8080:** Label Studio frontend
- **9090:** ML backend (Whisper transcription service)

## Notes

- The ML backend uses Whisper-small by default (faster, but less accurate)
- You can modify the model in `server.py` to use larger Whisper models
- The application handles both local audio files and remote URLs
