# Play to Xcode: Detailed Code Examples

## Complete Integration Pattern for Existing SwiftUI App

### Setup: Add Play Package to Project

```swift
// 1. In Xcode: File → Add Packages
// 2. Navigate to exported Play package folder
// 3. Add to your target

import SwiftUI
import PlayComponents  // Your module name
```

### Pattern 1: Simple Component with No Data

```swift
import SwiftUI
import PlayComponents

struct SimpleView: View {
    var body: some View {
        VStack {
            // Just display the component as-is
            CardMedium()
                .padding()
        }
    }
}
```

### Pattern 2: Dynamic Text & Image Updates

```swift
import SwiftUI
import PlayComponents

struct DynamicDataView: View {
    @State private var articleTitle = "Default Article"
    @State private var articleImage = UIImage(named: "placeholder")
    
    var body: some View {
        VStack(spacing: 16) {
            // Display component with dynamic data
            CardMedium()
                .setText(.title, articleTitle)
                .setImage(.imageOne, articleImage ?? UIImage())
            
            // Controls to change data
            VStack(spacing: 8) {
                TextField("Article Title", text: $articleTitle)
                    .textFieldStyle(.roundedBorder)
                    .padding()
                
                Button("Load New Image") {
                    articleImage = UIImage(named: "nature")
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding()
    }
}

// Preview
#Preview {
    DynamicDataView()
}
```

### Pattern 3: State Management & Animation

```swift
import SwiftUI
import PlayComponents

struct StateManagementView: View {
    @State private var cardState: CardMedium.State? = .default
    @State private var isExpanded = false
    
    var body: some View {
        VStack(spacing: 20) {
            // Card with state binding
            CardMedium()
                .state($cardState)
            
            // Toggle button
            Button(action: toggleState) {
                Label(
                    isExpanded ? "Collapse" : "Expand",
                    systemImage: isExpanded ? "chevron.up" : "chevron.down"
                )
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
    
    private func toggleState() {
        withAnimation(.easeInOut(duration: 0.3)) {
            if cardState == .default {
                cardState = .expanded
                isExpanded = true
            } else {
                cardState = .default
                isExpanded = false
            }
        }
    }
}

#Preview {
    StateManagementView()
}
```

### Pattern 4: Component Variables

```swift
import SwiftUI
import PlayComponents

struct VariablesView: View {
    @State private var isFavorited = false
    @State private var accentColor = Color.blue
    @State private var rating = 0
    
    var body: some View {
        VStack(spacing: 20) {
            // Pass variables to component
            CardMedium(
                isFavorite: isFavorited,
                accentColor: accentColor
            )
            
            VStack(spacing: 12) {
                // Toggle favorite
                Toggle("Favorite", isOn: $isFavorited)
                
                // Change accent color
                Picker("Accent Color", selection: $accentColor) {
                    Text("Blue").tag(Color.blue)
                    Text("Red").tag(Color.red)
                    Text("Green").tag(Color.green)
                }
                
                // Rating slider
                Slider(value: Binding(
                    get: { Double(rating) },
                    set: { rating = Int($0) }
                ), in: 0...5)
            }
            .padding()
        }
        .padding()
    }
}

#Preview {
    VariablesView()
}
```

### Pattern 5: API/Network Data Integration

```swift
import SwiftUI
import PlayComponents

// Model
struct Article: Decodable, Identifiable {
    let id: UUID
    let title: String
    let description: String
    let imageURL: String
    let author: String
}

// View Model
@MainActor
class ArticleViewModel: ObservableObject {
    @Published var articles: [Article] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    func fetchArticles() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            let url = URL(string: "https://api.example.com/articles")!
            let (data, _) = try await URLSession.shared.data(from: url)
            articles = try JSONDecoder().decode([Article].self, from: data)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// View
struct ArticleListView: View {
    @StateObject private var viewModel = ArticleViewModel()
    
    var body: some View {
        VStack {
            if viewModel.isLoading {
                ProgressView()
            } else if let error = viewModel.errorMessage {
                Text("Error: \(error)")
                    .foregroundColor(.red)
            } else {
                List(viewModel.articles) { article in
                    ArticleRowView(article: article)
                }
            }
        }
        .onAppear {
            Task {
                await viewModel.fetchArticles()
            }
        }
    }
}

struct ArticleRowView: View {
    let article: Article
    @State private var image: UIImage?
    
    var body: some View {
        CardMedium()
            .setText(.title, article.title)
            .setText(.subtitle, article.author)
            .setText(.description, article.description)
            .setImage(.imageOne, image ?? UIImage())
            .onAppear {
                loadImage()
            }
    }
    
    private func loadImage() {
        Task {
            if let url = URL(string: article.imageURL) {
                let (data, _) = try await URLSession.shared.data(from: url)
                image = UIImage(data: data)
            }
        }
    }
}

#Preview {
    ArticleListView()
}
```

