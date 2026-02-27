import SwiftUI

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
    private let apiBase = "http://localhost:8400"

    var body: some View {
        NavigationStack {
            Group {
                if loading {
                    ProgressView("Loading tasks...")
                } else if tasks.isEmpty {
                    ContentUnavailableView("No Tasks", systemImage: "checklist",
                                           description: Text("Task queue empty or API not reachable"))
                } else {
                    List(tasks) { task in
                        TaskRow(task: task)
                    }
                }
            }
            .navigationTitle("Tasks")
            .refreshable { await fetch() }
            .task { await fetch() }
        }
    }

    func fetch() async {
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBase)/tasks") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(TasksResponse.self, from: data)
            tasks = response.tasks
        } catch {
            tasks = []
        }
    }
}

struct TaskRow: View {
    let task: TaskItem

    var statusIcon: String {
        switch task.status {
        case "open": return "circle"
        case "claimed": return "circle.inset.filled"
        case "done": return "checkmark.circle.fill"
        case "blocked": return "xmark.circle.fill"
        default: return "questionmark.circle"
        }
    }

    var statusColor: Color {
        switch task.status {
        case "open": return .secondary
        case "claimed": return .blue
        case "done": return .green
        case "blocked": return .red
        default: return .gray
        }
    }

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: statusIcon)
                .foregroundStyle(statusColor)
            VStack(alignment: .leading, spacing: 2) {
                Text(task.title).font(.subheadline)
                HStack(spacing: 8) {
                    Text(task.priority).font(.caption2.bold())
                        .padding(.horizontal, 6).padding(.vertical, 1)
                        .background(task.priority == "P0" ? Color.red.opacity(0.2) :
                                    task.priority == "P1" ? Color.orange.opacity(0.2) :
                                    Color.gray.opacity(0.15))
                        .clipShape(Capsule())
                    if !task.claimed_by.isEmpty {
                        Text("@\(task.claimed_by)").font(.caption2).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .padding(.vertical, 2)
    }
}
