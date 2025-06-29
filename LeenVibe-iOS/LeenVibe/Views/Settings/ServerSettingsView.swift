import SwiftUI
import AVFoundation

/// Server Settings view for managing backend connections and QR code configuration
/// Integrates with WebSocketService and provides QR scanner for easy setup
struct ServerSettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var settingsManager = SettingsManager.shared
    @ObservedObject var webSocketService: WebSocketService
    @State private var showingQRScanner = false
    @State private var showingManualEntry = false
    @State private var isTestingConnection = false
    @State private var connectionTestResult: ConnectionTestResult?
    @State private var showingAdvancedSettings = false
    
    enum ConnectionTestResult {
        case success
        case failure(String)
    }
    
    // MARK: - Body
    
    var body: some View {
        List {
            // Current Connection Status
            connectionStatusSection
            
            // Configuration Options
            configurationSection
            
            // Connection Settings
            connectionSettingsSection
            
            // WebSocket Configuration
            webSocketSection
            
            // Advanced Options
            advancedSection
        }
        .navigationTitle("Server Settings")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingQRScanner) {
            QRScannerView { result in
                handleQRScanResult(result)
            }
        }
        .sheet(isPresented: $showingManualEntry) {
            ManualServerEntryView()
        }
        .sheet(isPresented: $showingAdvancedSettings) {
            AdvancedServerSettingsView()
        }
    }
    
    // MARK: - View Sections
    
    private var connectionStatusSection: some View {
        Section("Connection Status") {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Server Status")
                        .fontWeight(.medium)
                    
                    HStack {
                        connectionStatusIndicator
                        Text(connectionStatusText)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                if !isTestingConnection {
                    Button("Test") {
                        testConnection()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                } else {
                    ProgressView()
                        .controlSize(.small)
                }
            }
            
            if !settingsManager.connectionSettings.serverURL.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Server URL")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Text(fullServerURL)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .textSelection(.enabled)
                }
                .padding(.vertical, 4)
            }
            
            if let testResult = connectionTestResult {
                switch testResult {
                case .success:
                    Label("Connection successful", systemImage: "checkmark.circle.fill")
                        .foregroundColor(.green)
                        .font(.caption)
                case .failure(let error):
                    Label("Connection failed: \(error)", systemImage: "xmark.circle.fill")
                        .foregroundColor(.red)
                        .font(.caption)
                }
            }
        }
    }
    
    private var configurationSection: some View {
        Section("Setup Methods") {
            Button(action: { showingQRScanner = true }) {
                SettingsRow(
                    icon: "qrcode.viewfinder",
                    iconColor: .blue,
                    title: "Scan QR Code",
                    subtitle: "Quick setup from LeenVibe server"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: { showingManualEntry = true }) {
                SettingsRow(
                    icon: "keyboard",
                    iconColor: .green,
                    title: "Manual Entry",
                    subtitle: "Enter server details manually"
                )
            }
            .buttonStyle(.plain)
            
            if !settingsManager.connectionSettings.serverURL.isEmpty {
                Button(action: { clearServerConfiguration() }) {
                    SettingsRow(
                        icon: "trash",
                        iconColor: .red,
                        title: "Clear Configuration",
                        subtitle: "Remove current server settings"
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }
    
    private var connectionSettingsSection: some View {
        Section("Connection Behavior") {
            Toggle("Auto-reconnect", isOn: $settingsManager.connectionSettings.autoReconnect)
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Connection Timeout")
                    Spacer()
                    Text("\(Int(settingsManager.connectionSettings.connectionTimeout))s")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $settingsManager.connectionSettings.connectionTimeout,
                    in: 5...60,
                    step: 5
                )
            }
            .padding(.vertical, 4)
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Retry Attempts")
                    Spacer()
                    Text("\(settingsManager.connectionSettings.retryAttempts)")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: Binding(
                        get: { Double(settingsManager.connectionSettings.retryAttempts) },
                        set: { settingsManager.connectionSettings.retryAttempts = Int($0) }
                    ),
                    in: 1...10,
                    step: 1
                )
            }
            .padding(.vertical, 4)
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Retry Delay")
                    Spacer()
                    Text("\(Int(settingsManager.connectionSettings.retryDelay))s")
                        .foregroundColor(.secondary)
                }
                
                Slider(
                    value: $settingsManager.connectionSettings.retryDelay,
                    in: 1...30,
                    step: 1
                )
            }
            .padding(.vertical, 4)
        }
    }
    
    private var webSocketSection: some View {
        Section("Real-time Updates") {
            Toggle("Enable WebSocket", isOn: $settingsManager.connectionSettings.webSocketEnabled)
                .onChange(of: settingsManager.connectionSettings.webSocketEnabled) { _, enabled in
                    handleWebSocketToggle(enabled)
                }
            
            if settingsManager.connectionSettings.webSocketEnabled {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Heartbeat Interval")
                        Spacer()
                        Text("\(Int(settingsManager.connectionSettings.webSocketHeartbeat))s")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: $settingsManager.connectionSettings.webSocketHeartbeat,
                        in: 10...120,
                        step: 10
                    )
                    
                    Text("Keep-alive interval for WebSocket connection")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Reconnect Delay")
                        Spacer()
                        Text("\(Int(settingsManager.connectionSettings.webSocketReconnectDelay))s")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: $settingsManager.connectionSettings.webSocketReconnectDelay,
                        in: 1...30,
                        step: 1
                    )
                }
                .padding(.vertical, 4)
                
                HStack {
                    Text("WebSocket Status")
                    Spacer()
                    webSocketStatusIndicator
                }
            }
        }
    }
    
    private var advancedSection: some View {
        Section("Advanced") {
            Button(action: { showingAdvancedSettings = true }) {
                SettingsRow(
                    icon: "gearshape.2",
                    iconColor: .gray,
                    title: "Advanced Settings",
                    subtitle: "SSL, headers, and debugging options"
                )
            }
            .buttonStyle(.plain)
            
            NavigationLink("Network Diagnostics") {
                NetworkDiagnosticsView()
            }
            
            Button(action: { exportServerSettings() }) {
                SettingsRow(
                    icon: "square.and.arrow.up",
                    iconColor: .blue,
                    title: "Export Configuration",
                    subtitle: "Save server settings for backup"
                )
            }
            .buttonStyle(.plain)
        }
    }
    
    // MARK: - Helper Properties
    
    private var connectionStatusIndicator: some View {
        Image(systemName: connectionStatusIcon)
            .foregroundColor(connectionStatusColor)
    }
    
    private var connectionStatusIcon: String {
        if webSocketService.isConnected {
            return "checkmark.circle.fill"
        } else if isTestingConnection {
            return "arrow.clockwise"
        } else if settingsManager.connectionSettings.serverURL.isEmpty {
            return "questionmark.circle"
        } else {
            return "xmark.circle.fill"
        }
    }
    
    private var connectionStatusColor: Color {
        if webSocketService.isConnected {
            return .green
        } else if isTestingConnection {
            return .orange
        } else if settingsManager.connectionSettings.serverURL.isEmpty {
            return .gray
        } else {
            return .red
        }
    }
    
    private var connectionStatusText: String {
        switch webSocketService.connectionState {
        case .connected:
            return "Connected"
        case .connecting:
            return "Connecting..."
        case .disconnected:
            return "Disconnected"
        case .error(let error):
            return "Error: \(error?.localizedDescription ?? "Unknown")"
        }
    }
    
    private var fullServerURL: String {
        let host = settingsManager.connectionSettings.serverURL
        let port = settingsManager.connectionSettings.serverPort
        let protocolString = settingsManager.connectionSettings.useHTTPS ? "https" : "http"
        
        if port == 80 || port == 443 {
            return "\(protocolString)://\(host)"
        } else {
            return "\(protocolString)://\(host):\(port)"
        }
    }
    
    private var webSocketStatusIndicator: some View {
        HStack {
            Image(systemName: webSocketService.isConnected ? "checkmark.circle.fill" : "xmark.circle.fill")
                .foregroundColor(webSocketService.isConnected ? .green : .red)
            
            Text(webSocketService.isConnected ? "Connected" : "Disconnected")
                .foregroundColor(.secondary)
        }
    }
    
    // MARK: - Actions
    
    private func testConnection() {
        guard !settingsManager.connectionSettings.serverURL.isEmpty else { return }
        isTestingConnection = true
        connectionTestResult = nil
        
        // Simulate connection test
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            isTestingConnection = false
            
            if !settingsManager.connectionSettings.serverURL.isEmpty {
                connectionTestResult = Bool.random() ? .success : .failure("Connection timeout")
            } else {
                connectionTestResult = .failure("No server configured")
            }
        }
    }
    
    private func handleQRScanResult(_ result: String) {
        // Parse QR code result and update server settings
        if let serverConfig = parseQRCode(result) {
            settingsManager.connectionSettings.serverURL = serverConfig.host
            settingsManager.connectionSettings.serverPort = serverConfig.port
            settingsManager.connectionSettings.useHTTPS = serverConfig.useHTTPS
            
            // Test the new connection
            testConnection()
        }
    }
    
    private func parseQRCode(_ qrContent: String) -> (host: String, port: Int, useHTTPS: Bool)? {
        // Parse QR code content for server configuration
        // Expected format: "leenvibe://server/host:port?ssl=true"
        guard let url = URL(string: qrContent),
              url.scheme == "leenvibe",
              url.host == "server" else {
            return nil
        }
        
        let pathComponents = url.pathComponents.filter { $0 != "/" }
        guard let serverInfo = pathComponents.first,
              let colonIndex = serverInfo.firstIndex(of: ":"),
              let port = Int(serverInfo[serverInfo.index(after: colonIndex)...]) else {
            return nil
        }
        
        let host = String(serverInfo[..<colonIndex])
        let useHTTPS = url.query?.contains("ssl=true") ?? false
        
        return (host: host, port: port, useHTTPS: useHTTPS)
    }
    
    private func handleWebSocketToggle(_ enabled: Bool) {
        if enabled {
            // Connect WebSocket if server is configured
            if !settingsManager.connectionSettings.serverURL.isEmpty {
                Task {
                    await webSocketService.connect()
                }
            }
        } else {
            // Disconnect WebSocket
            webSocketService.disconnect()
        }
    }
    
    private func clearServerConfiguration() {
        webSocketService.disconnect()
        
        settingsManager.connectionSettings.serverURL = ""
        settingsManager.connectionSettings.serverPort = 8000
        settingsManager.connectionSettings.useHTTPS = false
        
        connectionTestResult = nil
    }
    
    private func exportServerSettings() {
        // Export server configuration
        print("Exporting server settings")
    }
}

