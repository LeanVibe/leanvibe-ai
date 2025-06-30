import SwiftUI

struct ServerSettingsView: View {
    @EnvironmentObject var settingsManager: SettingsManager
    
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
            .environmentObject(SettingsManager.shared)
    }
}