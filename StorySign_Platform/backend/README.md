# StorySign Backend

FastAPI backend server with MediaPipe processing for real-time ASL recognition.

## Setup

### Using Conda (Recommended)

```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate storysign-backend

# Start development server with hot reload
python dev_server.py
```

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - Health check endpoint
- `WebSocket /ws/video` - Real-time video streaming endpoint

## Development

The development server includes:

- Hot reload on code changes
- CORS configuration for frontend communication
- Comprehensive error logging
- WebSocket support for real-time video processing
