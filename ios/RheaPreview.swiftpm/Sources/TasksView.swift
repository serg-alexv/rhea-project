import SwiftUI
import Pow

struct TaskItem: Codable, Identifiable {
    let id: String
    let title: String
    let priority: String
    let status: String
    let agent: String
    let claimed_by: String
    let tags: [String]
}

struct TasksResponse: Codable {
    let tasks: [TaskItem]
}

struct TasksView: View {
    @State private var tasks: [TaskItem] = []
    @State private var loading = true
    @State private var filter: String = "all"
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var filteredTasks: [TaskItem] {
        guard filter != "all" else { return tasks }
        return tasks.filter { $0.status == filter }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Filter chips
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        FilterChip(label: "All", count: tasks.count, isActive: filter == "all") { filter = "all" }
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
                    .padding(.vertical, 10)
                }
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
                                TaskCard(task: task)
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
            .refreshable { await fetch() }
            .task { await fetch() }
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
struct FilterChip: View {
    let label: String
    let count: Int
    let isActive: Bool
    var color: Color = RheaTheme.accent
    let action: () -> Void

    var body: some View {
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
struct TaskCard: View {
    let task: TaskItem
    @State private var appeared = false

    var statusIcon: String {
        switch task.status {
        case "open": return "circle"
        case "claimed": return "circle.inset.filled"
        case "done": return "checkmark.circle.fill"
        case "blocked": return "xmark.octagon.fill"
        default: return "questionmark.circle"
        }
    }

    var body: some View {
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
