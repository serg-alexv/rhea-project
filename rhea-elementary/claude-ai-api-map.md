# Claude.ai Internal API Map

Discovered 2026-02-16 via browser network inspection.

## Organization-scoped endpoints

Pattern: `claude.ai/api/organizations/{org-uuid}/...`

### Sync Services (Gmail, Calendar, GitHub, Drive)
```
GET  /api/organizations/{org}/sync/settings
     → [{type:"gcal",enabled:true}, {type:"gmail",enabled:true}, ...]

GET  /api/organizations/{org}/sync/gmail/auth
GET  /api/organizations/{org}/sync/gcal/auth
GET  /api/organizations/{org}/sync/github/auth
GET  /api/organizations/{org}/sync/mcp/drive/auth
```

### OAuth Tokens (Chrome extension, Claude Code sessions)
```
GET  /api/organizations/{org}/oauth_tokens
GET  /api/organizations/{org}/oauth_tokens?application_slug=xcode
POST /api/oauth/organizations/{org}/oauth_tokens/{id}/revoke
```

### MCP Server Registry (global catalog)
```
GET  https://api.anthropic.com/mcp-registry/v0/servers?version=latest&limit=100&visibility=commercial,health
```

### Account & Features
```
GET  /api/account_profile
GET  /api/organizations/{org}/feature_settings
GET  /api/organizations/{org}/subscription_details
GET  /api/organizations/{org}/overage_spend_limit
GET  /api/organizations/{org}/model_configs/{model-name}
```

### Conversations
```
GET  /api/organizations/{org}/chat_conversations?limit=30&starred=false&consistency=eventual
GET  /api/organizations/{org}/chat_conversations/count_all
```

### Projects
```
GET  /api/organizations/{org}/projects?include_harmony_projects=true&limit=30&order_by=latest_chat
GET  /api/organizations/{org}/projects?include_harmony_projects=true&limit=30&starred=true
```

### Notifications
```
GET  /api/organizations/{org}/notification/channels
```

### Experiences / Feature Flags
```
GET  /api/organizations/{org}/experiences/claude_web?locale=en-US
```

## Notes
- All endpoints use session cookies for auth (works from browser JS with `credentials: "include"`)
- Feature settings include: haystack, thumbs, claude_code_desktop_bypass_permissions, dxt_allowlist, claude_code_review
- OAuth tokens track: Claude for Chrome, Claude Code, Xcode integrations
