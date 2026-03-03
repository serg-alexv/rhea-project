# RheaKit vs SwiftUI View Mapping

Goal: own **all** SwiftUI view types by either mapping them to existing `packages/RheaKit` components or flagging a wrapper/task for future implementation. Below is the master list.

| SwiftUI View | Status | RheaKit equivalent / notes |
| --- | --- | --- |
| `VStack`, `HStack`, `ZStack` | ✅ | `GovernorView`, `ToolsHubView`, `DialogView` already use stacked layouts for panels.
| `LazyVStack`, `LazyHStack` | ⚠️ | Not yet; plan a `LazyFlowView` for large task lists (NodeEditor/TasksView can be extended).
| `ScrollView`, `ScrollViewReader` | ✅ | `TasksView`, `HistoryView`, `ProcessesView` already wrap scrollable lists.
| `Group`, `ConditionalContent`, `AnyView` | ✅ | Used across BioRenderer/NodeEditor for dynamic content.
| `Spacer`, `Divider` | ✅ | Used in `TeamChatView`, `ClipboardView`, etc.
| `GeometryReader` | ⚠️ | BioRenderer uses geometry data; consider `MeshManager` helpers.
| `Divider` | ✅ | Already present.
| `Section`, `List`, `Form` | ⚠️ | `TasksView`/`HistoryView` mimic sections; future `FormView` to wrap `SettingsView`.
| `Grid`, `LazyVGrid`, `LazyHGrid` | ⚠️ | To implement when atlas needs dashboards with rows/columns (candidate for new `AtlasGrid` component).
| `OutlineGroup` | ⚠️ | NodeGraph needs outline view; wrap via `NodeEditorView`.
| `VSplitView`, `HSplitView` | ⚠️ | Could wrap `RuliadView` and `BioRendererView` for split screens.
| `TabView` | ✅ | `ToolsHubView`, `GovernorView` already expose tabs; expand semantics.
| `Text`, `Image` | ✅ | Core to most views.
| `Button`, `Link`, `Label` | ✅ | In AuthView, ToolsHub, etc.
| `Toggle`, `TextField`, `SecureField`, `Picker`, `Stepper`, `Slider` | ⚠️ | Need new subcomponents when config UI becomes richer (SettingsView should adopt them). 
| `DatePicker` | ⚠️ | Add to `TasksView` scheduling if needed.
| `Menu`, `ProgressView`, `DisclosureGroup`, `ToolbarItem`, `SearchField`, `NavigationBarItem` | ⚠️ | Build toolbar/toolbar item wrappers in `ToolsHubView`.
| `Alert`, `Sheet`, `Popover`, `ContextMenu`, `Tooltip`, `Overlay`, `PresentationDetents`, `ConfirmationDialog` | ⚠️ | Wrap in `DialogView`/ToolsHub overlays; each modal type gets handler.
| `Canvas`, `TimelineView`, `MatchedGeometryEffect`, `Material`, `Color`, `Gradient`, `Path`, `Shape`, `Rectangle`, `Circle`, `Capsule`, `Ellipse`, `RoundedRectangle`, `GroupBox`, `Shader`, `SymbolRenderingMode` | ✅/⚠️ | BioRenderer/Shader components already cover many; fill gaps via `BioRendererView` wrappers.
| `NavigationView`, `NavigationStack`, `NavigationSplitView`, `NavigationLink` | ⚠️ | NodeEditor/office navigation uses custom navigation; extend to general navigation controllers.
| `Scene`, `WindowGroup`, `Commands`, `App`, `MenuBarExtra` | ⚠️ | Partially handled by macOS launcher; document the desired wrappers.

## Next actions
1. For each ⚠️ view: create a mini-task (e.g., `Wrap LazyVGrid as AtlasGridView`). Track tasks in Mongo queue (`TaskDBMongo`), claim via swarms.
2. The new `docs/playui-swarm-plan.md` should reference the table: e.g., NodeEditor swarm owns OutlineGroup/Navigation components, Author Toolkit swarm handles Alerts/Sheets.
3. Add `rhea-cli biorendera export` to unlock Material/Path views; treat them as actual BioRenderer wrappers.
4. Keep this doc updated as we add wrappers; “last bite” is when every SwiftUI view has a RheaKit story.

Need me to auto-claim these ⚠️ wrappers via the Mongo queue or just document them here?"EOF