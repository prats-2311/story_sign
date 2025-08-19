# StorySign ASL Platform

A real-time American Sign Language (ASL) recognition and learning system that combines computer vision, web technologies, and interactive user interfaces.

## Features

- 🤟 Real-time ASL gesture recognition using MediaPipe
- 🖥️ Cross-platform desktop application with Electron
- 🎯 Interactive learning modules and progress tracking
- 📹 Live video processing and feedback
- 🔄 Hot reload development environment

## Project Structure

- `backend/` - FastAPI backend server with MediaPipe processing
- `frontend/` - React/Electron desktop application
- `.github/` - GitHub templates and workflows
- `docs/` - Project documentation

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Conda package manager
- Git
- Webcam access for video capture

### Installation

1. **Clone the repository**

   ```bash
   git clone <your-repository-url>
   cd StorySign_Platform
   ```

2. **Run the setup script**

   ```bash
   ./setup_dev.sh
   ```

3. **Verify installation**
   ```bash
   python verify_setup.py
   ```

### Development

#### Backend Development

```bash
cd backend
conda activate storysign-backend
python dev_server.py
```

Backend will be available at `http://localhost:8000`

#### Frontend Development

```bash
cd frontend
npm run electron-dev
```

The desktop application will launch automatically.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.