// MARK: - Supporting Views

struct QRScannerView: View {
    let onResult: (String) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var hasPermission = false
    @State private var showingPermissionAlert = false
    
    var body: some View {
        NavigationView {
            ZStack {
                if hasPermission {
                    QRCodeScannerRepresentable { result in
                        onResult(result)
                        dismiss()
                    }
                } else {
                    VStack(spacing: 20) {
                        Image(systemName: "camera.fill")
                            .font(.system(size: 64))
                            .foregroundColor(.gray)
                        
                        Text("Camera Permission Required")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("Please allow camera access to scan QR codes for server configuration.")
                            .multilineTextAlignment(.center)
                            .foregroundColor(.secondary)
                            .padding(.horizontal)
                        
                        Button("Request Permission") {
                            requestCameraPermission()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
            }
            .navigationTitle("Scan QR Code")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .onAppear {
                checkCameraPermission()
            }
            .alert("Camera Access Denied", isPresented: $showingPermissionAlert) {
                Button("Settings") {
                    if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
                        UIApplication.shared.open(settingsURL)
                    }
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("Please enable camera access in Settings to scan QR codes.")
            }
        }
    }
    
    private func checkCameraPermission() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            hasPermission = true
        case .notDetermined:
            requestCameraPermission()
        case .denied, .restricted:
            hasPermission = false
            showingPermissionAlert = true
        @unknown default:
            hasPermission = false
        }
    }
    
    private func requestCameraPermission() {
        AVCaptureDevice.requestAccess(for: .video) { granted in
            DispatchQueue.main.async {
                hasPermission = granted
                if !granted {
                    showingPermissionAlert = true
                }
            }
        }
    }
}

struct QRCodeScannerRepresentable: UIViewControllerRepresentable {
    let onResult: (String) -> Void
    
