import SwiftUI

struct VoiceWaveformView: View {
    let audioLevel: Float
    let isListening: Bool
    let recognitionState: SpeechRecognitionService.RecognitionState
    
    @State private var animationOffset: CGFloat = 0
    @State private var pulseScale: CGFloat = 1.0
    
    private let numberOfBars = 40
    private let animationDuration: Double = 0.1
    
    var body: some View {
        GeometryReader { geometry in
            HStack(alignment: .center, spacing: 2) {
                ForEach(0..<numberOfBars, id: \.self) { index in
                    WaveformBar(
                        index: index,
                        audioLevel: audioLevel,
                        isListening: isListening,
                        recognitionState: recognitionState,
                        totalBars: numberOfBars,
                        animationOffset: animationOffset
                    )
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .background(
            Circle()
                .fill(
                    RadialGradient(
                        gradient: Gradient(colors: [
                            Color.blue.opacity(isListening ? 0.3 : 0.1),
                            Color.clear
                        ]),
                        center: .center,
                        startRadius: 20,
                        endRadius: 60
                    )
                )
                .scaleEffect(pulseScale)
                .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: isListening)
        )
        .onAppear {
            startAnimation()
            if isListening {
                pulseScale = 1.2
            }
        }
        .onChange(of: isListening) { listening in
            pulseScale = listening ? 1.2 : 1.0
        }
    }
    
    private func startAnimation() {
        withAnimation(.linear(duration: animationDuration).repeatForever(autoreverses: false)) {
            animationOffset = 1.0
        }
    }
}

struct WaveformBar: View {
    let index: Int
    let audioLevel: Float
    let isListening: Bool
    let recognitionState: SpeechRecognitionService.RecognitionState
    let totalBars: Int
    let animationOffset: CGFloat
    
    @State private var barHeight: CGFloat = 4
    
    private var maxHeight: CGFloat { 60 }
    private var minHeight: CGFloat { 4 }
    
    var body: some View {
        RoundedRectangle(cornerRadius: 2)
            .fill(barColor)
            .frame(width: 3, height: barHeight)
            .animation(.easeInOut(duration: 0.1), value: barHeight)
            .onAppear {
                updateBarHeight()
            }
            .onChange(of: audioLevel) { _ in
                updateBarHeight()
            }
            .onChange(of: isListening) { _ in
                updateBarHeight()
            }
            .onChange(of: recognitionState) { _ in
                updateBarHeight()
            }
    }
    
    private var barColor: Color {
        switch recognitionState {
        case .listening:
            let intensity = CGFloat(audioLevel) + 0.3
            return Color.blue.opacity(intensity)
        case .processing:
            return Color.orange.opacity(0.8)
        case .completed:
            return Color.green.opacity(0.8)
        case .error:
            return Color.red.opacity(0.8)
        case .idle:
            return Color.gray.opacity(0.4)
        }
    }
    
    private func updateBarHeight() {
        guard isListening else {
            // Show gentle idle animation
            let idleHeight = minHeight + (sin(Double(index) * 0.5 + Double(animationOffset) * .pi * 2) + 1) * 2
            barHeight = max(minHeight, idleHeight)
            return
        }
        
        // Calculate position-based modifier for wave effect
        let normalizedPosition = CGFloat(index) / CGFloat(totalBars)
        let waveEffect = sin(normalizedPosition * .pi * 4 + animationOffset * .pi * 8)
        
        // Calculate audio-responsive height
        let audioHeight = CGFloat(audioLevel) * maxHeight
        let baseHeight = max(minHeight, audioHeight)
        
        // Add wave effect and randomization
        let waveHeight = baseHeight + (waveEffect * 10)
        let randomFactor = CGFloat.random(in: 0.8...1.2)
        
        barHeight = max(minHeight, min(maxHeight, waveHeight * randomFactor))
    }
}

// MARK: - Advanced Waveform View with Frequency Analysis

struct AdvancedVoiceWaveformView: View {
    let audioLevel: Float
    let isListening: Bool
    let recognitionState: SpeechRecognitionService.RecognitionState
    
    @State private var frequencyData: [Float] = Array(repeating: 0, count: 32)
    @State private var animationPhase: Double = 0
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Background glow
                backgroundGlow
                
                // Main waveform
                mainWaveform(geometry: geometry)
                
                // Center pulse
                centerPulse
                
                // Status indicator
                statusIndicator
            }
        }
        .onAppear {
            startFrequencyAnimation()
        }
    }
    
    private var backgroundGlow: some View {
        Circle()
            .fill(
                RadialGradient(
                    gradient: Gradient(colors: [
                        stateColor.opacity(0.3),
                        stateColor.opacity(0.1),
                        Color.clear
                    ]),
                    center: .center,
                    startRadius: 10,
                    endRadius: 100
                )
            )
            .scaleEffect(isListening ? 1.5 : 1.0)
            .animation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true), value: isListening)
    }
    
    private func mainWaveform(geometry: GeometryProxy) -> some View {
        HStack(alignment: .center, spacing: 1) {
            ForEach(0..<frequencyData.count, id: \.self) { index in
                FrequencyBar(
                    frequency: frequencyData[index],
                    index: index,
                    isListening: isListening,
                    color: stateColor,
                    animationPhase: animationPhase
                )
            }
        }
        .frame(width: min(geometry.size.width * 0.8, 200))
    }
    
    private var centerPulse: some View {
        Circle()
            .stroke(stateColor, lineWidth: 2)
            .frame(width: 60, height: 60)
            .scaleEffect(isListening ? 1.2 : 1.0)
            .opacity(isListening ? 0.6 : 0.3)
            .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: isListening)
    }
    
    private var statusIndicator: some View {
        VStack {
            Spacer()
            
            HStack {
                Circle()
                    .fill(stateColor)
                    .frame(width: 8, height: 8)
                
                Text(stateDescription)
                    .font(.caption)
                    .foregroundColor(stateColor)
            }
            .padding(.bottom, 8)
        }
    }
    
    private var stateColor: Color {
        switch recognitionState {
        case .listening:
            return .blue
        case .processing:
            return .orange
        case .completed:
            return .green
        case .error:
            return .red
        case .idle:
            return .gray
        }
    }
    
    private var stateDescription: String {
        switch recognitionState {
        case .listening:
            return "Listening..."
        case .processing:
            return "Processing..."
        case .completed:
            return "Completed"
        case .error(let message):
            return "Error: \(message)"
        case .idle:
            return "Ready"
        }
    }
    
    private func startFrequencyAnimation() {
        Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { _ in
            Task { @MainActor in
                updateFrequencyData()
                withAnimation(.linear(duration: 0.05)) {
                    animationPhase += 0.1
                }
            }
        }
    }
    
    private func updateFrequencyData() {
        for i in 0..<frequencyData.count {
            if isListening {
                // Simulate frequency analysis based on audio level
                let baseAmplitude = audioLevel * Float.random(in: 0.5...1.5)
                let frequencyBand = sin(Double(i) * 0.3 + animationPhase) * 0.3 + 0.7
                frequencyData[i] = baseAmplitude * Float(frequencyBand)
            } else {
                // Gentle idle animation
                let idleAmplitude = sin(Double(i) * 0.2 + animationPhase * 0.5) * 0.1 + 0.05
                frequencyData[i] = Float(idleAmplitude)
            }
        }
    }
}

