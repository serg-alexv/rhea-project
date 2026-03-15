# Play AI

Play AI allows you to leverage AI within Play for macOS to [design](/en/articles/design-mode) and [prototype](/en/articles/interactions). You can design basic layouts, select objects based on properties, update content, access learning resources, configure interaction nodes, add prefabs, and more. You can also generate an [AI View](/en/articles/ai-view), which uses external GPTs to create modules, pages, or full flows in Play.

## Availability

Play AI is currently in beta and available to all users on any plan. During the beta phase, we've set a daily credit limit, which may change as we continue testing and tuning performance.

After beta, Play AI will transition to a tiered credit system — with different credit amounts included for each [paid plan](/en/articles/plans-and-upgrades).

## Play AI Panel

Prompt Play AI in the Play AI left side panel. You can toggle this panel in and out of view by clicking on the sparkle (AI) icon or using the keyboard shortcut `OPT + 6`.

Use the panel's text field to enter your prompt, starting with a command from the section below.

## Add Context

Use the panel's Add button to upload relevant images or JSON files or to mention relevant context in Play, like layers, styles, assets, main components, states, variables, or interaction nodes. Mentioning can also be done by typing "@" in the text field.

## Best Practices

To achieve the best results, we strongly recommend using a command (like /design or /learn) before every prompt and specifically mentioning the layer or node you'd like to affect, rather than relying on the selected object.

Instead of writing "apply a glass effect," you should write "/effect apply a glass effect to @Stack 1".

## Commands

Help Play AI contextualize your prompt by starting with a command. Type "/" and select any of the following commands, followed by your prompt.

### Generate

Use this command to create interactive modules or pages with an external GPT. These AI Views can be used within Play prototypes but are not made of Play elements or interactions. The result will be similar to what you might get in Lovable. Learn more in this article.

Examples:
```
/generate an onboarding flow
/generate an analog clock that ticks
/generate a to do list
```

### Design

Use this command to add elements and components to your design or to edit object properties, like size.

Examples:
```
/design create a stack with a title, subtitle, and image
/design add a primary and secondary button in a stack
/design create a row with a title text "Notifications" and a subtitle "Enable push alerts". Place a switch on the right side to turn it on/off.
```

### Effect

Use this command to apply shadows, borders, blurs, or glass effects.

Examples:
```
/effect apply a glass effect to @Object 1
/effect add a black shadow to @Object 1
/effect add a blue 2pt border to @Object 1
```

### Interaction

Use this command to add triggers, actions, or other interaction nodes.

Examples:
```
/interaction tap @Object 1 to go to page 2 and play a haptic
/interaction when the user scrolls @Page 1 passed 200, set @Component to @default state
/interaction print all global variables on load
```

### Prefab

Use this command to insert ready-made patterns, called prefabs, that accomplish a common interaction.

Examples:
```
/prefab make @Object 1 draggable
/prefab add a tinder style swipe to the cards in @Stack 1
/prefab animate in the children of @Page 1
```

### Select

Use this command to select layers or interactions based on certain criteria.

Examples:
```
/select all stacks with a blue background
/select all text size 16
/select all layers without Fill width
```

### Command

Use this command to move, duplicate, or delete layers.

Examples:
```
/ delete the last object in @Stack 1
/duplicate @Object 1 five times
/move all text elements into @Stack 1
```

### Text

Use this command to edit text or labels.

Examples:
```
/text make each text element say "city"
/text rewrite @Text 1 for clarity
/text translate @Text 1 to Spanish
```

### Image

Use this command to fill images from your assets or Unsplash.

Examples:
```
/image randomly fill all images
/image fill all images 64pt x 64pt with profile photos
/image fill @Image 1 with a picture of pizza
```

### Rename

Use this command to rename specific layers, selected layers, or all layers based on their context.

Examples:
```
/rename selection
/rename all symbols 24pt x 24pt
/rename @Object 1
```

### Learn

Use this command to ask about a concept in Play, and we'll return relevant resources.

Examples:
```
/learn what is a pan gesture?
/learn what is a component instance vs. a component state?
/learn how does layout work in Play?
```