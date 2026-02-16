# Chrome Browser Automation via AppleScript + JavaScript

## Prerequisites
- Chrome: View > Developer > "Allow JavaScript from Apple Events" (enable once)
- macOS Terminal with osascript access

## Core Patterns

### Navigate to URL
```bash
osascript -e 'tell application "Google Chrome" to set URL of active tab of front window to "https://example.com"'
```

### Execute JS and get result
```bash
osascript -e 'tell application "Google Chrome" to execute front window'\''s active tab javascript "document.title"'
```

### List all tabs
```bash
osascript -e 'tell application "Google Chrome"
  set res to ""
  set tc to count of tabs of front window
  repeat with i from 1 to tc
    set res to res & i & ": " & URL of tab i of front window & linefeed
  end repeat
  return res
end tell'
```

### Switch to specific tab
```bash
osascript -e 'tell application "Google Chrome" to set active tab index of front window to 4'
```

### Store long JS results via document.title
```bash
osascript -e 'tell application "Google Chrome" to execute front window'\''s active tab javascript "
fetch(\"/api/something\", {credentials: \"include\"}).then(function(r) { return r.text(); }).then(function(t) { document.title = t.substring(0, 800); });
\"fetching...\";
"'
sleep 3
osascript -e 'tell application "Google Chrome" to execute front window'\''s active tab javascript "document.title"'
```

### Click React/Radix UI buttons (full event chain)
```bash
osascript -e 'tell application "Google Chrome" to execute front window'\''s active tab javascript "
var btn = document.querySelector(\"button[aria-haspopup=menu]\");
btn.scrollIntoView({block: \"center\"});
var events = [\"pointerdown\", \"mousedown\", \"pointerup\", \"mouseup\", \"click\"];
for (var e = 0; e < events.length; e++) {
  btn.dispatchEvent(new MouseEvent(events[e], {bubbles: true, cancelable: true, view: window}));
}
\"clicked\";
"'
```

### Async automation loop
```bash
osascript -e 'tell application "Google Chrome" to execute front window'\''s active tab javascript "
async function doStuff() {
  // click, await new Promise(r => setTimeout(r, 800)), check DOM, repeat
  return \"done\";
}
doStuff().then(function(r) { document.title = r; });
\"running...\";
"'
```

### Discover API endpoints from any SPA
```bash
osascript -e 'tell application "Google Chrome" to execute front window'\''s active tab javascript "
var entries = performance.getEntriesByType(\"resource\");
var apis = [];
for (var i = 0; i < entries.length; i++) {
  if (entries[i].name.indexOf(\"api\") > -1) apis.push(entries[i].name);
}
apis.join(\"\\n\");
"'
```

## Gotchas
- `missing value` = JS expression returned undefined. Always end with a string.
- Max output ~32KB. For large results, use `document.title` trick.
- Async JS: start it, `sleep N`, then read `document.title`.
- Single quotes in bash+osascript: escape as `'\''`
- Page navigation during automation: always verify `document.location.href` before acting.
- Multiple tabs with same URL: active tab can shift. Pin your tab index.
