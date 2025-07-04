import SwiftUI
import AVFoundation
import Foundation

/// Server Configuration Settings view for managing backend connection
/// NO HARDCODED VALUES - Everything comes from dynamic configuration
@available(iOS 18.0, macOS 14.0, *)
struct ServerSettingsView: View {
    
    // MARK: - Properties
    
    @StateObject private var webSocketService = WebSocketService.shared
    // TODO: Re-enable BackendSettingsService after dependency resolution
    // @StateObject private var backendService = BackendSettingsService.shared
    @State private var isBackendAvailable = false
    @State private var config = AppConfiguration.shared
    @State private var showingQRScanner = false
    @State private var showingManualEntry = false
    @State private var isTestingConnection = false
    @State private var testResult: ConnectionTestResult?
    @State private var manualURL = ""
    @State private var showingResetConfirmation = false
    
    enum ConnectionTestResult {
        case success(String)
        case failure(String)
    }
    
    // MARK: - Body
    
    var body: some View {
        List {
            // Current Configuration
            currentConfigSection
            
            // Connection Status  
            connectionStatusSection
            
            // Setup Methods
            setupMethodsSection
            
            // Connection Testing
            testingSection
            
            // Advanced Options
            advancedSection
        }
        .navigationTitle("Server Settings")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingQRScanner) {
            QRCodeScannerView { qrCode in
                handleQRCodeScanned(qrCode)
            }
        }
        .sheet(isPresented: $showingManualEntry) {
            ManualServerEntryView(url: $manualURL) { url in
                handleManualURLEntry(url)
            }
        }
        .confirmationDialog(
            "Reset Server Configuration",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset Configuration", role: .destructive) {
                resetServerConfiguration()
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will remove the current server configuration. You'll need to scan a QR code or manually enter server details again.")
        }
    }
    
    // MARK: - View Sections
    
    private var currentConfigSection: some View {
        Section("Current Configuration") {
            if config.isBackendConfigured {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Backend URL")
                            .fontWeight(.medium)
                        Spacer()
                        Text(config.apiBaseURL)
                            .foregroundColor(.secondary)
                            .font(.caption)
                            .multilineTextAlignment(.trailing)
                    }
                    
                    HStack {
                        Text("WebSocket URL")
                            .fontWeight(.medium)
                        Spacer()
                        Text(config.webSocketURL)
                            .foregroundColor(.secondary)
                            .font(.caption)
                            .multilineTextAlignment(.trailing)
                    }
                    
                    HStack {
                        Text("Environment")
                            .fontWeight(.medium)
                        Spacer()
                        Text(config.environmentName)
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                }
                .padding(.vertical, 4)
            } else {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.orange)
                        Text("No Backend Configured")
                            .fontWeight(.medium)
                    }
                    
                    Text("To use LeanVibe, you need to connect to a backend server. Use the QR code from your Mac agent or manually enter server details.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
    }
    
    private var connectionStatusSection: some View {
        Section("Connection Status") {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("WebSocket Connection")
                        .fontWeight(.medium)
                    
                    HStack {
                        Circle()
                            .fill(webSocketService.isConnected ? .green : .red)
                            .frame(width: 8, height: 8)
                        
                        Text(webSocketService.connectionStatus)
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                }
                
                Spacer()
                
                if config.isBackendConfigured {
                    Button(webSocketService.isConnected ? "Disconnect" : "Connect") {
                        if webSocketService.isConnected {
                            webSocketService.disconnect()
                        } else {
                            webSocketService.connect()
                        }
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
            }
            
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Backend API")
                        .fontWeight(.medium)
                    
                    HStack {
                        Circle()
                            .fill(isBackendAvailable ? .green : .red)
                            .frame(width: 8, height: 8)
                        
                        Text(isBackendAvailable ? "Available" : "Unavailable")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                }
                
                Spacer()
                
                if config.isBackendConfigured {
                    Button("Test") {
                        Task {
                            await testBackendConnection()
                        }
                    }
                    .disabled(isTestingConnection)
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
            }
            
            if let error = webSocketService.lastError {
                Text("Error: \(error)")
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.top, 4)
            }
        }
    }
    
    private var setupMethodsSection: some View {
        Section("Setup Backend Connection") {
            Button(action: {
                showingQRScanner = true
            }) {
                SettingsRow(
                    icon: "qrcode.viewfinder",
                    iconColor: .blue,
                    title: "Scan QR Code",
                    subtitle: "Automatic setup from Mac agent"
                )
            }
            .buttonStyle(.plain)
            
            Button(action: {
                showingManualEntry = true
            }) {
                SettingsRow(
                    icon: "text.cursor",
                    iconColor: .green,
                    title: "Manual Entry",
                    subtitle: "Enter server URL manually"
                )
            }
            .buttonStyle(.plain)
            
            if config.isBackendConfigured {
                Button(action: {
                    showingResetConfirmation = true
                }) {
                    SettingsRow(
                        icon: "trash",
                        iconColor: .red,
                        title: "Reset Configuration",
                        subtitle: "Remove current server settings"
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }
    
    private var testingSection: some View {
        Section("Connection Testing") {
            Button(action: {
                Task {
                    await runFullConnectionTest()
                }
            }) {
                HStack {
                    if isTestingConnection {
                        ProgressView()
                            .controlSize(.small)
                        Text("Testing Connection...")
                    } else {
                        SettingsRow(
                            icon: "network",
                            iconColor: .purple,
                            title: "Test Full Connection",
                            subtitle: "Test API, WebSocket, and features"
                        )
                    }
                }
            }
            .buttonStyle(.plain)
            .disabled(!config.isBackendConfigured || isTestingConnection)
            
            if let result = testResult {
                switch result {
                case .success(let message):
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text(message)
                            .font(.caption)
                            .foregroundColor(.green)
                    }
                    .padding(.top, 4)
                    
                case .failure(let error):
                    HStack {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.red)
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                    .padding(.top, 4)
                }
            }
        }
    }
    
    private var advancedSection: some View {
        Section("Advanced") {
            NavigationLink("Network Diagnostics") {
                NetworkDiagnosticsView()
            }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Configuration Details")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                if config.isBackendConfigured {
                    Group {
                        HStack {
                            Text("Network Timeout:")
                            Spacer()
                            Text("\(Int(config.networkTimeout))s")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Max Retry Attempts:")
                            Spacer()
                            Text("\(config.maxRetryAttempts)")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Text("Certificate Pinning:")
                            Spacer()
                            Text(config.isCertificatePinningEnabled ? "Enabled" : "Disabled")
                                .foregroundColor(.secondary)
                        }
                    }
                    .font(.caption)
                } else {
                    Text("Configure backend to see details")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .italic()
                }
            }
            .padding(.vertical, 4)
        }
    }
    
    // MARK: - Actions
    
    private func handleQRCodeScanned(_ qrCode: String) {
        Task {
            do {
                try await webSocketService.connectWithQRCode(qrCode)
                
                // Update our local config reference
                config = AppConfiguration.shared
                
                // Test the connection
                await testBackendConnection()
                
            } catch {
                testResult = .failure("QR Setup Failed: \(error.localizedDescription)")
            }
        }
        
        showingQRScanner = false
    }
    
    private func handleManualURLEntry(_ url: String) {
        do {
            try config.configureBackend(url: url)
            
            // Try to connect
            webSocketService.connectToSavedConnection()
            
            Task {
                await testBackendConnection()
            }
            
        } catch {
            testResult = .failure("Invalid URL: \(error.localizedDescription)")
        }
        
        showingManualEntry = false
    }
    
    private func testBackendConnection() async {
        isTestingConnection = true
        
        // TODO: Re-implement with BackendSettingsService after dependency resolution
        let isAvailable = await pingBackendDirectly()
        
        await MainActor.run {
            if isAvailable {
                testResult = .success("Backend API is reachable")
                isBackendAvailable = true
            } else {
                testResult = .failure("Backend API is not reachable")
                isBackendAvailable = false
            }
            isTestingConnection = false
        }
    }
    
    private func runFullConnectionTest() async {
        isTestingConnection = true
        testResult = nil
        
        // Test API availability
        let apiAvailable = await pingBackendDirectly()
        
        if !apiAvailable {
            await MainActor.run {
                testResult = .failure("API test failed - backend not reachable")
                isTestingConnection = false
            }
            return
        }
        
        // Test WebSocket connection
        if !webSocketService.isConnected {
            webSocketService.connect()
            
            // Wait a bit for connection
            try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
        }
        
        await MainActor.run {
            if webSocketService.isConnected {
                testResult = .success("All connections successful - API ✓ WebSocket ✓")
            } else {
                testResult = .failure("API available but WebSocket connection failed")
            }
            isTestingConnection = false
        }
    }
    
    private func resetServerConfiguration() {
        config.resetBackendConfiguration()
        webSocketService.disconnect()
        
        // Clear test results
        testResult = nil
        
        // Update local reference
        config = AppConfiguration.shared
    }
    
    // MARK: - Temporary Direct Backend Methods (until dependency resolution)
    
    private func pingBackendDirectly() async -> Bool {
        guard config.isBackendConfigured else {
            return false
        }
        
        do {
            let url = URL(string: "\(config.apiBaseURL)/api/health")!
            var request = URLRequest(url: url)
            request.httpMethod = "GET"
            request.timeoutInterval = 5.0 // Quick ping
            
            let (_, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                return httpResponse.statusCode == 200
            }
            
            return false
            
        } catch {
            return false
        }
    }
}

