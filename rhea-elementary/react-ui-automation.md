# Automating React/Radix UI Web Applications

## The Core Problem
Modern React apps don't respond to simple `.click()`. They use synthetic event systems.

## Solution: Full Pointer Event Chain
```javascript
// This FAILS on React/Radix buttons:
button.click();

// This WORKS:
["pointerdown", "mousedown", "pointerup", "mouseup", "click"].forEach(evt => {
  button.dispatchEvent(new MouseEvent(evt, {
    bubbles: true,
    cancelable: true,
    view: window
  }));
});
```

## Menu/Dialog Automation Pattern

```javascript
async function automateMenuAction(triggerSelector, menuItemText, confirmBtnText) {
  // 1. Click trigger button (full event chain)
  var btn = document.querySelector(triggerSelector);
  btn.scrollIntoView({block: "center"});
  ["pointerdown","mousedown","pointerup","mouseup","click"].forEach(evt => {
    btn.dispatchEvent(new MouseEvent(evt, {bubbles:true, cancelable:true, view:window}));
  });

  // 2. Wait for dropdown
  await new Promise(r => setTimeout(r, 800));

  // 3. Find and click menu item
  var items = document.querySelectorAll("[role=menuitem]");
  var target = Array.from(items).find(i => i.innerText.trim() === menuItemText);
  target.click();

  // 4. Wait for confirmation dialog
  await new Promise(r => setTimeout(r, 800));

  // 5. Find and click confirm button
  var dialog = document.querySelector("[role=dialog]");
  var confirmBtn = Array.from(dialog.querySelectorAll("button"))
    .find(b => b.innerText.trim() === confirmBtnText);
  confirmBtn.click();

  // 6. Wait for API call to complete
  await new Promise(r => setTimeout(r, 1500));
}
```

## Batch Automation Loop

```javascript
async function removeAll() {
  var removed = 0;
  for (var attempt = 0; attempt < 50; attempt++) {
    // Find next target
    var target = document.querySelector("button.my-target");
    if (!target) break;

    // Execute action sequence
    await automateMenuAction(target, "Remove", "Confirm");
    removed++;
  }
  return "removed " + removed;
}
```

## DOM Identification Strategies

### By known text anchor
```javascript
var configBtns = Array.from(document.querySelectorAll("button"))
  .filter(b => b.innerText.trim() === "Configure");
```

### By aria attributes
```javascript
document.querySelectorAll("[aria-haspopup=menu]")  // dropdown triggers
document.querySelectorAll("[aria-expanded=true]")   // open dropdowns
document.querySelectorAll("[role=dialog]")           // modals
```

### By Radix UI data attributes
```javascript
document.querySelectorAll("[data-radix-popper-content-wrapper]")  // popovers
document.querySelectorAll("[data-state=open]")                     // open components
```

### Tag elements for later retrieval
```javascript
configBtns.forEach((btn, i) => btn.setAttribute("data-my-tag", i));
// Later:
document.querySelector('[data-my-tag="0"]');
```

## Timing Guidelines
- After button click: wait 500-800ms for dropdown/dialog
- After API-triggering action: wait 1000-1500ms for completion
- Before re-querying DOM: wait 300ms for React re-render
- Always verify state after waiting (don't assume success)
