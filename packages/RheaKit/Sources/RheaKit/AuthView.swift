import SwiftUI
import KeychainAccess
import AuthenticationServices

// MARK: - Auth Manager

public class AuthManager: ObservableObject {
    public static let shared = AuthManager()

    @Published public var token: String? = nil
    @Published public var email: String? = nil
    @Published public var plan: String = "free"
    @Published public var queriesUsed: Int = 0
    @Published public var queryLimit: Int = 100
    @Published public var didSkipAuth: Bool = UserDefaults.standard.bool(forKey: "didSkipAuth")

    private let keychain = Keychain(service: "com.rhea.preview")

    public var isLoggedIn: Bool { token != nil }

    private init() {
        token = keychain["jwt_token"]
        email = keychain["user_email"]
        if token != nil { fetchProfile() }
    }

    public func save(token: String, email: String) {
        self.token = token
        self.email = email
        keychain["jwt_token"] = token
        keychain["user_email"] = email
        fetchProfile()
    }

    public func logout() {
        token = nil
        email = nil
        plan = "free"
        queriesUsed = 0
        queryLimit = 100
        didSkipAuth = false
        UserDefaults.standard.set(false, forKey: "didSkipAuth")
        keychain["jwt_token"] = nil
        keychain["user_email"] = nil
    }

    public func skipLogin() {
        didSkipAuth = true
        UserDefaults.standard.set(true, forKey: "didSkipAuth")
    }

    /// Attach auth header to a URLRequest
    public func authorize(_ request: inout URLRequest) {
        if let token = token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else {
            request.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        }
    }

    /// Fetch profile from backend to sync plan + usage
    public func fetchProfile() {
        guard let token = token else { return }
        let base = UserDefaults.standard.string(forKey: "apiBaseURL") ?? AppConfig.defaultAPIBaseURL
        guard let url = URL(string: "\(base)/auth/profile") else { return }
        var req = URLRequest(url: url)
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        URLSession.shared.dataTask(with: req) { [weak self] data, response, _ in
            guard let data = data,
                  let http = response as? HTTPURLResponse, http.statusCode == 200,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
            DispatchQueue.main.async {
                if let plan = json["plan"] as? String { self?.plan = plan }
                if let usage = json["usage"] as? [String: Any] {
                    self?.queriesUsed = usage["queries"] as? Int ?? 0
                    self?.queryLimit = usage["limit"] as? Int ?? 100
                }
            }
        }.resume()
    }

    /// Handle OAuth callback URL (rhea://oauth?token=...&email=...)
    public func handleOAuthURL(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let items = components.queryItems else { return }
        let params = Dictionary(uniqueKeysWithValues: items.compactMap { item in
            item.value.map { (item.name, $0) }
        })
        if let token = params["token"], !token.isEmpty,
           let email = params["email"] {
            save(token: token, email: email)
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

            // OAuth buttons
            VStack(spacing: 12) {
                AppleSignInButton(apiBaseURL: apiBaseURL)
                OAuthButton(provider: "Google", icon: "globe", color: .white, apiBaseURL: apiBaseURL)
                OAuthButton(provider: "Microsoft", icon: "building.2", color: Color(red: 0, green: 0.47, blue: 0.84), apiBaseURL: apiBaseURL)
            }
            .padding(.horizontal, 24)

            // Divider
            HStack {
                Rectangle().fill(RheaTheme.cardBorder).frame(height: 1)
                Text("or email").font(.caption2).foregroundStyle(.secondary)
                Rectangle().fill(RheaTheme.cardBorder).frame(height: 1)
            }
            .padding(.horizontal, 24)

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

// MARK: - Apple Sign In

struct AppleSignInButton: View {
    let apiBaseURL: String
    @ObservedObject private var auth = AuthManager.shared

    var body: some View {
        SignInWithAppleButton(.signIn) { request in
            request.requestedScopes = [.email, .fullName]
        } onCompletion: { result in
            switch result {
            case .success(let authorization):
                handleAppleAuth(authorization)
            case .failure:
                break
            }
        }
        .signInWithAppleButtonStyle(.white)
        .frame(maxWidth: .infinity)
        .frame(height: 50)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func handleAppleAuth(_ authorization: ASAuthorization) {
        guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
              let identityTokenData = credential.identityToken,
              let identityToken = String(data: identityTokenData, encoding: .utf8) else { return }

        // Send Apple identity token to our backend for verification
        guard let url = URL(string: "\(apiBaseURL)/auth/apple/native") else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "identity_token": identityToken,
            "email": credential.email ?? "",
            "full_name": [credential.fullName?.givenName, credential.fullName?.familyName]
                .compactMap { $0 }.joined(separator: " "),
        ]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: req) { data, response, _ in
            guard let data = data,
                  let http = response as? HTTPURLResponse, http.statusCode < 300,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let token = json["token"] as? String,
                  let email = json["email"] as? String else { return }
            DispatchQueue.main.async {
                auth.save(token: token, email: email)
            }
        }.resume()
    }
}

// MARK: - OAuth Button

struct OAuthButton: View {
    let provider: String
    let icon: String
    let color: Color
    let apiBaseURL: String

    @ObservedObject private var auth = AuthManager.shared
    @State private var loading = false

    var body: some View {
        Button(action: startOAuth) {
            HStack(spacing: 10) {
                if loading {
                    ProgressView().tint(.white).controlSize(.small)
                } else {
                    Image(systemName: icon)
                }
                Text("Continue with \(provider)")
                    .font(.system(size: 15, weight: .semibold))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 13)
            .foregroundStyle(provider == "Google" ? .black : .white)
            .background(RoundedRectangle(cornerRadius: 12).fill(color))
        }
        .disabled(loading)
    }

    private func startOAuth() {
        loading = true
        let providerPath = provider.lowercased()
        guard let authURL = URL(string: "\(apiBaseURL)/auth/\(providerPath)?callback=rhea://oauth") else {
            loading = false
            return
        }
        let session = ASWebAuthenticationSession(
            url: authURL,
            callbackURLScheme: "rhea"
        ) { callbackURL, error in
            DispatchQueue.main.async {
                loading = false
                if let url = callbackURL {
                    auth.handleOAuthURL(url)
                }
            }
        }
        #if os(iOS)
        session.presentationContextProvider = OAuthPresentationContext.shared
        session.prefersEphemeralWebBrowserSession = false
        #endif
        session.start()
    }
}

#if os(iOS)
private class OAuthPresentationContext: NSObject, ASWebAuthenticationPresentationContextProviding {
    static let shared = OAuthPresentationContext()
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        let scenes = UIApplication.shared.connectedScenes
        let windowScene = scenes.first as? UIWindowScene
        return windowScene?.windows.first ?? ASPresentationAnchor()
    }
}
#endif

// MARK: - Billing View

public struct BillingView: View {
    @ObservedObject private var auth = AuthManager.shared
    @State private var keys: [[String: Any]] = []

