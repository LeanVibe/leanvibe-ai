# System Patterns: LeenVibe

## 1. System Architecture

LeenVibe employs a multi-component, client-server architecture designed for local-first operation.

*   **Backend (FastAPI)**: A robust Python backend built with FastAPI serves as the central hub. It is responsible for:
    *   Hosting the AI models (`MLXModelService`).
    *   Performing static code analysis (`TreeSitterService`).
    *   Managing vector embeddings for context (`VectorStoreService`).
    *   Handling client communication via REST and WebSocket endpoints.
    *   Managing event streaming for real-time updates.

*   **CLI (Click & Rich)**: A command-line interface that acts as the primary client. It is built with `click` for command parsing and `rich` for an enhanced terminal UI. It communicates with the backend to send commands and receive results.

*   **iOS App (SwiftUI)**: A companion mobile app that provides a UI for monitoring the AI agent's status in real-time by connecting to the backend's WebSocket stream.

## 2. Key Technical Decisions & Design Patterns

*   **Local-First Principle**: The entire system is designed to run on the user's local machine, ensuring data privacy and offline capability.
*   **Service-Oriented Backend**: The backend is structured into distinct services (e.g., `EnhancedAIService`, `SessionManager`, `EventService`), promoting modularity and separation of concerns.
*   **Client-Server Model**: The CLI and iOS app act as clients to the backend server, interacting through well-defined APIs.
*   **Event-Driven Communication**: Real-time features, such as notifications and monitoring, are powered by an event-driven pattern using WebSockets. The backend streams events to connected clients.
*   **RESTful API**: Standard REST endpoints are used for request-response interactions, such as triggering a code analysis task.

## 3. Component Relationships

The diagram below illustrates the high-level relationships between the core components:

```mermaid
graph TD;
    subgraph User Facing
        CLI_Client[CLI Client (Click, Rich)];
        iOS_App[iOS App (SwiftUI)];
    end

    subgraph Backend (FastAPI)
        WebSocket_API[WebSocket API];
        REST_API[REST API];

        subgraph Core Services
            EnhancedAIService[Enhanced AI Service];
            TreeSitterService[TreeSitter Service];
            VectorStoreService[Vector Store Service];
            EventService[Event Service];
        end
    end

    CLI_Client -- REST Requests --> REST_API;
    CLI_Client -- WebSocket Connection --> WebSocket_API;
    iOS_App -- WebSocket Connection --> WebSocket_API;

    REST_API --> EnhancedAIService;
    WebSocket_API --> EventService;
    EnhancedAIService --> TreeSitterService;
    EnhancedAIService --> VectorStoreService;
    EnhancedAIService --> EventService;

    style CLI_Client fill:#D5E8D4,stroke:#82B366;
    style iOS_App fill:#D5E8D4,stroke:#82B366;
    style Backend fill:#F8CECC,stroke:#B85450;
``` 