import Combine
import Foundation
import JavaScriptCore

@MainActor
final class PlayRuntimeLoader: ObservableObject {
    @Published private(set) var loadedScripts: [String] = []
    @Published private(set) var logText = ""
    @Published private(set) var statusText = "Idle"

    var didLoadSuccessfully: Bool {
        statusText == "Loaded"
    }

    private var context: JSContext!
    private let bootstrapOrder = [
        "runtime.js",
        "app.js",
    ]

    init() {
        resetContext()
    }

    func loadBundleScripts() {
        loadedScripts = []
        logText = ""
        statusText = "Loading"
        resetContext()
        context.exception = nil

        do {
            try bootstrapOrder.forEach(loadScript(named:))
            statusText = "Loaded"
        } catch {
            appendLog("Load failed: \(error.localizedDescription)")
            statusText = "Load failed"
        }
    }

    private func loadScript(named scriptName: String) throws {
        guard let scriptURL = Bundle.main.url(
            forResource: scriptName.replacingOccurrences(of: ".js", with: ""),
            withExtension: "js",
            subdirectory: "JSCoreScripts"
        ) else {
            throw RuntimeLoaderError.missingScript(scriptName)
        }

        let source = try String(contentsOf: scriptURL, encoding: .utf8)
        appendLog("Evaluating \(scriptName) from \(scriptURL.path)")
        context.evaluateScript(source, withSourceURL: scriptURL)

        if let exception = context.exception {
            let message = exception.toString() ?? "Unknown JavaScript exception"
            context.exception = nil
            throw RuntimeLoaderError.scriptException(scriptName, message)
        }

        loadedScripts.append(scriptName)
    }

    private func installConsoleBridge() {
        let logBlock: @convention(block) (String) -> Void = { [weak self] message in
            self?.appendLog("console.log: \(message)")
        }

        let errorBlock: @convention(block) (String) -> Void = { [weak self] message in
            self?.appendLog("console.error: \(message)")
        }

        let console = JSValue(newObjectIn: context)
        console?.setObject(logBlock, forKeyedSubscript: "log" as NSString)
        console?.setObject(errorBlock, forKeyedSubscript: "error" as NSString)
        context.setObject(console, forKeyedSubscript: "console" as NSString)
    }

    private func resetContext() {
        context = JSContext()
        installConsoleBridge()
        context.exceptionHandler = { [weak self] _, exception in
            let message = exception?.toString() ?? "Unknown JavaScript exception"
            self?.appendLog("JS exception: \(message)")
            self?.statusText = "JavaScript exception"
        }
    }

    private func appendLog(_ line: String) {
        if logText.isEmpty {
            logText = line
        } else {
            logText += "\n\(line)"
        }
        print(line)
    }
}

private enum RuntimeLoaderError: LocalizedError {
    case missingScript(String)
    case scriptException(String, String)

    var errorDescription: String? {
        switch self {
        case let .missingScript(name):
            return "Missing bundled script: \(name)"
        case let .scriptException(name, message):
            return "\(name) failed with: \(message)"
        }
    }
}
