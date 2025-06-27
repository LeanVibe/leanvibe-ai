# LeenVibe Agent Guide

This document is the primary entry point for developers and AI agents working on the LeenVibe project. For a deeper understanding of the project's context, architecture, and progress, please refer to the documents in the `memory-bank/` directory.

## 1. Project Overview

LeenVibe is a local-first, AI-powered coding assistant designed to provide deep codebase analysis and real-time assistance to developers. It runs entirely on-device, ensuring code privacy and security.

The system consists of three main components:
*   **Backend (`leenvibe-backend`)**: A Python/FastAPI application that serves the AI models, performs code analysis, and manages client communication.
*   **CLI (`leenvibe-cli`)**: An interactive command-line client for developers to interact with the backend.
*   **iOS App (`LeenVibe-iOS-App`)**: A companion app for real-time monitoring.

## 2. Setup and Installation

### Prerequisites
*   **Hardware**: Mac with Apple Silicon (M1/M2/M3).
*   **Software**: macOS 13.0+, Python 3.11+, Xcode 15+.

### Backend Setup
```bash
# Navigate to the backend directory
cd leenvibe-backend

# Make the startup script executable
chmod +x start.sh

# Run the script to install dependencies and start the server
./start.sh
```
*After running, verify the backend is healthy by visiting `http://localhost:8000/health` in your browser.*

### iOS App Setup
```bash
# The simplest method is to open the Swift Package directly in Xcode
cd LeenVibe-SwiftPM
open Package.swift

# Then, select an iOS Simulator and press Cmd+R to build and run.
```

## 3. Getting Started: Commands & Workflow

### Quality Checks (Run Before Committing)
```bash
# From the leenvibe-backend directory:
cd leenvibe-backend

# Format and sort imports
black .
isort .

# Run linter and type checker
flake8 .
mypy .

# Run the full test suite
python run_tests.py
```

### Backend Development
```bash
# Navigate to the backend directory
cd leenvibe-backend

# Install/sync dependencies
uv sync

# Start the development server with hot-reloading
./start.sh
```

### iOS Development
```bash
# Open the Xcode project
open LeenVibe-iOS-App/LeenVibe.xcodeproj

# Use standard Xcode commands to build (⌘+B) and test (⌘+U)
```

## 4. Technology Stack

### Backend
*   **Language**: Python 3.11+
*   **Framework**: FastAPI, Uvicorn
*   **AI Stack**: MLX, Pydantic.ai
*   **Databases**: Neo4j, ChromaDB
*   **Tooling**: `uv` for package management, `pytest` for testing

### CLI
*   **Framework**: Python `click`
*   **UI**: `rich`

### iOS App
*   **Framework**: SwiftUI (iOS 17+)
*   **Communication**: WebSocket Client

## 5. Key Architectural Patterns
*   **Local-First**: All processing is done on the local machine.
*   **Event-Driven**: WebSockets provide real-time updates to clients.
*   **Service-Oriented**: The backend is composed of modular services for AI, AST parsing, etc.

## 6. Development Workflow
*   **Branching**: Use `feature/` and `fix/` branches off of `develop`. `main` is for production-ready code.
*   **Commits**: Follow the conventional commits standard (e.g., `feat:`, `fix:`, `docs:`).

## 7. Troubleshooting

### Backend Issues
*   **`ModuleNotFoundError`**: Run `uv sync` in the `leenvibe-backend` directory.
*   **`Address already in use`**: Find and stop the process on port 8000 with `lsof -ti:8000 | xargs kill -9`.
*   **Permission errors**: Ensure scripts are executable with `chmod +x *.sh`.

### iOS Issues
*   **Build errors**: Clean the build folder in Xcode (Product > Clean Build Folder) and rebuild.
*   **Dependency errors**: Update Swift Packages in Xcode (File > Packages > Update to Latest).
*   **Connection fails**: Ensure the backend server is running and accessible.

For more detailed information, please consult the `memory-bank/` directory.