// MARK: - Supporting Views

@available(iOS 18.0, macOS 14.0, *)
struct QRCodeScannerView: View {
    let onQRCodeScanned: (String) -> Void
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack {
                Text("Scan QR Code from Mac Agent")
                    .font(.headline)
                    .padding()
                
                // QR Scanner would go here - placeholder for now
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(.systemGray5))
                    .frame(width: 250, height: 250)
                    .overlay {
                        VStack {
                            Image(systemName: "qrcode.viewfinder")
                                .font(.largeTitle)
                                .foregroundColor(.secondary)
                            Text("QR Scanner")
                                .foregroundColor(.secondary)
                        }
                    }
                
                Text("Position the QR code from your LeanVibe Mac agent within the frame")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding()
                
                Button("Test QR Code") {
                    // For testing - simulate a QR code scan
                    let testQRData = """
                    {
                        "leanvibe": {
                            "server": {
                                "host": "localhost",
                                "port": 8000,
                                "websocket_path": "/ws"
                            },
                            "metadata": {
                                "server_name": "Local Development",
                                "network": "development"
                            }
                        }
                    }
                    """
                    onQRCodeScanned(testQRData)
                }
                .buttonStyle(.bordered)
                
                Spacer()
            }
            .navigationTitle("QR Scanner")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ManualServerEntryView: View {
    @Binding var url: String
    let onURLEntered: (String) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var manualURL = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Server Configuration") {
                    TextField("Backend URL", text: $manualURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                    
                    Text("Example: http://192.168.1.100:8000")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Section("Common Configurations") {
                    Button("Local Development (localhost:8000)") {
                        manualURL = "http://localhost:8000"
                    }
                    
                    Button("Local Network (192.168.1.x:8000)") {
                        manualURL = "http://192.168.1.100:8000"
                    }
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
                    Button("Connect") {
                        onURLEntered(manualURL)
                    }
                    .disabled(manualURL.isEmpty)
                }
            }
        }
        .onAppear {
            manualURL = url
        }
    }
}

#Preview {
    NavigationView {
        ServerSettingsView()
    }
}