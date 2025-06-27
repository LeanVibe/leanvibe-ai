import SwiftUI
import AVFoundation
import AudioToolbox

struct QRScannerView: View {
    @Binding var isPresented: Bool
    @ObservedObject var webSocketService: WebSocketService
    @State private var isScanning = true
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationView {
            ZStack {
                // Camera view
                CameraView(
                    isScanning: $isScanning,
                    onQRCodeDetected: handleQRCode,
                    onError: handleError
                )
                
                // Overlay with scanning frame
                ScannerOverlay()
                
                // Error message
                if let errorMessage = errorMessage {
                    VStack {
                        Spacer()
                        Text(errorMessage)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.red.opacity(0.8))
                            .cornerRadius(8)
                            .padding()
                    }
                }
            }
            .navigationTitle("Scan QR Code")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        isPresented = false
                    }
                    .foregroundColor(.white)
                }
            }
            .background(Color.black)
        }
    }
    
    private func handleQRCode(_ code: String) {
        isScanning = false
        
        // Parse and connect using QR code
        webSocketService.connectWithQRCode(code) { success, error in
            DispatchQueue.main.async {
                if success {
                    isPresented = false
                } else {
                    errorMessage = error ?? "Failed to connect"
                    // Resume scanning after 2 seconds
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                        errorMessage = nil
                        isScanning = true
                    }
                }
            }
        }
    }
    
    private func handleError(_ error: String) {
        errorMessage = error
    }
}

struct CameraView: UIViewRepresentable {
    @Binding var isScanning: Bool
    let onQRCodeDetected: (String) -> Void
    let onError: (String) -> Void
    
    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: UIScreen.main.bounds)
        
        let captureSession = AVCaptureSession()
        
        guard let videoCaptureDevice = AVCaptureDevice.default(for: .video) else {
            onError("Camera not available")
            return view
        }
        
        let videoInput: AVCaptureDeviceInput
        
        do {
            videoInput = try AVCaptureDeviceInput(device: videoCaptureDevice)
        } catch {
            onError("Camera input error")
            return view
        }
        
        if (captureSession.canAddInput(videoInput)) {
            captureSession.addInput(videoInput)
        } else {
            onError("Cannot add camera input")
            return view
        }
        
        let metadataOutput = AVCaptureMetadataOutput()
        
        if (captureSession.canAddOutput(metadataOutput)) {
            captureSession.addOutput(metadataOutput)
            
            metadataOutput.setMetadataObjectsDelegate(context.coordinator, queue: DispatchQueue.main)
            metadataOutput.metadataObjectTypes = [.qr]
        } else {
            onError("Cannot add metadata output")
            return view
        }
        
        let previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
        previewLayer.frame = view.layer.bounds
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)
        
        context.coordinator.captureSession = captureSession
        
        DispatchQueue.global(qos: .background).async {
            captureSession.startRunning()
        }
        
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {
        if isScanning {
            if !(context.coordinator.captureSession?.isRunning ?? false) {
                DispatchQueue.global(qos: .background).async {
                    context.coordinator.captureSession?.startRunning()
                }
            }
        } else {
            context.coordinator.captureSession?.stopRunning()
        }
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, AVCaptureMetadataOutputObjectsDelegate {
        var parent: CameraView
        var captureSession: AVCaptureSession?
        
        init(_ parent: CameraView) {
            self.parent = parent
        }
        
        func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
            if let metadataObject = metadataObjects.first {
                guard let readableObject = metadataObject as? AVMetadataMachineReadableCodeObject else { return }
                guard let stringValue = readableObject.stringValue else { return }
                
                // Vibrate to indicate scan
                AudioServicesPlaySystemSound(SystemSoundID(kSystemSoundID_Vibrate))
                
                parent.onQRCodeDetected(stringValue)
            }
        }
    }
}

struct ScannerOverlay: View {
    var body: some View {
        ZStack {
            // Semi-transparent background
            Color.black.opacity(0.5)
            
            // Clear scanning area
            RoundedRectangle(cornerRadius: 16)
                .frame(width: 250, height: 250)
                .blendMode(.destinationOut)
        }
        .compositingGroup()
        .overlay(
            // Scanning frame
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.white, lineWidth: 3)
                .frame(width: 250, height: 250)
                .overlay(
                    VStack {
                        Spacer()
                        Text("Point camera at QR code")
                            .foregroundColor(.white)
                            .font(.headline)
                            .padding(.bottom, 20)
                    }
                )
        )
    }
}