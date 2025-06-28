import Foundation

// MARK: - Server Configuration Model

struct ServerConfig: Codable, Equatable {
    let host: String
    let port: Int
    let websocketPath: String
    let serverName: String?
    let network: String?
    
    init(host: String, port: Int, websocketPath: String = "/ws/ios-client", serverName: String? = nil, network: String? = nil) {
        self.host = host
        self.port = port
        self.websocketPath = websocketPath
        self.serverName = serverName
        self.network = network
    }
    
    var websocketURL: String {
        return "ws://\(host):\(port)\(websocketPath)"
    }
    
    var displayName: String {
        return serverName ?? "\(host):\(port)"
    }
}