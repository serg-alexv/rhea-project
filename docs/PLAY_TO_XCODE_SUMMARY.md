# Play to Xcode: Quick Reference Guide

## Overview
Play to Xcode is a Swift package export feature from Create with Play that lets designers ship iOS apps directly to the App Store without writing UI code.

## The 5-Video Learning Path

| # | Video | Length | Focus |
|---|-------|--------|-------|
| 1 | Publish to App Store | 19:07 | Full end-to-end publishing workflow (dev account → App Store review) |
| 2 | Using Components | 11:17 | Data binding, state management, variables in Xcode |
| 3 | Launch Video | 0:56 | High-level feature overview |
| 4 | Using Play to Xcode | 7:08 | Export wizard, preview, and component integration |
| 5 | Overview | 1:22 | Quick summary of capabilities |

## Critical Workflow (Video 1 Summary)

1. **Publish** → Click publish in Play → Export to Xcode
2. **Xcode Setup** → Trust package → Add Apple ID → Test in simulator
3. **Apple Setup** → Create developer account → Register bundle ID
4. **App Store Setup** → Create app → Link bundle ID → Add build
5. **Metadata** → Screenshots, description, privacy policy, age ratings
6. **Submit** → Add for review → Submit to app review

## Key Techniques (Video 2 Summary)

```swift
// Add component
CardMedium()

// Modify text
.setText(.title, "New Title")

// Modify image
.setImage(.imageOne, UIImage(named: "asset"))

// Manage state
@State private var state: CardMedium.State? = .default
.state($state)
withAnimation { state = .expanded }

// Use variables
CardMedium(isFavorite: true, accentColor: .blue)
```

## Pricing (Per Editor/Month)

| Plan | Monthly | Annual | Features |
|------|---------|--------|----------|
| **Basic** | Free | Free | 1 project, limited |
| **Starter** | $15 | $12 | Unlimited assets, prefabs, watermark-free clips |
| **Pro** | $40 | $30 | Unlimited projects, custom fonts, password protection |
| **Enterprise** | Custom | Custom | Admin seats, dedicated support |

## Integration Steps (For Existing Project)

1. **Export from Play** → Publish → Add to existing project → Name module
2. **Add to Xcode** → File → Add Packages → Select exported folder
3. **Import** → `import PlayComponents`
4. **Use** → `CardMedium()` + `.setText()` / `.setImage()`
5. **Bind Data** → Use `@State` variables and pass to helpers
6. **Connect Backend** → Layer your API calls on top
7. **Update** → Re-export from Play when design changes

## What Exports / What Doesn't

### Exports
- Styles, components, pages, flows
- Interactions, animations, state transitions
- Variables and data bindings
- Assets (images, fonts, videos)
- SwiftUI or UIKit code

### Does NOT Export
- Backend logic
- Database code
- Authentication (you add this)
- Network calls (you add this)
- Complex state machines

## Best Use Cases

✅ MVP apps with design-heavy UI  
✅ Apps where designers lead  
✅ Rapid prototyping → shipping  
✅ Design system → code system  
✅ Startups / agencies  

❌ Data-heavy backend apps  
❌ Complex custom Swift logic  
❌ Highly specialized performance code  

## Gotchas & Tips

1. **Module name ≠ project name** (separate them in export)
2. **Change build target to "Any iOS Device"** before archiving (not simulator)
3. **Use `withAnimation()`** for smooth state transitions
4. **Assets auto-import** (drag & drop to Xcode asset catalog)
5. **State optional** (`State?`) because can be `nil`
6. **Re-export often** — Play → Xcode is iterative, not one-way

## Essential Resources

- Playlist: https://www.youtube.com/playlist?list=PLwRTW8m9R8_Dg5fXOllwNr85nn_OBPC5R
- Docs: https://docs.createwithplay.com
- Example App: Loom (GPT weather app) on App Store

