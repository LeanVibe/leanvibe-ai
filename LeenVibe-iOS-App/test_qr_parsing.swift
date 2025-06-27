import Foundation

// Test QR parsing logic
let testQRData = """
{"leenvibe": {"version": "1.0", "server": {"host": "192.168.1.202", "port": 8000, "websocket_path": "/ws", "protocol": "ws"}, "metadata": {"server_name": "code-mb16", "network": "Unknown Network", "all_interfaces": [{"ip": "192.168.1.202", "interface": "en0", "type": "ethernet", "url": "ws://192.168.1.202:8000/ws"}], "timestamp": 1750983242}}}
"""

func parseQRConfig(_ qrData: String) -> ServerConfig? {
    do {
        let data = qrData.data(using: .utf8) ?? Data()
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        
        guard let leenvibe = json?["leenvibe"] as? [String: Any],
              let server = leenvibe["server"] as? [String: Any],
              let host = server["host"] as? String,
              let port = server["port"] as? Int,
              let websocketPath = server["websocket_path"] as? String else {
            return nil
        }
        
        let metadata = leenvibe["metadata"] as? [String: Any]
        let serverName = metadata?["server_name"] as? String
        let network = metadata?["network"] as? String
        
        return ServerConfig(
            host: host,
            port: port,
            websocketPath: websocketPath,
            serverName: serverName,
            network: network
        )
    } catch {
        print("Error parsing QR config: \(error)")
        return nil
    }
}

struct ServerConfig {
    let host: String
    let port: Int
    let websocketPath: String
    let serverName: String?
    let network: String?
}

// Test the parsing
if let config = parseQRConfig(testQRData) {
    print("✅ QR Parsing Success:")
    print("   Host: \(config.host)")
    print("   Port: \(config.port)")
    print("   Path: \(config.websocketPath)")
    print("   Server: \(config.serverName ?? "Unknown")")
    print("   Network: \(config.network ?? "Unknown")")
    print("   WebSocket URL: ws://\(config.host):\(config.port)\(config.websocketPath)")
} else {
    print("❌ QR Parsing Failed")
}