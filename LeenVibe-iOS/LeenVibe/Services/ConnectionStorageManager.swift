import Foundation

// MARK: - Server Configuration

struct ServerConfig: Codable {
    let host: String
    let port: Int
    let websocketPath: String
    let serverName: String?
    let network: String?
    
    var baseURL: String {
        return "\(host):\(port)"
    }
    
    var fullURL: String {
        return "ws://\(host):\(port)\(websocketPath)"
    }
}

// MARK: - Connection Settings Storage

struct ConnectionSettings: Codable, Equatable {
    let host: String
    let port: Int
    let websocketPath: String
    let serverName: String?
    let network: String?
    let lastConnected: Date
    let isActive: Bool
    
    var websocketURL: String {
        return "ws://\(host):\(port)\(websocketPath)"
    }
    
    var displayName: String {
        return serverName ?? "\(host):\(port)"
    }
    
    init(from serverConfig: ServerConfig) {
        self.host = serverConfig.host
        self.port = serverConfig.port
        self.websocketPath = serverConfig.websocketPath
        self.serverName = serverConfig.serverName
        self.network = serverConfig.network
        self.lastConnected = Date()
        self.isActive = true
    }
    
    init(host: String, port: Int, websocketPath: String, serverName: String? = nil, network: String? = nil) {
        self.host = host
        self.port = port
        self.websocketPath = websocketPath
        self.serverName = serverName
        self.network = network
        self.lastConnected = Date()
        self.isActive = true
    }
}

// MARK: - Connection Storage Manager

@MainActor
class ConnectionStorageManager: ObservableObject {
    private let userDefaults = UserDefaults.standard
    private let storageKey = "leenvibe_connections"
    private let currentConnectionKey = "leenvibe_current_connection"
    
    @Published var savedConnections: [ConnectionSettings] = []
    @Published var currentConnection: ConnectionSettings?
    
    init() {
        loadConnections()
        loadCurrentConnection()
    }
    
    // MARK: - Public Methods
    
    func saveConnection(_ settings: ConnectionSettings) {
        // Remove existing connection with same host:port if exists
        savedConnections.removeAll { $0.host == settings.host && $0.port == settings.port }
        
        // Add new connection at the beginning
        savedConnections.insert(settings, at: 0)
        
        // Keep only last 5 connections
        if savedConnections.count > 5 {
            savedConnections = Array(savedConnections.prefix(5))
        }
        
        // Set as current connection
        currentConnection = settings
        
        // Persist to storage
        persistConnections()
        persistCurrentConnection()
    }
    
    func setCurrentConnection(_ settings: ConnectionSettings) {
        // Update last connected time
        let updatedSettings = ConnectionSettings(
            host: settings.host,
            port: settings.port,
            websocketPath: settings.websocketPath,
            serverName: settings.serverName,
            network: settings.network
        )
        
        currentConnection = updatedSettings
        
        // Update in saved connections if exists
        if let index = savedConnections.firstIndex(where: { $0.host == settings.host && $0.port == settings.port }) {
            savedConnections[index] = updatedSettings
        }
        
        persistConnections()
        persistCurrentConnection()
    }
    
    func removeConnection(_ settings: ConnectionSettings) {
        savedConnections.removeAll { $0.host == settings.host && $0.port == settings.port }
        
        // Clear current connection if it was removed
        if currentConnection?.host == settings.host && currentConnection?.port == settings.port {
            currentConnection = nil
            persistCurrentConnection()
        }
        
        persistConnections()
    }
    
    func clearAllConnections() {
        savedConnections.removeAll()
        currentConnection = nil
        persistConnections()
        persistCurrentConnection()
    }
    
    func hasValidConnection() -> Bool {
        return currentConnection != nil
    }
    
    func hasStoredConnection() -> Bool {
        return currentConnection != nil
    }
    
    func store(_ config: ServerConfig) {
        let settings = ConnectionSettings(from: config)
        saveConnection(settings)
    }
    
    func loadStoredConnection() -> ServerConfig? {
        guard let connection = currentConnection else { return nil }
        
        return ServerConfig(
            host: connection.host,
            port: connection.port,
            websocketPath: connection.websocketPath,
            serverName: connection.serverName,
            network: connection.network
        )
    }
    
    func clearStoredConnection() {
        currentConnection = nil
        persistCurrentConnection()
    }
    
    // MARK: - Private Methods
    
    private func loadConnections() {
        guard let data = userDefaults.data(forKey: storageKey),
              let connections = try? JSONDecoder().decode([ConnectionSettings].self, from: data) else {
            savedConnections = []
            return
        }
        savedConnections = connections
    }
    
    private func persistConnections() {
        guard let data = try? JSONEncoder().encode(savedConnections) else {
            print("Failed to encode connections")
            return
        }
        userDefaults.set(data, forKey: storageKey)
    }
    
    private func loadCurrentConnection() {
        guard let data = userDefaults.data(forKey: currentConnectionKey),
              let connection = try? JSONDecoder().decode(ConnectionSettings.self, from: data) else {
            currentConnection = nil
            return
        }
        currentConnection = connection
    }
    
    private func persistCurrentConnection() {
        if let connection = currentConnection {
            guard let data = try? JSONEncoder().encode(connection) else {
                print("Failed to encode current connection")
                return
            }
            userDefaults.set(data, forKey: currentConnectionKey)
        } else {
            userDefaults.removeObject(forKey: currentConnectionKey)
        }
    }
}