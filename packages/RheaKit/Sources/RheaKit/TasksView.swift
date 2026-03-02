import SwiftUI
import Pow

public struct TaskItem: Codable, Identifiable {
    public let id: String
    public let title: String
    public let priority: String
    public let status: String
    public let agent: String
    public let claimed_by: String
    public let tags: [String]

    public init(id: String, title: String, priority: String, status: String, agent: String, claimed_by: String, tags: [String]) {
        self.id = id
        self.title = title
        self.priority = priority
        self.status = status
        self.agent = agent
        self.claimed_by = claimed_by
        self.tags = tags
    }
}

public struct TasksResponse: Codable {
    public let tasks: [TaskItem]

    public init(tasks: [TaskItem]) {
        self.tasks = tasks
    }
}

public struct TasksView: View {
    @State private var tasks: [TaskItem] = []
    @State private var loading = true
    @State private var filter: String = "all"
    @State private var agentFilter: String? = nil
    @State private var priorityFilter: String? = nil
    @State private var lensMode: Bool = false
    @State private var pollTimer: Timer? = nil
    @State private var showNewTask = false
    @State private var newTitle = ""
    @State private var newPriority = "P1"
    @State private var newAgent = ""
    @State private var isCreating = false
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    /// Unique agents found in tasks
    private var agents: [String] {
        Array(Set(tasks.compactMap { $0.claimed_by.isEmpty ? nil : $0.claimed_by })).sorted()
    }

    /// Unique priorities
    private var priorities: [String] {
        Array(Set(tasks.map { $0.priority })).sorted()
    }

    /// Does a task pass all active filters?
    func taskMatchesLens(_ task: TaskItem) -> Bool {
        if filter != "all" && task.status != filter { return false }
        if let agent = agentFilter, task.claimed_by != agent { return false }
        if let prio = priorityFilter, task.priority != prio { return false }
        return true
    }

    /// Any filter active beyond "all"?
    var hasActiveLens: Bool {
        filter != "all" || agentFilter != nil || priorityFilter != nil
    }

    /// In lens mode: show all, dim non-matching. Otherwise: filter out.
    public var filteredTasks: [TaskItem] {
        if lensMode { return tasks }
        return tasks.filter { taskMatchesLens($0) }
    }