struct FrequencyBar: View {
    let frequency: Float
    let index: Int
    let isListening: Bool
    let color: Color
    let animationPhase: Double
    
    private var barHeight: CGFloat {
        let baseHeight: CGFloat = 4
        let maxHeight: CGFloat = 40
        
        if isListening {
            let height = CGFloat(frequency) * maxHeight
            return max(baseHeight, height)
        } else {
            // Subtle idle animation
            let idleHeight = baseHeight + sin(Double(index) * 0.5 + animationPhase) * 2
            return max(baseHeight, idleHeight)
        }
    }
    
    private var barOpacity: Double {
        isListening ? Double(frequency) + 0.3 : 0.5
    }
    
    var body: some View {
        RoundedRectangle(cornerRadius: 1.5)
            .fill(color.opacity(barOpacity))
            .frame(width: 3, height: barHeight)
            .animation(.easeOut(duration: 0.05), value: frequency)
    }
}

#Preview {
    VStack(spacing: 40) {
        VoiceWaveformView(
            audioLevel: 0.5,
            isListening: true,
            recognitionState: .listening
        )
        .frame(height: 120)
        
        AdvancedVoiceWaveformView(
            audioLevel: 0.3,
            isListening: false,
            recognitionState: .idle
        )
        .frame(height: 120)
    }
    .padding()
}