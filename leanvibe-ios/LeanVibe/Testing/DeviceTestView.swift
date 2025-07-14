import SwiftUI

/// Device testing validation view for iOS
struct DeviceTestView: View {
    @StateObject private var testSuite = DeviceTestSuite()
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                VStack(spacing: 8) {
                    Text("📱 Device Validation")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text("Comprehensive testing for LeanVibe compatibility")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.top)
                
                // Test Status
                if testSuite.isRunning {
                    VStack(spacing: 12) {
                        ProgressView()
                            .scaleEffect(1.5)
                        
                        Text("Running: \(testSuite.currentTest)")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        Text("Please wait while we validate your device...")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding()
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(12)
                } else {
                    // Overall Status
                    overallStatusView
                }
                
                // Test Results
                if !testSuite.testResults.isEmpty {
                    testResultsList
                }
                
                Spacer()
                
                // Action Buttons
                actionButtons
            }
            .padding()
            .navigationTitle("Device Testing")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Close") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private var overallStatusView: some View {
        VStack(spacing: 8) {
            statusIcon
            
            Text(statusText)
                .font(.title2)
                .fontWeight(.semibold)
            
            Text(statusDescription)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .background(statusColor.opacity(0.1))
        .cornerRadius(12)
    }
    
    private var statusIcon: some View {
        Group {
            switch testSuite.overallStatus {
            case .notStarted:
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
            case .running:
                ProgressView()
                    .scaleEffect(2)
            case .passed:
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.green)
            case .failed:
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.red)
            case .partial:
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.orange)
            }
        }
    }
    
    private var statusText: String {
        switch testSuite.overallStatus {
        case .notStarted:
            return "Ready to Test"
        case .running:
            return "Testing in Progress"
        case .passed:
            return "All Tests Passed"
        case .failed:
            return "Tests Failed"
        case .partial:
            return "Partial Success"
        }
    }
    
    private var statusDescription: String {
        switch testSuite.overallStatus {
        case .notStarted:
            return "Tap 'Start Tests' to begin comprehensive device validation"
        case .running:
            return "Running comprehensive tests to validate your device"
        case .passed:
            return "Your device is fully compatible with LeanVibe"
        case .failed:
            return "Critical issues found that may affect LeanVibe functionality"
        case .partial:
            return "Some issues found but core functionality should work"
        }
    }
    
    private var statusColor: Color {
        switch testSuite.overallStatus {
        case .notStarted:
            return .gray
        case .running:
            return .blue
        case .passed:
            return .green
        case .failed:
            return .red
        case .partial:
            return .orange
        }
    }
    
    private var testResultsList: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Test Results")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(testSuite.testResults.count) tests")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(testSuite.testResults.indices, id: \.self) { index in
                        let result = testSuite.testResults[index]
                        TestResultRow(result: result)
                    }
                }
                .padding(.vertical, 4)
            }
            .frame(maxHeight: 300)
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(12)
    }
    
    private var actionButtons: some View {
        VStack(spacing: 12) {
            if testSuite.isRunning {
                Button("Running Tests...") {
                    // Tests are running, button disabled
                }
                .disabled(true)
                .buttonStyle(PrimaryButtonStyle())
            } else {
                Button("Start Device Tests") {
                    Task {
                        await testSuite.runDeviceValidationSuite()
                    }
                }
                .buttonStyle(PrimaryButtonStyle())
            }
            
            // Show report button if tests completed
            if !testSuite.testResults.isEmpty && !testSuite.isRunning {
                Button("View Detailed Report") {
                    showDetailedReport()
                }
                .buttonStyle(SecondaryButtonStyle())
            }
        }
    }
    
    private func showDetailedReport() {
        // Show detailed test report
        print("📊 Detailed Report:")
        print(testSuite.getFormattedResults())
        
        let criticalIssues = testSuite.getCriticalIssues()
        if !criticalIssues.isEmpty {
            print("\n🚨 Critical Issues:")
            criticalIssues.forEach { print("  - \($0)") }
        }
        
        let recommendations = testSuite.getRecommendations()
        if !recommendations.isEmpty {
            print("\n💡 Recommendations:")
            recommendations.forEach { print("  - \($0)") }
        }
    }
}

/// Individual test result row
struct TestResultRow: View {
    let result: DeviceTestSuite.TestResult
    
    var body: some View {
        HStack {
            // Status icon
            statusIcon
            
            // Test info
            VStack(alignment: .leading, spacing: 4) {
                Text(result.testName)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(result.details)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            
            Spacer()
            
            // Duration
            Text("\(String(format: "%.1f", result.duration))s")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(statusColor.opacity(0.1))
        .cornerRadius(8)
    }
    
    private var statusIcon: some View {
        Group {
            switch result.status {
            case .passed:
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
            case .failed:
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.red)
            case .partial:
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.orange)
            case .running:
                ProgressView()
                    .scaleEffect(0.8)
            case .notStarted:
                Image(systemName: "circle")
                    .foregroundColor(.gray)
            }
        }
        .font(.title3)
    }
    
    private var statusColor: Color {
        switch result.status {
        case .passed:
            return .green
        case .failed:
            return .red
        case .partial:
            return .orange
        case .running:
            return .blue
        case .notStarted:
            return .gray
        }
    }
}

/// Primary button style
struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(configuration.isPressed ? Color.blue.opacity(0.8) : Color.blue)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

/// Secondary button style
struct SecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.subheadline)
            .foregroundColor(.blue)
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.blue, lineWidth: 1)
                    .fill(configuration.isPressed ? Color.blue.opacity(0.1) : Color.clear)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

/// Preview
struct DeviceTestView_Previews: PreviewProvider {
    static var previews: some View {
        DeviceTestView()
    }
}