    public init() {}

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // MARK: - Cognitive Lens Filters
                VStack(spacing: 6) {
                    // Row 1: Status + lens toggle
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            // Lens mode toggle
                            Button {
                                withAnimation(.spring(duration: 0.3)) { lensMode.toggle() }
                            } label: {
                                Image(systemName: lensMode ? "eye.circle.fill" : "eye.circle")
                                    .font(.system(size: 16))
                                    .foregroundStyle(lensMode ? RheaTheme.amber : .secondary)
                            }
                            .buttonStyle(.plain)
                            .help("Lens mode: dim instead of hide")

                            FilterChip(label: "All", count: tasks.count, isActive: filter == "all") {
                                filter = "all"; agentFilter = nil; priorityFilter = nil
                            }
                            FilterChip(label: "Open", count: tasks.filter { $0.status == "open" }.count,
                                       isActive: filter == "open", color: .secondary) { filter = "open" }
                            FilterChip(label: "Claimed", count: tasks.filter { $0.status == "claimed" }.count,
                                       isActive: filter == "claimed", color: RheaTheme.accent) { filter = "claimed" }
                            FilterChip(label: "Done", count: tasks.filter { $0.status == "done" }.count,
                                       isActive: filter == "done", color: RheaTheme.green) { filter = "done" }
                            FilterChip(label: "Blocked", count: tasks.filter { $0.status == "blocked" }.count,
                                       isActive: filter == "blocked", color: RheaTheme.red) { filter = "blocked" }
                        }
                        .padding(.horizontal)
                    }

                    // Row 2: Agent + Priority chips (only show when tasks loaded)
                    if !tasks.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 6) {
                                // Agent chips
                                ForEach(agents, id: \.self) { agent in
                                    FilterChip(
                                        label: agent,
                                        count: tasks.filter { $0.claimed_by == agent }.count,
                                        isActive: agentFilter == agent,
                                        color: RheaTheme.accent
                                    ) {
                                        agentFilter = agentFilter == agent ? nil : agent
                                    }
                                }
                                if !agents.isEmpty && !priorities.isEmpty {
                                    Divider().frame(height: 16)
                                }
                                // Priority chips
                                ForEach(priorities, id: \.self) { prio in
                                    FilterChip(
                                        label: prio,
                                        count: tasks.filter { $0.priority == prio }.count,
                                        isActive: priorityFilter == prio,
                                        color: RheaTheme.priorityColor(prio)
                                    ) {
                                        priorityFilter = priorityFilter == prio ? nil : prio
                                    }
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                }
                .padding(.vertical, 8)
                .background(RheaTheme.bg)

                if loading {
                    Spacer()
                    ProgressView()
                    Spacer()
                } else if filteredTasks.isEmpty {
                    Spacer()
                    ContentUnavailableView("No Tasks", systemImage: "checklist",
                                           description: Text(tasks.isEmpty ? "Queue empty or API offline" : "No \(filter) tasks"))
                    Spacer()
                } else {
                    ScrollView {
                        LazyVStack(spacing: 10) {
                            ForEach(filteredTasks) { task in
                                let matches = taskMatchesLens(task)
                                TaskCard(task: task)
                                    .opacity(lensMode && !matches ? 0.2 : 1.0)
                                    .scaleEffect(lensMode && !matches ? 0.97 : 1.0)
                                    .blur(radius: lensMode && !matches ? 1.5 : 0)
                                    .animation(.easeInOut(duration: 0.25), value: matches)
                            }
                        }
                        .padding(.horizontal)
                        .padding(.top, 8)
                        .padding(.bottom, 20)
                    }
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("Tasks")
            #if os(iOS)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button { showNewTask = true } label: {
                        Image(systemName: "plus.circle.fill")
                            .foregroundColor(RheaTheme.accent)
                    }
                }
            }
            .sheet(isPresented: $showNewTask) {
                newTaskSheet
            }
            .refreshable { await fetch() }
            .task {
                await fetch()
                startPolling()
            }
            .onDisappear {
                pollTimer?.invalidate()
                pollTimer = nil
            }
        }
    }

    // MARK: - New Task Sheet

    var newTaskSheet: some View {
        NavigationStack {
            Form {
                Section("Task") {
                    TextField("Title", text: $newTitle)
                    Picker("Priority", selection: $newPriority) {
                        Text("P0").tag("P0")
                        Text("P1").tag("P1")
                        Text("P2").tag("P2")
                        Text("P3").tag("P3")
                    }
                    .pickerStyle(.segmented)
                    TextField("Assign to agent (optional)", text: $newAgent)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        #endif
                        .autocorrectionDisabled()
                }
            }
            .navigationTitle("New Task")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showNewTask = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        Task { await createTask() }
                    }
                    .disabled(newTitle.trimmingCharacters(in: .whitespaces).isEmpty || isCreating)
                }
            }
        }
        .presentationDetents([.medium])
    }

    func createTask() async {
        let title = newTitle.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !title.isEmpty else { return }
        isCreating = true
        defer { isCreating = false }
        var comps = URLComponents(string: "\(apiBaseURL)/tasks")
        comps?.queryItems = [
            URLQueryItem(name: "title", value: title),
            URLQueryItem(name: "priority", value: newPriority),
        ]
        if !newAgent.isEmpty {
            comps?.queryItems?.append(URLQueryItem(name: "agent", value: newAgent))
        }
        guard let url = comps?.url else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        do {
            let (_, response) = try await URLSession.shared.data(for: req)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                showNewTask = false
                newTitle = ""
                newAgent = ""
                await fetch()
            }
        } catch {}
    }

    func startPolling() {
        pollTimer = Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { _ in
            Task { await fetch() }
        }
    }

    func fetch() async {
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBaseURL)/tasks") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(TasksResponse.self, from: data)
            withAnimation(.spring(duration: 0.3)) {
                tasks = response.tasks
            }
        } catch {
            tasks = []
        }
    }
}

