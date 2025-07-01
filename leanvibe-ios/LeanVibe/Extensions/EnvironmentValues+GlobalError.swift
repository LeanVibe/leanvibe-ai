import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct GlobalErrorManagerKey: EnvironmentKey {
    static let defaultValue: GlobalErrorManager = GlobalErrorManager.shared
}

@available(iOS 18.0, macOS 14.0, *)
extension EnvironmentValues {
    var globalErrorManager: GlobalErrorManager {
        get { self[GlobalErrorManagerKey.self] }
        set { self[GlobalErrorManagerKey.self] = newValue }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct SettingsManagerKey: EnvironmentKey {
    static let defaultValue: SettingsManager = SettingsManager.shared
}

@available(iOS 18.0, macOS 14.0, *)
extension EnvironmentValues {
    var settingsManager: SettingsManager {
        get { self[SettingsManagerKey.self] }
        set { self[SettingsManagerKey.self] = newValue }
    }
}

@available(iOS 18.0, macOS 14.0, *)
extension View {
    func globalErrorManager(_ manager: GlobalErrorManager) -> some View {
        environment(\.globalErrorManager, manager)
    }
    
    func settingsManager(_ manager: SettingsManager) -> some View {
        environment(\.settingsManager, manager)
    }
}