    func makeUIViewController(context: Context) -> UIViewController {
        // Placeholder for actual QR scanner implementation
        let viewController = UIViewController()
        viewController.view.backgroundColor = .black
        
        let label = UILabel()
        label.text = "QR Scanner Placeholder\nTap to simulate scan"
        label.textColor = .white
        label.textAlignment = .center
        label.numberOfLines = 0
        label.translatesAutoresizingMaskIntoConstraints = false
        
        viewController.view.addSubview(label)
        NSLayoutConstraint.activate([
            label.centerXAnchor.constraint(equalTo: viewController.view.centerXAnchor),
            label.centerYAnchor.constraint(equalTo: viewController.view.centerYAnchor)
        ])
        
        let tapGesture = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.simulateScan))
        viewController.view.addGestureRecognizer(tapGesture)
        
        return viewController
    }
    
    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(onResult: onResult)
    }
    
    class Coordinator: NSObject {
        let onResult: (String) -> Void
        
        init(onResult: @escaping (String) -> Void) {
            self.onResult = onResult
        }
        
        @objc func simulateScan() {
            // Simulate QR code scan result
            onResult("leenvibe://server/localhost:8000?ssl=false")
        }
    }
}

struct ManualServerEntryView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var settingsManager = SettingsManager.shared
    @State private var serverHost = ""
    @State private var serverPort = "8000"
    @State private var useHTTPS = false
    
    var body: some View {
        NavigationView {
            Form {
                Section("Server Details") {
                    TextField("Server Host", text: $serverHost)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    
                    TextField("Port", text: $serverPort)
                        .keyboardType(.numberPad)
                    
                    Toggle("Use HTTPS", isOn: $useHTTPS)
                }
                
                Section("Preview") {
                    Text("\(useHTTPS ? "https" : "http")://\(serverHost):\(serverPort)")
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Manual Entry")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveServerConfiguration()
                        dismiss()
                    }
                    .disabled(serverHost.isEmpty)
                }
            }
            .onAppear {
                serverHost = settingsManager.connectionSettings.serverURL
                serverPort = String(settingsManager.connectionSettings.serverPort)
                useHTTPS = settingsManager.connectionSettings.useHTTPS
            }
        }
    }
    
    private func saveServerConfiguration() {
        settingsManager.connectionSettings.serverURL = serverHost
        settingsManager.connectionSettings.serverPort = Int(serverPort) ?? 8000
        settingsManager.connectionSettings.useHTTPS = useHTTPS
    }
}

struct AdvancedServerSettingsView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                Section("SSL/TLS Settings") {
                    Text("Advanced SSL configuration")
                }
                
                Section("Headers") {
                    Text("Custom HTTP headers")
                }
                
                Section("Debugging") {
                    Text("Network debugging options")
                }
            }
            .navigationTitle("Advanced Settings")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

// MARK: - Preview

#Preview {
    NavigationView {
        ServerSettingsView(webSocketService: WebSocketService())
    }
}