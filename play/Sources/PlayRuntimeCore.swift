import Foundation
import JavaScriptCore
import Combine

/// Minimal Swift Host for the Play Runtime.
/// Responsibilities: JSContext lifecycle, console bridge, serial script loading.
@MainActor
final class PlayRuntimeCore: ObservableObject {
    @Published private(set) var status: RuntimeStatus = .idle
    @Published private(set) var logs: [String] = []
    
    private let context: JSContext
    private let bootstrapSequence = ["runtime", "app"]
    
    enum RuntimeStatus: String {
        case idle, booting, running, failed
    }
    
    init() {
        self.context = JSContext()
        setupConsoleBridge()
        setupExceptionHandler()
    }
    
    /// Executes the primary bootstrap sequence: runtime.js -> app.js
    func boot() {
        status = .booting
        logs.removeAll()
        
        for scriptName in bootstrapSequence {
            do {
                try loadBundledScript(named: scriptName)
            } catch {
                appendLog("FATAL: \(error.localizedDescription)")
                status = .failed
                return
            }
        }
        
        status = .running
    }
    
    private func loadBundledScript(named name: String) throws {
        guard let url = Bundle.main.url(forResource: name, withExtension: "js", subdirectory: "JSCoreScripts") else {
            throw RuntimeError.missingResource(name)
        }
        
        let source = try String(contentsOf: url, encoding: .utf8)
        appendLog("Loading \(name).js...")
        context.evaluateScript(source, withSourceURL: url)
        
        if let exception = context.exception {
            let msg = exception.toString() ?? "Unknown JS Error"
            context.exception = nil
            throw RuntimeError.jsException(name, msg)
        }
    }
    
    private func setupConsoleBridge() {
        let log: @convention(block) (String) -> Void = { [weak self] msg in
            self?.appendLog("JS: \(msg)")
        }
        
        let console = JSValue(newObjectIn: context)
        console?.setObject(log, forKeyedSubscript: "log" as NSString)
        console?.setObject(log, forKeyedSubscript: "error" as NSString)
        context.setObject(console, forKeyedSubscript: "console" as NSString)
    }
    
    private func setupExceptionHandler() {
        context.exceptionHandler = { [weak self] _, exception in
            let msg = exception?.toString() ?? "Unknown exception"
            self?.appendLog("CRITICAL: \(msg)")
            self?.status = .failed
        }
    }
    
    private func appendLog(_ line: String) {
        logs.append(line)
        print(line)
    }
}

enum RuntimeError: LocalizedError {
    case missingResource(String)
    case jsException(String, String)
    
    var errorDescription: String? {
        switch self {
        case .missingResource(let n): return "Missing \(n).js in JSCoreScripts"
        case .jsException(let n, let m): return "Error in \(n).js: \(m)"
        }
    }
}
