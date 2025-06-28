import SwiftUI

@main
struct LeenVibeApp: App {
    @StateObject private var coordinator = AppCoordinator()
    
    var body: some Scene {
        WindowGroup {
            Group {
                switch coordinator.appState {
                case .launching:
                    LaunchScreenView()
                case .needsConfiguration:
                    QROnboardingView(coordinator: coordinator)
                case .ready:
                    DashboardTabView()
                        .environmentObject(coordinator)
                case .error(let errorMessage):
                    ErrorRecoveryView(
                        errorMessage: errorMessage,
                        onRetry: coordinator.retryConfiguration,
                        onReset: coordinator.resetApp
                    )
                }
            }
            .animation(.easeInOut(duration: 0.5), value: coordinator.appState)
        }
    }
}