### Pattern 6: Form with Play Components

```swift
import SwiftUI
import PlayComponents

struct FormView: View {
    @State private var name = ""
    @State private var email = ""
    @State private var selectedCategory = "General"
    @State private var message = ""
    @State private var isSubmitting = false
    @State private var submitSuccess = false
    
    let categories = ["General", "Support", "Feedback", "Other"]
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header card
                CardMedium()
                    .setText(.title, "Contact Us")
                    .padding()
                
                Form {
                    Section("Personal Info") {
                        TextField("Name", text: $name)
                        TextField("Email", text: $email)
                            .keyboardType(.emailAddress)
                    }
                    
                    Section("Details") {
                        Picker("Category", selection: $selectedCategory) {
                            ForEach(categories, id: \.self) { category in
                                Text(category).tag(category)
                            }
                        }
                        
                        TextEditor(text: $message)
                            .frame(height: 100)
                    }
                }
                
                Button(action: submit) {
                    if isSubmitting {
                        ProgressView()
                    } else {
                        Text("Submit")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(isSubmitting || name.isEmpty || email.isEmpty)
                
                if submitSuccess {
                    Text("Message sent successfully!")
                        .foregroundColor(.green)
                }
            }
            .padding()
        }
    }
    
    private func submit() {
        isSubmitting = true
        // Send form data to your backend
        Task {
            // Simulate API call
            try await Task.sleep(nanoseconds: 2_000_000_000)
            isSubmitting = false
            submitSuccess = true
        }
    }
}

#Preview {
    FormView()
}
```

### Pattern 7: List with Play Components

```swift
import SwiftUI
import PlayComponents

struct Product: Identifiable {
    let id: UUID
    let name: String
    let price: Double
    let imageName: String
    let isFavorite: Bool
}

struct ProductListView: View {
    @State private var products = [
        Product(id: UUID(), name: "Product 1", price: 29.99, imageName: "product1", isFavorite: false),
        Product(id: UUID(), name: "Product 2", price: 39.99, imageName: "product2", isFavorite: true),
        Product(id: UUID(), name: "Product 3", price: 49.99, imageName: "product3", isFavorite: false),
    ]
    
    var body: some View {
        List {
            ForEach(products) { product in
                ProductCardView(product: product)
                    .listRowSeparator(.hidden)
                    .listRowInsets(EdgeInsets())
            }
        }
        .listStyle(.plain)
    }
}

struct ProductCardView: View {
    let product: Product
    @State private var isFavorite: Bool
    
    init(product: Product) {
        self.product = product
        _isFavorite = State(initialValue: product.isFavorite)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            CardMedium(isFavorite: isFavorite)
                .setText(.title, product.name)
                .setText(.price, String(format: "$%.2f", product.price))
                .setImage(.imageOne, UIImage(named: product.imageName) ?? UIImage())
            
            HStack {
                Button(action: toggleFavorite) {
                    Label(isFavorite ? "Favorited" : "Favorite", 
                          systemImage: isFavorite ? "heart.fill" : "heart")
                }
                .buttonStyle(.bordered)
                
                Spacer()
                
                Button("Add to Cart") {
                    // Add to cart action
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    private func toggleFavorite() {
        withAnimation {
            isFavorite.toggle()
        }
    }
}

#Preview {
    ProductListView()
}
```

### Pattern 8: Tab Navigation with Play Components

