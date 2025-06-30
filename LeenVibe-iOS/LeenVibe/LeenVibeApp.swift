import SwiftUI

@main
struct LeanVibeApp: App {
    @StateObject private var coordinator = AppCoordinator()
    
    var body: some Scene {
        WindowGroup {
            contentView
                .animation(.easeInOut(duration: 0.5), value: coordinator.appState)
        }
    }
    
    @ViewBuilder
    private var contentView: some View {
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
                onRetry: coordinator.retry,
                onReset: coordinator.resetConfiguration
            )
        }
    }
}