# WHAT WORKS — Confirmed Functionality

**Last verified:** 2026-03-14  
**Status:** Core API functional, services partially deployed

## ✅ CONFIRMED WORKING

### Tribunal API (Core Product)

- **186 endpoints** loaded successfully  
- **Multi-model bridge**: 4 live providers (gemini, github, openai, openshift_ai)
- **Core consensus endpoints**: `/tribunal`, `/tribunal/ice`, `/tribunal/sceptic`
- **Health check**: `/health` endpoint responsive
- **Authentication**: JWT auth system functional
- **Memory system**: Persistent storage via rhea-memory package
- **Setup script**: One-command deployment works (`deploy/setup.sh`)

### Documentation & Infrastructure

- **README**: Complete with install instructions, API examples
- **Requirements**: All Python dependencies installable
- **Virtual environment**: `.venv` configured and functional
- **Environment keys**: API keys configured (Gemini, OpenAI, Firebase)
- **Git repository**: Clean history, all commits pushed

### Package Ecosystem

- **rhea-memory**: Standalone pip package (MIT, zero deps)
- **RheaKit**: Swift framework for iOS/macOS
- **CLI tools**: Multiple Rust-based utilities built and ready

## ⚠️ PARTIAL / BROKEN

### Service Deployment

- **Session Server**: Not currently running (port 3000 down)
- **AI Auth**: Not currently running (port 3001 down)  
- **Angel Game**: Not currently running (port 3002 down)
- **BioRenderer**: Not currently running (port 3003 down)
- **RAG Storage**: Not currently running (port 3004 down)
- **Play Token Mapper**: Not currently running (port 3006 down)
- **Logical Keyboard**: Not currently running (port 3005 down)

### Integration Tests

- **test_integration.sh**: Fails at Test 1 (services down)
- **Expected**: 10/10 tests passing (currently 0/10)

### Billing & OAuth

- **Stripe integration**: Configured but secrets validation blocks startup
- **BTCPay**: Not configured
- **Google OAuth**: Keys present but disabled
- **Microsoft OAuth**: Keys present but disabled

### Database

- **CockroachDB**: Not connected (crdb_store disabled)
- **Firebase**: Configured but connection status unknown
- **SQLite**: Local users.db exists but not verified

## ❓ UNKNOWN STATUS

### Production Deployment

- **Fly.io deployment**: Mentioned in docs but not verified
- **Cloud Run**: Scripts exist but not tested
- **Docker images**: Build status unknown
- **TLS certificates**: Not verified

### External Integrations

- **GitHub API**: Token detected but not tested
- **Google Cloud**: Partially configured (Firestore keys present)
- **Redis**: Configured but connection status unknown
- **ZMQ**: Installed but not tested

### Mobile Apps

- **iOS app**: Xcode project exists but build status unknown
- **macOS Command Centre**: Exists but not tested
- **Atlas dashboard**: Next.js build exists but deployment unknown

## 🎯 CURRENT FIRST-DELIVERY TARGET

**Tribunal API as Service**  
Deploy the core multi-model consensus API as a standalone service:

1. **Single endpoint focus**: `/tribunal` consensus endpoint
2. **Minimal billing**: Per-call billing ($0.05/tribunal call)  
3. **Simple deployment**: Cloud Run or Fly.io
4. **One-page docs**: cURL examples + API key setup
5. **External test**: Send URL to 1 real external user

This bypasses the complex multi-service architecture and delivers the core value proposition immediately.
