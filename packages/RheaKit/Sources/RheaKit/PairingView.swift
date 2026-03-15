import SwiftUI
#if canImport(UIKit)
import UIKit
import AVFoundation
#endif

/// PairingView — User-facing QR code scanning and pairing status UI.
///
/// States:
/// - Ready: Shows "Scan QR" button
/// - Scanning: Activates camera for QR code capture
/// - Pairing: Shows progress + status messages
/// - Connected: Shows device ID + trust level
/// - Error: Shows error message with retry button
///
/// Usage:
/// ```swift
/// NavigationStack {
///     PairingView()
/// }
/// ```
public struct PairingView: View {
    @StateObject private var pairing = PairingDelegate.shared
    @State private var showQRScanner = false
    @State private var showErrorAlert = false
    @State private var errorMessage = ""

    public init() {}

    public var body: some View {
        VStack(spacing: 24) {
            // MARK: - Header
            VStack(spacing: 8) {
                Image(systemName: statusIcon)
                    .font(.system(size: 48))
                    .foregroundColor(statusColor)
                    .animation(.spring(response: 0.6, dampingFraction: 0.7), value: pairing.pairingTrustLevel)

                Text("Device Pairing")
                    .font(.title2)
                    .fontWeight(.bold)

                Text(pairing.pairingStatusText)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding()
            #if os(iOS)
            .background(Color(.systemGray6))
            #else
            .background(Color.gray.opacity(0.1))
            #endif
            .cornerRadius(12)

            // MARK: - Status Details
            if pairing.isConnected {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Label("Device ID", systemImage: "iphone")
                        Spacer()
                        Text(pairing.linkedDeviceID ?? "Unknown")
                            .font(.caption)
                            .monospaced()
                            .foregroundColor(.secondary)
                    }

                    Divider()

                    HStack {
                        Label("Trust Level", systemImage: "lock.shield")
                        Spacer()
                        Text(pairing.pairingTrustLevel.displayName)
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(trustLevelColor)
                    }

                    Divider()

                    HStack {
                        Label("Public Key", systemImage: "key.circle")
                        Spacer()
                        Text(pairing.publicKeyHex?.prefix(16) ?? "N/A")
                            .font(.caption)
                            .monospaced()
                            .foregroundColor(.secondary)
                    }
                }
                .padding()
                #if os(iOS)
                .background(Color(.systemGray6))
                #else
                .background(Color.gray.opacity(0.1))
                #endif
                .cornerRadius(12)
            }

            // MARK: - Actions
            if !pairing.isConnected {
                Button(action: { showQRScanner = true }) {
                    HStack(spacing: 12) {
                        Image(systemName: "qrcode.viewfinder")
                        Text(pairing.isPairingInProgress ? "Pairing..." : "Scan QR Code")
                    }
                    .frame(maxWidth: .infinity)
                    .padding(12)
                    .background(pairing.isPairingInProgress ? Color.gray : Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(8)
                    .fontWeight(.semibold)
                }
                .disabled(pairing.isPairingInProgress)
            } else {
                Button(action: { resetPairing() }) {
                    HStack(spacing: 12) {
                        Image(systemName: "arrow.clockwise")
                        Text("Re-pair Device")
                    }
                    .frame(maxWidth: .infinity)
                    .padding(12)
                    .background(Color.orange)
                    .foregroundColor(.white)
                    .cornerRadius(8)
                    .fontWeight(.semibold)
                }
            }

            Spacer()

            // MARK: - Info Footer
            VStack(alignment: .leading, spacing: 8) {
                Label("How to pair", systemImage: "info.circle")
                    .font(.caption)
                    .fontWeight(.semibold)

                Text("1. Open the Rhea Control Centre on another device\n2. Go to Settings → Pair New Device\n3. Scan this QR code with your iPhone")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .lineSpacing(2)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            #if os(iOS)
            .background(Color(.systemGray6))
            #else
            .background(Color.gray.opacity(0.1))
            #endif
            .cornerRadius(8)
        }
        .padding()
        .navigationTitle("Pairing")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .sheet(isPresented: $showQRScanner) {
            #if canImport(UIKit)
            QRScannerView { qrString in
                pairing.handleScannedQRCode(qrString)
                showQRScanner = false
            }
            #else
            Text("Scanner only available on iOS")
                .padding()
            #endif
        }
    }

    // MARK: - Computed Properties

    private var statusIcon: String {
        switch pairing.pairingTrustLevel {
        case .unknown: return "qrcode"
        case .pending: return "hourglass"
        case .authenticated: return "checkmark.circle.fill"
        case .revoked: return "xmark.circle.fill"
        }
    }

    private var statusColor: Color {
        switch pairing.pairingTrustLevel {
        case .unknown: return .gray
        case .pending: return .orange
        case .authenticated: return .green
        case .revoked: return .red
        }
    }

    private var trustLevelColor: Color {
        switch pairing.pairingTrustLevel {
        case .unknown: return .secondary
        case .pending: return .orange
        case .authenticated: return .green
        case .revoked: return .red
        }
    }

    // MARK: - Actions

    private func resetPairing() {
        // Clear pairing state
        // TODO: Implement keychain cleanup
    }
}

// MARK: - QR Scanner View

#if canImport(UIKit)
struct QRScannerView: UIViewControllerRepresentable {
    let onScanned: (String) -> Void