// MARK: - FilterChip
public struct FilterChip: View {
    public let label: String
    public let count: Int
    public let isActive: Bool
    public var color: Color = RheaTheme.accent
    public let action: () -> Void

    public init(label: String, count: Int, isActive: Bool, color: Color = RheaTheme.accent, action: @escaping () -> Void) {
        self.label = label
        self.count = count
        self.isActive = isActive
        self.color = color
        self.action = action
    }

    public var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Text(label)
                if count > 0 {
                    Text("\(count)")
                        .font(.system(.caption2, design: .rounded, weight: .bold))
                        .padding(.horizontal, 5)
                        .padding(.vertical, 1)
                        .background(
                            Capsule().fill(isActive ? .white.opacity(0.2) : .clear)
                        )
                }
            }
            .font(.system(.caption, design: .rounded, weight: isActive ? .bold : .medium))
            .foregroundStyle(isActive ? .white : .secondary)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                Capsule().fill(isActive ? color.opacity(0.3) : .white.opacity(0.05))
            )
            .overlay(
                Capsule().stroke(isActive ? color.opacity(0.5) : .clear, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - TaskCard
public struct TaskCard: View {
    public let task: TaskItem
    @State private var appeared = false

    public init(task: TaskItem) {
        self.task = task
    }

    public var statusIcon: String {
        switch task.status {
        case "open": return "circle"
        case "claimed": return "circle.inset.filled"
        case "done": return "checkmark.circle.fill"
        case "blocked": return "xmark.octagon.fill"
        default: return "questionmark.circle"
        }
    }

    public var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Status icon with priority ring
            ZStack {
                Circle()
                    .stroke(RheaTheme.priorityColor(task.priority).opacity(0.3), lineWidth: 2)
                    .frame(width: 32, height: 32)
                Image(systemName: statusIcon)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(RheaTheme.statusColor(task.status))
            }
            .changeEffect(.rise(origin: UnitPoint(x: 0.5, y: 0.0)) {
                Image(systemName: "checkmark")
                    .font(.caption2.bold())
                    .foregroundStyle(RheaTheme.green)
            }, value: task.status, isEnabled: task.status == "done")

            VStack(alignment: .leading, spacing: 6) {
                Text(task.title)
                    .font(.system(.subheadline, weight: .medium))
                    .foregroundStyle(.white)
                    .lineLimit(2)

                HStack(spacing: 8) {
                    // Priority badge
                    Text(task.priority)
                        .font(.system(.caption2, design: .rounded, weight: .bold))
                        .foregroundStyle(RheaTheme.priorityColor(task.priority))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(
                            RoundedRectangle(cornerRadius: 4)
                                .fill(RheaTheme.priorityColor(task.priority).opacity(0.15))
                        )

                    // Agent badge
                    if !task.claimed_by.isEmpty {
                        HStack(spacing: 3) {
                            Image(systemName: "person.fill")
                                .font(.system(size: 8))
                            Text(task.claimed_by)
                        }
                        .font(.caption2)
                        .foregroundStyle(RheaTheme.accent)
                    }

                    // Tags
                    ForEach(task.tags.prefix(2), id: \.self) { tag in
                        Text(tag)
                            .font(.system(.caption2, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Spacer()
        }
        .glassCard()
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 12)
        .onAppear {
            withAnimation(.spring(duration: 0.4, bounce: 0.2).delay(Double.random(in: 0...0.15))) {
                appeared = true
            }
        }
    }
}
