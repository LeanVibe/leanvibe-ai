import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct ServerSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    
    var body: some View {
        Form {
            Section(header: Text("Server Configuration")) {
                TextField("Host", text: $settingsManager.connection.host)
                TextField("Port", value: $settingsManager.connection.port, formatter: NumberFormatter())
                Toggle("Use SSL", isOn: $settingsManager.connection.useSSL)
            }
            
            Section(header: Text("Authentication")) {
                SecureField("Auth Token", text: $settingsManager.connection.authToken)
            }
        }
        .navigationTitle("Server Settings")
    }
}

struct ServerSettingsView_Previews: PreviewProvider {
    static var previews: some View {
        ServerSettingsView()
            .environment(\.settingsManager, SettingsManager.shared)
    }
}