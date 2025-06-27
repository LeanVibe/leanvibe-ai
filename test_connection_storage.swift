import Foundation

// Test Connection Storage Manager functionality
class TestConnectionStorage {
    
    static func runTests() {
        print("🧪 Testing Connection Storage Manager")
        print("=====================================")
        
        // Test 1: Create connection settings
        print("\n📱 Test 1: Create Connection Settings")
        let connection = ConnectionSettings(
            host: "192.168.1.100",
            port: 8000,
            websocketPath: "/ws",
            serverName: "Test Server",
            network: "Test WiFi"
        )
        
        print("✅ Connection created:")
        print("   Display Name: \(connection.displayName)")
        print("   WebSocket URL: \(connection.websocketURL)")
        print("   Last Connected: \(connection.lastConnected)")
        
        // Test 2: JSON encoding/decoding
        print("\n🔍 Test 2: JSON Persistence")
        do {
            let data = try JSONEncoder().encode(connection)
            let decoded = try JSONDecoder().decode(ConnectionSettings.self, from: data)
            
            if decoded == connection {
                print("✅ JSON encoding/decoding: SUCCESS")
            } else {
                print("❌ JSON encoding/decoding: FAILED - Objects not equal")
            }
        } catch {
            print("❌ JSON encoding/decoding: FAILED - \(error)")
        }
        
        // Test 3: ServerConfig conversion
        print("\n🔄 Test 3: ServerConfig Conversion")
        let serverConfig = ServerConfig(
            host: "192.168.1.101",
            port: 8001,
            websocketPath: "/ws",
            serverName: "Config Server",
            network: "Config WiFi"
        )
        
        let convertedConnection = ConnectionSettings(from: serverConfig)
        print("✅ ServerConfig conversion:")
        print("   Original host: \(serverConfig.host)")
        print("   Converted host: \(convertedConnection.host)")
        print("   WebSocket URL: \(convertedConnection.websocketURL)")
        
        print("\n🎉 All tests completed!")
    }
}

// Run tests
TestConnectionStorage.runTests()