    func makeUIViewController(context: Context) -> QRScannerViewController {
        let controller = QRScannerViewController()
        controller.onScanned = onScanned
        return controller
    }

    func updateUIViewController(_ uiViewController: QRScannerViewController, context: Context) {}
}

// MARK: - QR Scanner View Controller

final class QRScannerViewController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    var onScanned: ((String) -> Void)?

    private let captureSession = AVCaptureSession()
    private var previewLayer: AVCaptureVideoPreviewLayer?

    override func viewDidLoad() {
        super.viewDidLoad()
        setupCamera()
    }

    private func setupCamera() {
        guard let videoCaptureDevice = AVCaptureDevice.default(for: .video) else {
            showError("Camera not available")
            return
        }

        let videoInput: AVCaptureDeviceInput
        do {
            videoInput = try AVCaptureDeviceInput(device: videoCaptureDevice)
        } catch {
            showError("Unable to access camera")
            return
        }

        if captureSession.canAddInput(videoInput) {
            captureSession.addInput(videoInput)
        } else {
            showError("Cannot add video input")
            return
        }

        let metadataOutput = AVCaptureMetadataOutput()
        if captureSession.canAddOutput(metadataOutput) {
            captureSession.addOutput(metadataOutput)
            metadataOutput.setMetadataObjectsDelegate(self, queue: DispatchQueue.main)
            metadataOutput.metadataObjectTypes = [.qr]
        } else {
            showError("Cannot add metadata output")
            return
        }

        let previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
        previewLayer.frame = view.layer.bounds
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)
        self.previewLayer = previewLayer

        DispatchQueue.global(qos: .userInitiated).async {
            self.captureSession.startRunning()
        }
    }

    func metadataOutput(
        _ output: AVCaptureMetadataOutput,
        didOutput metadataObjects: [AVMetadataObject],
        from connection: AVCaptureConnection
    ) {
        captureSession.stopRunning()

        for metadata in metadataObjects {
            if let qrCodeObject = metadata as? AVMetadataMachineReadableCodeObject,
               qrCodeObject.type == .qr,
               let stringValue = qrCodeObject.stringValue {
                onScanned?(stringValue)
                dismiss(animated: true)
                return
            }
        }
    }

    private func showError(_ message: String) {
        let alert = UIAlertController(
            title: "Camera Error",
            message: message,
            preferredStyle: .alert
        )
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in
            self.dismiss(animated: true)
        })
        present(alert, animated: true)
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        if captureSession.isRunning {
            captureSession.stopRunning()
        }
    }
}
#endif

// MARK: - Preview

#if DEBUG
struct PairingView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack {
            PairingView()
        }
    }
}
#endif
