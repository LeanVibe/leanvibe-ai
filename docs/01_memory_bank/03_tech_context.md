# Technology Context: LeanVibe

This document outlines the technology stack, development setup, and technical constraints for the LeanVibe project.

## 1. Backend

*   **Language**: Python
*   **Web Framework**: FastAPI
*   **AI / Machine Learning**:
    *   **Primary LLM**: `Qwen2.5-Coder-32B`
    *   **Local Inference Engine**: Apple's `MLX` framework for running models on Apple Silicon.
    *   **Agent Framework**: `Pydantic.ai` for structuring and managing AI agent logic.
*   **Data Storage**:
    *   **Graph Database**: `Neo4j` for storing and querying codebase relationships.
    *   **Vector Store**: `VectorStoreService` (specific implementation, e.g., ChromaDB, is abstracted).
*   **Code Parsing**: `TreeSitter` for generating Abstract Syntax Trees (ASTs).
*   **API**: Exposes both a RESTful API and a WebSocket endpoint for real-time communication.

## 2. Command-Line Interface (CLI)

*   **Language**: Python
*   **Framework**: `click`
*   **Terminal UI**: `rich` for enhanced, interactive terminal output.

## 3. iOS Application

*   **Language**: Swift
*   **UI Framework**: SwiftUI
*   **Functionality**: Acts as a real-time monitor for the backend agent via a WebSocket connection.

## 4. Development & Operations

*   **Development Workflow**: The project follows an agile, sprint-based methodology.
*   **Build/Test**: All build, test, and quality check commands are documented in `AGENTS.md`.
*   **Code Style**: `ruff` is the primary tool for linting and formatting.
*   **Deployment**: The system is designed for local deployment.

## 5. Development Commands

This section provides common commands for development and testing.

### Backend (leanvibe-backend)

- **Run development server:**
  ```bash
  cd leanvibe-backend && ./start.sh
  ```
- **Run tests:**
  ```bash
  cd leanvibe-backend
  python run_tests.py
  # Or, for verbose output:
  pytest tests/ -v
  ```
- **Run code quality checks:**
  ```bash
  cd leanvibe-backend
  black app/ tests/
  isort app/ tests/
  flake8 app/ tests/
  mypy app/
  ```

### iOS (LeanVibe-iOS-App)

- **Open project in Xcode:**
  ```bash
  open LeanVibe-iOS-App/LeanVibe.xcodeproj
  ``` 