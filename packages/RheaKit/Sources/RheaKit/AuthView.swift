import SwiftUI
import KeychainAccess

// MARK: - Auth Manager

public class AuthManager: ObservableObject {
    public static let shared = AuthManager()

    @Published public var token: String? = nil
    @Published public var email: String? = nil
    @Published public var plan: String = "free"
    @Published public var queriesUsed: Int = 0
    @Published public var didSkipAuth: Bool = false

    private let keychain = Keychain(service: "com.rhea.preview")

    public var isLoggedIn: Bool { token != nil }

    private init() {
        token = keychain["jwt_token"]
        email = keychain["user_email"]
    }

    public func save(token: String, email: String) {
        self.token = token
        self.email = email
        keychain["jwt_token"] = token
        keychain["user_email"] = email
    }

    public func logout() {
        token = nil
        email = nil
        plan = "free"
        queriesUsed = 0
        didSkipAuth = false
        keychain["jwt_token"] = nil
        keychain["user_email"] = nil
    }

    public func skipLogin() {
        didSkipAuth = true
    }

    /// Attach auth header to a URLRequest
    public func authorize(_ request: inout URLRequest) {
        if let token = token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else {
            // Fallback for local dev — will be rejected in production
            request.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        }
    }
}

// MARK: - Auth View

public struct AuthView: View {
    @ObservedObject private var auth = AuthManager.shared
    @State private var email = ""
    @State private var password = ""
    @State private var isLogin = true
    @State private var loading = false
    @State private var errorMsg: String? = nil
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    public init() {}

    public var body: some View {
        VStack(spacing: 20) {
            Spacer()

            // Logo — nabla (∇) as brand mark
            VStack(spacing: 8) {
                Text("∇")
                    .font(.system(size: 72, weight: .thin, design: .serif))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [RheaTheme.accent, RheaTheme.accent.opacity(0.5)],
                            startPoint: .top, endPoint: .bottom
                        )
                    )
                Text("Rhea")
                    .font(.system(size: 34, weight: .bold, design: .rounded))
                    .foregroundStyle(.white)
                Text("Multi-model consensus engine")
                    .font(.system(size: 14, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            Spacer()

            // Form
            VStack(spacing: 14) {
                TextField("Email", text: $email)
                    #if os(iOS)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                    .textContentType(.emailAddress)
                    #endif
                    .autocorrectionDisabled()
                    .padding(14)
                    .background(RoundedRectangle(cornerRadius: 12).fill(RheaTheme.card))
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(RheaTheme.cardBorder, lineWidth: 1))

                SecureField("Password", text: $password)
                    #if os(iOS)
                    .textContentType(isLogin ? .password : .newPassword)
                    #endif
                    .padding(14)
                    .background(RoundedRectangle(cornerRadius: 12).fill(RheaTheme.card))
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(RheaTheme.cardBorder, lineWidth: 1))

                if let err = errorMsg {
                    Text(err)
                        .font(.caption)
                        .foregroundStyle(RheaTheme.red)
                }

                Button(action: submit) {
                    HStack {
                        if loading {
                            ProgressView().tint(.white)
                        }
                        Text(isLogin ? "Sign In" : "Create Account")
                            .font(.system(size: 16, weight: .bold, design: .monospaced))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                }
                .buttonStyle(.borderedProminent)
                .tint(RheaTheme.accent)
                .disabled(email.isEmpty || password.count < 4 || loading)

                Button(isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in") {
                    isLogin.toggle()
                    errorMsg = nil
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 24)

            Spacer()

            // Skip for now (works offline / local dev only)
            Button("Continue without account") {
                auth.skipLogin()
            }
            .font(.caption)
            .foregroundStyle(.secondary.opacity(0.6))
            .padding(.bottom, 20)
        }
        .foregroundStyle(.white)
        .background(RheaTheme.bg)
    }

    private func submit() {
        let trimEmail = email.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !trimEmail.isEmpty, password.count >= 4 else { return }
        loading = true
        errorMsg = nil

        let endpoint = isLogin ? "login" : "signup"
        guard let url = URL(string: "\(apiBaseURL)/auth/\(endpoint)") else {
            loading = false
            errorMsg = "Invalid API URL"
            return
        }

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: String] = ["email": trimEmail, "password": password]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: req) { data, response, error in
            DispatchQueue.main.async {
                loading = false
                if let error = error {
                    errorMsg = error.localizedDescription
                    return
                }
                guard let data = data,
                      let http = response as? HTTPURLResponse else {
                    errorMsg = "No response"
                    return
                }
                if http.statusCode >= 400 {
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let detail = json["detail"] as? String {
                        errorMsg = detail
                    } else {
                        errorMsg = "Error \(http.statusCode)"
                    }
                    return
                }
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let token = json["token"] as? String {
                    auth.save(token: token, email: trimEmail)
                }
            }
        }.resume()
    }
}

// MARK: - Account Badge (for SettingsView)

public struct AccountBadge: View {
    @ObservedObject private var auth = AuthManager.shared

    public init() {}

    public var body: some View {
        if auth.isLoggedIn {
            HStack(spacing: 8) {
                Image(systemName: "person.crop.circle.fill")
                    .foregroundStyle(RheaTheme.green)
                VStack(alignment: .leading, spacing: 2) {
                    Text(auth.email ?? "")
                        .font(.system(.caption, design: .monospaced))
                        .foregroundStyle(.white)
                    Text(auth.plan.uppercased())
                        .font(.system(.caption2, design: .rounded, weight: .semibold))
                        .foregroundStyle(RheaTheme.accent)
                }
                Spacer()
                Button("Sign Out") {
                    auth.logout()
                }
                .font(.caption2)
                .foregroundStyle(RheaTheme.red)
            }
        } else {
            HStack(spacing: 8) {
                Image(systemName: "person.crop.circle.badge.questionmark")
                    .foregroundStyle(.secondary)
                Text("Not signed in")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
            }
        }
    }
}
