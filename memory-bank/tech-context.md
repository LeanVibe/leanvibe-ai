# Technology Context: LeenVibe

This document outlines the technology stack, development setup, and technical constraints for the LeenVibe project.

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
*   **Build/Test**: Build and test commands are documented in `AGENTS.md`.
*   **Code Style**: The project enforces specific code style guidelines.
*   **Deployment**: The system is designed for local deployment, though specific deployment scripts exist (e.g., `deploy-leenvibe.sh`). 