    public init() {}

    public var body: some View {
        List {
            // Current plan
            Section("Current Plan") {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(auth.plan.uppercased())
                            .font(.system(.title2, design: .rounded, weight: .bold))
                            .foregroundStyle(planColor)
                        Text(planDescription)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if auth.plan == "free" {
                        Text("Free tier")
                            .font(.caption2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(RheaTheme.card)
                            .clipShape(Capsule())
                    }
                }
            }

            // Usage
            Section("Usage This Month") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("\(auth.queriesUsed)")
                            .font(.system(.title, design: .monospaced, weight: .bold))
                        Text("/ \(auth.queryLimit == -1 ? "∞" : "\(auth.queryLimit)")")
                            .font(.system(.body, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text("queries")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    if auth.queryLimit > 0 {
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(RheaTheme.card)
                                    .frame(height: 6)
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(usageColor)
                                    .frame(width: geo.size.width * usageRatio, height: 6)
                            }
                        }
                        .frame(height: 6)
                    }
                }
            }

            // API Keys
            Section("API Keys") {
                if auth.plan == "free" {
                    Text("Upgrade to Pro for API key access")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(keys.indices, id: \.self) { i in
                        let key = keys[i]
                        HStack {
                            VStack(alignment: .leading) {
                                Text(key["key"] as? String ?? "")
                                    .font(.system(.caption, design: .monospaced))
                                Text(key["label"] as? String ?? "")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            if key["active"] as? Bool == true {
                                Circle().fill(RheaTheme.green).frame(width: 8, height: 8)
                            } else {
                                Circle().fill(RheaTheme.red).frame(width: 8, height: 8)
                            }
                        }
                    }
                    if keys.isEmpty {
                        Text("No API keys yet")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            // Plans comparison
            Section("Available Plans") {
                PlanRow(name: "Free", price: "$0", features: "100 queries/mo · 1 model")
                PlanRow(name: "Pro", price: "$29/mo", features: "10K queries/mo · 5 models · 3 API keys")
                PlanRow(name: "Enterprise", price: "$99/mo", features: "Unlimited · All models · 10 keys · Reseller")
            }
        }
        .scrollContentBackground(.hidden)
        .background(RheaTheme.bg)
        .navigationTitle("Billing")
        .task { await loadBillingData() }
        .refreshable { await loadBillingData() }
    }

    private var planColor: Color {
        switch auth.plan {
        case "pro": return .purple
        case "enterprise": return .orange
        default: return RheaTheme.accent
        }
    }

    private var planDescription: String {
        switch auth.plan {
        case "pro": return "Multi-model consensus · API access"
        case "enterprise": return "Unlimited · White-label · Reseller"
        default: return "100 queries/month · Single model"
        }
    }

    private var usageRatio: CGFloat {
        guard auth.queryLimit > 0 else { return 0 }
        return min(1.0, CGFloat(auth.queriesUsed) / CGFloat(auth.queryLimit))
    }

    private var usageColor: Color {
        if usageRatio > 0.9 { return RheaTheme.red }
        if usageRatio > 0.7 { return .orange }
        return RheaTheme.green
    }

    private func loadBillingData() async {
        auth.fetchProfile()
        do {
            let keysData = try await RheaAPI.shared.get("/billing/keys", auth: true)
            if let json = try? JSONSerialization.jsonObject(with: keysData) as? [String: Any],
               let k = json["keys"] as? [[String: Any]] {
                await MainActor.run { keys = k }
            }
        } catch {}
    }
}

struct PlanRow: View {
    let name: String
    let price: String
    let features: String

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(name)
                    .font(.system(.body, design: .rounded, weight: .semibold))
                Text(features)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(price)
                .font(.system(.caption, design: .monospaced, weight: .bold))
                .foregroundStyle(RheaTheme.accent)
        }
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
