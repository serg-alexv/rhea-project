import Foundation
import JavaScriptCore
import Combine

/// Minimal Swift Host for the Play Runtime.
/// Responsibilities: JSContext lifecycle, console bridge, serial script loading.
/// 
/// [PROTOCOL: MINIMAL_KERNEL_V1]
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
    
    /// Executes the primary bootstrap sequence: runtime.js -> app.js
    /// This effectively reboots the runtime by creating a fresh JSContext.
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