```swift
import SwiftUI
import PlayComponents

struct TabbedAppView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            // Home Tab
            HomeTab()
                .tabItem {
                    Label("Home", systemImage: "house.fill")
                }
                .tag(0)
            
            // Explore Tab
            ExploreTab()
                .tabItem {
                    Label("Explore", systemImage: "magnifyingglass")
                }
                .tag(1)
            
            // Profile Tab
            ProfileTab()
                .tabItem {
                    Label("Profile", systemImage: "person.fill")
                }
                .tag(2)
        }
    }
}

struct HomeTab: View {
    var body: some View {
        NavigationStack {
            VStack {
                CardMedium()
                    .setText(.title, "Welcome Home")
                    .padding()
                
                List {
                    ForEach(0..<5) { index in
                        CardMedium()
                            .setText(.title, "Item \(index + 1)")
                    }
                }
            }
            .navigationTitle("Home")
        }
    }
}

struct ExploreTab: View {
    var body: some View {
        NavigationStack {
            VStack {
                CardMedium()
                    .setText(.title, "Explore New Content")
                    .padding()
                
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(0..<10) { index in
                            CardMedium()
                                .setText(.title, "Discovery \(index + 1)")
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("Explore")
        }
    }
}

struct ProfileTab: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                CardMedium()
                    .setText(.title, "Your Profile")
                    .padding()
                
                VStack(alignment: .leading, spacing: 12) {
                    ProfileRow(label: "Name", value: "John Doe")
                    ProfileRow(label: "Email", value: "john@example.com")
                    ProfileRow(label: "Location", value: "San Francisco, CA")
                }
                .padding()
                
                Spacer()
                
                Button("Sign Out", action: {})
                    .buttonStyle(.bordered)
            }
            .navigationTitle("Profile")
        }
    }
}

struct ProfileRow: View {
    let label: String
    let value: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption)
                .foregroundColor(.gray)
            Text(value)
                .font(.body)
        }
    }
}

#Preview {
    TabbedAppView()
}
```

### Pattern 9: Sheet/Modal with Play Components

```swift
import SwiftUI
import PlayComponents

struct ModalViewExample: View {
    @State private var showDetailSheet = false
    @State private var selectedItem: String?
    
    var body: some View {
        NavigationStack {
            VStack {
                List {
                    ForEach(["Item 1", "Item 2", "Item 3"], id: \.self) { item in
                        Button(action: { 
                            selectedItem = item
                            showDetailSheet = true 
                        }) {
                            CardMedium()
                                .setText(.title, item)
                        }
                    }
                }
            }
            .navigationTitle("Items")
            .sheet(isPresented: $showDetailSheet) {
                DetailSheetView(item: selectedItem)
            }
        }
    }
}

struct DetailSheetView: View {
    let item: String?
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                CardMedium()
                    .setText(.title, item ?? "Unknown")
                    .padding()
                
                Text("This is the detail view for \(item ?? "this item")")
                    .padding()
                
                Spacer()
            }
            .navigationTitle("Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    ModalViewExample()
}
```

### Pattern 10: Search with Play Components

```swift
import SwiftUI
import PlayComponents

struct SearchableView: View {
    @State private var searchText = ""
    @State private var results: [String] = []
    
    let allItems = ["Apple", "Apricot", "Banana", "Blueberry", "Cherry", "Coconut"]
    
    var filteredItems: [String] {
        if searchText.isEmpty {
            return allItems
        }
        return allItems.filter { $0.localizedCaseInsensitiveContains(searchText) }
    }
    
    var body: some View {
        NavigationStack {
            VStack {
                SearchBar(text: $searchText)
                    .padding()
                
                if filteredItems.isEmpty {
                    CardMedium()
                        .setText(.title, "No Results Found")
                        .padding()
                } else {
                    List(filteredItems, id: \.self) { item in
                        CardMedium()
                            .setText(.title, item)
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Search")
        }
    }
}

struct SearchBar: View {
    @Binding var text: String
    
    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.gray)
            
            TextField("Search...", text: $text)
                .textFieldStyle(.roundedBorder)
            
            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.gray)
                }
            }
        }
    }
}

#Preview {
    SearchableView()
}
```

---

## Key Takeaways for All Patterns

1. **Always use `.setText()` and `.setImage()` helpers** for data updates
2. **Wrap state changes in `withAnimation()`** for smooth transitions
3. **Use `@State` for local component state**, `@StateObject` for view models
4. **Bind with `$`** when passing state to component modifiers
5. **Keep Play components at top level**, layer native SwiftUI around them
6. **Test in preview** before shipping
7. **Re-export from Play** when design changes; Xcode package auto-updates

