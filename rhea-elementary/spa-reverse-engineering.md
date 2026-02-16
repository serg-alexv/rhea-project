# Reverse Engineering Any SPA's API

Works on React, Next.js, Vue, Angular — any SPA that makes API calls.

## Step 1: Discover API calls already made
```javascript
var entries = performance.getEntriesByType("resource");
var apis = entries
  .filter(e => e.name.includes("api") || e.name.includes("graphql"))
  .map(e => e.name);
```

## Step 2: Read page-specific JS bundle for endpoint patterns
```javascript
// Find bundle URL from performance entries
var jsChunks = performance.getEntriesByType("resource")
  .filter(e => e.name.includes("_next/static/chunks") && e.name.endsWith(".js"))
  .map(e => e.name);

// Fetch and search a bundle
fetch(jsChunks[0]).then(r => r.text()).then(t => {
  // Find API path patterns
  var paths = t.match(/\/api\/[a-zA-Z_\/{}]+/g);

  // Search for action keywords
  ["disconnect","delete","remove","create","update"].forEach(kw => {
    var idx = t.indexOf(kw);
    if (idx > -1) console.log(kw, t.substring(idx-30, idx+80));
  });
});
```

## Step 3: Make authenticated calls using browser session
```javascript
fetch("/api/whatever", {credentials: "include"})
  .then(r => r.json())
  .then(data => console.log(data));
```

## Step 4: Monkey-patch fetch to capture future calls
```javascript
var origFetch = window.fetch;
window.__capturedRequests = [];
window.fetch = function() {
  var url = arguments[0];
  var method = (arguments[1] && arguments[1].method) || "GET";
  window.__capturedRequests.push({url: url, method: method});
  console.log(method, url);
  return origFetch.apply(this, arguments);
};
```

## Step 5: Identify DOM patterns for automation
```javascript
// Find interactive elements by role
document.querySelectorAll("[role=menuitem]")     // dropdown items
document.querySelectorAll("[role=dialog]")        // modals/confirmations
document.querySelectorAll("[aria-haspopup=menu]") // dropdown triggers
document.querySelectorAll("[data-state=open]")    // Radix UI open states

// Walk DOM from known anchor text to find action buttons
var anchor = Array.from(document.querySelectorAll("button"))
  .find(b => b.innerText.trim() === "Configure");
var row = anchor.parentElement.parentElement;
var menuBtn = row.querySelector("button[aria-haspopup=menu]");
```

## Tips
- `performance.getEntriesByType("resource")` shows ALL network requests since page load
- JS bundles contain hardcoded API paths — searchable with regex
- Browser session cookies authenticate API calls automatically
- React Query / SWR cache can be inspected via React DevTools
- Radix UI components use `data-state="open"/"closed"` for visibility
