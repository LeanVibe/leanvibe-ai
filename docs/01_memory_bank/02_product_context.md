# Product Context: LeenVibe

## 1. Problem Statement

Modern software development often requires tools that can deeply understand a codebase while ensuring the privacy and security of the code. Cloud-based AI assistants can be powerful, but they raise concerns about data security and require a constant internet connection. Developers need a tool that is both powerful and secure, integrating seamlessly into their local workflow.

## 2. Solution

LeenVibe is a **local-first AI coding assistant** that addresses these challenges by running entirely on the user's local machine. This approach guarantees that a user's code never leaves their computer, providing maximum privacy and security. It is designed to be a powerful, context-aware "co-pilot" for developers.

## 3. User Experience Goals

*   **Terminal-First Interface**: The primary interface is a rich, interactive Command-Line Interface (CLI) built with `click` and `rich`, catering to developers who are most comfortable in a terminal environment.
*   **Real-time, Unobtrusive Notifications**: The system provides real-time feedback and notifications directly in the terminal, keeping the developer informed without disrupting their workflow.
*   **Convenient Monitoring**: A companion iOS application allows for at-a-glance monitoring of the AI agent's status and activities.

## 4. How It Works

LeenVibe's architecture consists of three main components:

1.  **Backend (Python/FastAPI)**: The core of the system. It handles AI model inference, codebase analysis (AST, vector embeddings), and serves data to the clients via REST and WebSocket APIs.
2.  **CLI Client (Python/Click)**: The main entry point for developers to interact with the system. It communicates with the backend to execute commands.
3.  **iOS App (Swift/SwiftUI)**: A companion app that connects to the backend's WebSocket to provide real-time monitoring. 