import Foundation
import JavaScriptCore
import Combine

/// PlayRuntimeCore - Minimal JavaScript Kernel for RheaKit
///
/// This class provides a lightweight JavaScript runtime environment beneath the SwiftUI layer.
/// It's designed as a minimal kernel, not a full "PlayOS" - just enough to support
/// the playful, game-like interactions in RheaKit.
///
/// ## Architecture
/// ```
/// SwiftUI Layer (NodeEditorView, etc.)
///     ↓
/// PlayRuntimeCore (Swift Host)
///     ↓ (console bridge, exception handling)
/// JavaScriptCore (JSContext)
///     ↓
/// runtime.js → app.js (minimal bootstrap)
/// ```
///
/// ## Bridge Mechanisms
/// 1. **Console Bridge**: JS console.log/warn/error → Swift logs + @MainActor UI updates
/// 2. **Exception Bridge**: JS exceptions → Swift error handling + status updates
/// 3. **Bootstrap Sequence**: runtime.js → app.js (tracked via loadedScripts array)
///
/// ## Key Features
/// - Isolated JSContext per runtime instance
/// - Automatic exception catching and reporting
/// - Real-time log streaming from JS to Swift
/// - Minimal footprint - only essential bootstrap scripts
///
/// ## Usage
/// ```swift
/// let runtime = PlayRuntimeCore()
/// runtime.boot()  // Starts the JS runtime
/// ```
///
/// [PROTOCOL: MINIMAL_KERNEL_V1] - Keep it minimal, document reality.
@MainActor
public final class PlayRuntimeCore: ObservableObject {
    @Published public private(set) var status: RuntimeStatus = .idle
    @Published public private(set) var logs: [String] = []
    @Published public private(set) var loadedScripts: [String] = []
    @Published public private(set) var lastError: String? = nil
    
    private var context: JSContext?
    private let bootstrapSequence = ["runtime", "app"]
    
    public enum RuntimeStatus: String {
        case idle, booting, running, failed
    }
    
    public init() {
        appendLog("Core initialized. Ready for boot.")
    }
    
    /// Executes the primary bootstrap sequence: runtime.js → app.js
    /// 
    /// This method creates a fresh JavaScript runtime environment by:
    /// 1. Creating a new, isolated JSContext
    /// 2. Installing the console bridge for JS→Swift logging
    /// 3. Setting up exception handling for error recovery
    /// 4. Loading runtime.js (establishes PlayRuntime global)
    /// 5. Loading app.js (marks app entry point)
    /// 
    /// The bootstrap is designed to be minimal and fast, providing just enough
    /// JavaScript infrastructure to support the playful UI interactions.
    /// 
    /// Use this method to restart the JS runtime or initialize it for the first time.
    /// All previous state is cleared when boot() is called.
    public func boot() {
        status = .booting
        lastError = nil
        loadedScripts.removeAll()
        
        appendLog("--- RUNTIME BOOT START ---")
        
        // 1. Create fresh context
        appendLog("Creating isolated JSContext...")
        guard let newContext = JSContext() else {
            fail(with: "Failed to allocate JSContext.")
            return
        }
        
        // 2. Setup bridges
        appendLog("Installing console bridge...")
        setupConsoleBridge(newContext)
        
        appendLog("Installing exception handler...")
        setupExceptionHandler(newContext)
        
        self.context = newContext
        
        // 3. Load bootstrap layer
        for scriptName in bootstrapSequence {
            do {
                appendLog("Preparing to load plugin: \(scriptName).js")
                try loadBundledScript(named: scriptName, into: newContext)
                loadedScripts.append("\(scriptName).js")
                appendLog("Successfully initialized: \(scriptName).js")
            } catch {
                fail(with: "Bootstrap failed at [\(scriptName)]: \(error.localizedDescription)")
                return
            }
        }
        
        status = .running
        appendLog("--- RUNTIME BOOT COMPLETE: RUNNING ---")
    }
    
    private func loadBundledScript(named name: String, into context: JSContext) throws {
        guard let url = Bundle.module.url(forResource: name, withExtension: "js", subdirectory: "JSCoreScripts") else {
            throw RuntimeError.missingResource(name)
        }
        
        let source = try String(contentsOf: url, encoding: .utf8)
        appendLog("Evaluating \(name).js (\(source.count) bytes)")
        
        context.evaluateScript(source, withSourceURL: url)
        
        if let exception = context.exception {
            let msg = exception.toString() ?? "Unknown JS Error"
            context.exception = nil
            throw RuntimeError.jsException(name, msg)
        }
    }
    
    /// Installs the console bridge between JavaScript and Swift.
    /// 
    /// This creates a console object in the JavaScript context that redirects
    /// all console.log, console.error, and console.warn calls to Swift's logging system.
    /// 
    /// The bridge ensures:
    /// - All JS console output appears in Swift logs
    /// - Logs are timestamped and prefixed with "JS:"
    /// - UI updates happen on the main actor
    /// - No JS logs are lost during execution
    /// 
    /// This is the primary debugging bridge for JavaScript code running in PlayRuntimeCore.
    private func setupConsoleBridge(_ context: JSContext) {
        let log: @convention(block) (String) -> Void = { [weak self] msg in
            DispatchQueue.main.async {
                self?.appendLog("JS: \(msg)")
            }
        }
        
        let console = JSValue(newObjectIn: context)
        console?.setObject(log, forKeyedSubscript: "log" as NSString)
        console?.setObject(log, forKeyedSubscript: "error" as NSString)
        console?.setObject(log, forKeyedSubscript: "warn" as NSString)
        context.setObject(console, forKeyedSubscript: "console" as NSString)
    }
    
    private func setupExceptionHandler(_ context: JSContext) {
        context.exceptionHandler = { [weak self] _, exception in
            let msg = exception?.toString() ?? "Unknown exception"
            DispatchQueue.main.async {
                self?.appendLog("EXCEPTION: \(msg)")
                self?.lastError = msg
                self?.status = .failed
            }
        }
    }
    
    private func fail(with message: String) {
        appendLog("FATAL ERROR: \(message)")
        self.lastError = message
        self.status = .failed
    }
    
    private func appendLog(_ line: String) {
        let timestamp = ISO8601DateFormatter().string(from: Date()).suffix(8).prefix(5) // MM:SS
        let formattedLine = "[\(timestamp)] \(line)"
        logs.append(formattedLine)
        print("[PlayRuntime] \(formattedLine)")
        
        // Keep logs manageable but sufficient for debugging
        if logs.count > 500 {
            logs.removeFirst(100)
        }
    }
}

public enum RuntimeError: LocalizedError {
    case missingResource(String)
    case jsException(String, String)
    
    public var errorDescription: String? {
        switch self {
        case .missingResource(let n): return "Missing \(n).js in JSCoreScripts resource bundle."
        case .jsException(let n, let m): return "JavaScript execution error in [\(n).js]: \(m)"
        }
    }
}
