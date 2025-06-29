import Foundation
import Combine
import Observation

/// Represents user-configurable settings for the application.
@Observable
class SettingsManager {
    static let shared = SettingsManager()

    // MARK: - Published Properties
    @Published var connection: ConnectionPreferences {
        didSet {
            save(connection, for: .connection)
        }
    }
    @Published var voice: VoiceSettings {
        didSet {
            save(voice, for: .voice)
        }
    }
    @Published var notifications: NotificationSettings {
        didSet {
            save(notifications, for: .notifications)
        }
    }
    @Published var kanban: KanbanSettings {
        didSet {
            save(kanban, for: .kanban)
        }
    }

    private init() {
        self.connection = load(.connection, as: ConnectionPreferences.self) ?? ConnectionPreferences()
        self.voice = load(.voice, as: VoiceSettings.self) ?? VoiceSettings()
        self.notifications = load(.notifications, as: NotificationSettings.self) ?? NotificationSettings()
        self.kanban = load(.kanban, as: KanbanSettings.self) ?? KanbanSettings()
    }

    // MARK: - Public Methods
    func resetAll() {
        self.connection = ConnectionPreferences()
        self.voice = VoiceSettings()
        self.notifications = NotificationSettings()
        self.kanban = KanbanSettings()
        saveAll()
    }
    
    // Type-safe save method
    func save<T: Codable>(_ data: T, for key: SettingsKey) {
        let encoder = JSONEncoder()
        if let encoded = try? encoder.encode(data) {
            UserDefaults.standard.set(encoded, forKey: key.rawValue)
        }
    }

    // Type-safe load method
    func load<T: Codable>(_ key: SettingsKey, as type: T.Type) -> T? {
        if let data = UserDefaults.standard.data(forKey: key.rawValue) {
            let decoder = JSONDecoder()
            if let decoded = try? decoder.decode(T.self, from: data) {
                return decoded
            }
        }
        return nil
    }
    
    // MARK: - Private Methods
    private func saveAll() {
        save(connection, for: .connection)
        save(voice, for: .voice)
        save(notifications, for: .notifications)
        save(kanban, for: .kanban)
    }
}

// MARK: - Settings Structures
/// Defines the keys used to store settings in UserDefaults.
enum SettingsKey: String {
    case connection = "LeenVibe.ConnectionSettings"
    case voice = "LeenVibe.VoiceSettings"
    case notifications = "LeenVibe.NotificationSettings"
    case kanban = "LeenVibe.KanbanSettings"
}

/// A protocol for settings structures to ensure they provide default values.
protocol SettingsProtocol: Codable {
    init()
}

// MARK: - Settings Definitions
/// Stores the settings related to the WebSocket server connection.
struct ConnectionPreferences: SettingsProtocol {
    var host: String = "127.0.0.1"
    var port: Int = 8765
    var authToken: String = "your_auth_token"
    var useSSL: Bool = false
    
    var url: URL? {
        var components = URLComponents()
        components.scheme = useSSL ? "wss" : "ws"
        components.host = host
        components.port = port
        return components.url
    }
    
    init(host: String = "127.0.0.1", port: Int = 8765, authToken: String = "your_auth_token", useSSL: Bool = false) {
        self.host = host
        self.port = port
        self.authToken = authToken
        self.useSSL = useSSL
    }
    
    init() {
        // Initializes with default values
    }
}

/// Stores settings related to voice commands and transcription.
struct VoiceSettings: SettingsProtocol {
    var wakeWord: String = "Hey Leen"
    var autoStartListening: Bool = true
    
    init(wakeWord: String = "Hey Leen", autoStartListening: Bool = true) {
        self.wakeWord = wakeWord
        self.autoStartListening = autoStartListening
    }
    
    init() {
        // Default initializer
    }
}

/// Stores the settings related to notifications.
struct NotificationSettings: SettingsProtocol {
    var enableNotifications: Bool = true
    var alertTone: String = "default"
    
    init(enableNotifications: Bool = true, alertTone: String = "default") {
        self.enableNotifications = enableNotifications
        self.alertTone = alertTone
    }
    
    init() {
        // Default initializer
    }
}

/// Stores the settings related to the kanban board.
struct KanbanSettings: SettingsProtocol {
    var defaultView: String = "board" // "board" or "list"
    var showTaskIDs: Bool = false
    
    init(defaultView: String = "board", showTaskIDs: Bool = false) {
        self.defaultView = defaultView
        self.showTaskIDs = showTaskIDs
    }
    
    init() {
        // Default initializer
    }
} 