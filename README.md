<p align="center">
  <img src="https://img.shields.io/badge/python-v3.8+-blue.svg?style=flat-square" alt="python" />
  <img src="https://img.shields.io/badge/node-v16+-brightgreen.svg?style=flat-square" alt="node" />
  <img src="https://img.shields.io/badge/react-v18+-61DAFB.svg?style=flat-square" alt="react" />
  <img src="https://img.shields.io/badge/fastapi-v0.104+-009688.svg?style=flat-square" alt="fastapi" />
  <a href="https://github.com/your-org/storysign-platform/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT" />
  </a>
  <a href="https://github.com/your-org/storysign-platform/blob/main/CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/contributions-welcome-orange.svg?style=flat-square" alt="Contributions Welcome" />
  </a>
</p>

<p align="center">
  <img src="https://via.placeholder.com/200x200/4A90E2/FFFFFF?text=StorySign" alt="StorySign Logo" />
</p>

# StorySign ASL Platform

The StorySign ASL Platform is a real-time American Sign Language (ASL) recognition and learning system that combines computer vision, web technologies, and interactive user interfaces. Built with FastAPI backend and React/Electron frontend, it provides an accessible and engaging way to learn ASL through modern technology.

## Features

- 🤟 **Real-time ASL Recognition** - Advanced gesture recognition using MediaPipe
- 🖥️ **Cross-platform Desktop App** - Built with React and Electron
- 🎯 **Interactive Learning** - Gamified learning modules with progress tracking
- 📹 **Live Video Processing** - Real-time feedback with <100ms latency
- 🔄 **Hot Reload Development** - Streamlined development experience
- 🧠 **Hybrid AI** - Local vision models with cloud LLM integration
- ♿ **Accessibility First** - WCAG 2.1 AA compliant interface
- 🔒 **Privacy Focused** - Local processing with secure data handling

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

You will need the following properly installed on your computer:

- [Git](http://git-scm.com/)
- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js 16+](http://nodejs.org/)
- [Conda](https://docs.conda.io/en/latest/miniconda.html) package manager
- Webcam access for video capture

### Installation

In a terminal window run these commands:

```bash
# Clone the repository
git clone https://github.com/your-org/storysign-platform.git
cd storysign-platform

# Setup backend environment
cd StorySign_Platform/backend
conda env create -f environment.yml
conda activate storysign-backend
pip install -r requirements.txt

# Setup frontend environment
cd ../frontend
npm install

# Return to root directory
cd ../..
```

### Development

#### Backend Development

```bash
cd StorySign_Platform/backend
conda activate storysign-backend
python main.py
```

Backend will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

#### Frontend Development

```bash
cd StorySign_Platform/frontend
npm run electron-dev
```

The desktop application will launch automatically with hot reload enabled.

#### Full Stack Development

For development with both backend and frontend running:

```bash
# Terminal 1 - Backend
cd StorySign_Platform/backend
conda activate storysign-backend
python main.py

# Terminal 2 - Frontend
cd StorySign_Platform/frontend
npm run electron-dev
```

## Project Structure

```
storysign-platform/
├── StorySign_Platform/
│   ├── backend/                 # FastAPI backend server
│   │   ├── api/                # API endpoints
│   │   ├── core/               # Core business logic
│   │   ├── models/             # Database models
│   │   ├── services/           # Service layer
│   │   └── main.py             # Application entry point
│   ├── frontend/               # React/Electron desktop app
│   │   ├── src/
│   │   │   ├── components/     # React components
│   │   │   ├── pages/          # Application pages
│   │   │   ├── hooks/          # Custom React hooks
│   │   │   └── utils/          # Utility functions
│   │   └── public/             # Static assets
│   └── docs/                   # Project documentation
├── tests/                      # Test suites
│   ├── e2e/                   # End-to-end tests
│   ├── integration/           # Integration tests
│   └── performance/           # Performance benchmarks
├── CONTRIBUTING.md             # Contribution guidelines
├── CHANGELOG.md               # Version history
└── LICENSE                    # MIT License
```

## Testing

### Backend Testing

```bash
cd StorySign_Platform/backend
conda activate storysign-backend
python -m pytest tests/ -v
```

### Frontend Testing

```bash
cd StorySign_Platform/frontend
npm run test
```

### End-to-End Testing

```bash
cd tests/e2e
npm run test:e2e
```

### Performance Testing

```bash
cd tests/performance
python benchmark_latency.py
```

## API Documentation

The FastAPI backend provides comprehensive API documentation:

- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Architecture

The StorySign platform follows a modern microservices architecture:

- **Frontend**: React/Electron desktop application with WebSocket communication
- **Backend**: FastAPI server with async processing and MediaPipe integration
- **AI Services**: Hybrid approach using local Ollama models and cloud LLMs
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Real-time Communication**: WebSocket for video streaming and gesture recognition

For detailed architecture information, see [docs/ARCHITECTURE.md](StorySign_Platform/docs/ARCHITECTURE.md).

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting issues and pull requests.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our coding standards
4. Ensure all tests pass and accessibility requirements are met
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Roadmap

- [ ] **Mobile App** - iOS and Android applications
- [ ] **Multi-language Support** - Support for international sign languages
- [ ] **Advanced AI Models** - Improved gesture recognition accuracy
- [ ] **Cloud Sync** - Progress synchronization across devices
- [ ] **Community Features** - User-generated content and social learning
- [ ] **VR/AR Integration** - Immersive learning experiences

## Support

- 📧 **Email**: support@storysign.com
- 💬 **Discord**: [Join our community](https://discord.gg/storysign)
- 📖 **Documentation**: [docs.storysign.com](https://docs.storysign.com)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/storysign-platform/issues)

## Acknowledgments

- MediaPipe team for computer vision capabilities
- The ASL community for guidance and feedback
- Open source contributors and maintainers
- Accessibility advocates for inclusive design principles
