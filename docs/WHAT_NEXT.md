# WHAT NEXT — Immediate Actions

**Updated:** 2026-03-14  
**Focus:** Ship Tribunal API as standalone service

## 🎯 CURRENT DELIVERY TARGET

**Tribunal API as Service** - Deploy core consensus endpoint as paid API service

## 📋 NEXT 3 ACTIONS

### 1. Fix Service Startup Blocks

**Issue**: Billing validation prevents API startup  
**Action**: Disable non-essential billing modules  

**Commands**:

```bash
export STRIPE_ENABLED=false
export BTCPAY_ENABLED=false  
export GOOGLE_OAUTH_ENABLED=false
export MICROSOFT_OAUTH_ENABLED=false
python3 src/tribunal_api.py
```

**Expected**: Tribunal API starts on port 8400

### 2. Deploy to Production

**Issue**: No public URL available  

**Action**: Deploy to Fly.io (simplest path)  

**Commands**:

```bash
# Install flyctl if needed
curl -L https://fly.io/install.sh | sh

# Deploy (assuming fly.toml exists)
flyctl deploy
```

**Expected**: Public URL returned (e.g., <https://rhea-tribunal.fly.dev>)

### 3. Setup Minimal Billing

**Issue**: No payment collection mechanism  

**Action**: Implement simple per-call billing  

**Steps**:
- Add Stripe Checkout Session creation
- Require API key for `/tribunal` endpoint  
- Charge $0.05 per consensus call
- Return error if no valid API key

**Expected**: Working pay-per-call API

## 🚧 BLOCKERS

### Technical

- **Billing module validation**: Must disable to start API
- **Missing uvicorn**: Fixed (installed in venv)
- **Service dependencies**: Session server down but not required for core API

### External  

- **Stripe account**: Need to create and configure
- **Domain name**: Optional but recommended for production
- **API key management**: Need simple key generation system

### Process

- **Testing**: Need external user for validation
- **Documentation**: One-page docs need writing
- **Monitoring**: Basic health checks needed

## 🔄 CONTINGENCY PLANS

### If Fly.io deployment fails

1. **Cloud Run**: Use GCP Cloud Run instead
2. **VPS**: Simple Ubuntu VPS with docker-compose
3. **GitHub Codespaces**: Temporary public URL for testing

### If billing integration fails

1. **Free tier**: Offer 100 calls/month for free
2. **Manual billing**: Invoice users monthly
3. **Prepaid credits**: Sell credit packs upfront

### If API keys complex

1. **Single key**: Use one universal API key for all users
2. **No auth**: Make API free for initial launch
3. **GitHub auth**: Use GitHub tokens for authentication

## 📊 SUCCESS METRICS

### Technical

- [ ] Tribunal API starts without errors
- [ ] `/tribunal` endpoint returns consensus results  
- [ ] Health check passes (`/health`)
- [ ] Public URL accessible

### Business

- [ ] External user can make successful API call
- [ ] Payment processed for first paid call
- [ ] Documentation clear enough for self-service

### Operations

- [ ] Deployment automated (one command)
- [ ] Monitoring alerts configured
- [ ] Backup/restore process documented

## 🎯 END STATE

**Working product**: Multi-model consensus API accessible via HTTP POST

```bash
curl -X POST https://rhea-tribunal.fly.dev/tribunal \
  -H "Content-Type: application/json" \
  -H "X-API-Key: user_key_here" \
  -d '{"prompt": "Aspirin inhibits COX-2 selectively"}'
```

Returns: Agreement score, confidence interval, individual model votes, proof ID

**Revenue**: $0.05 per call, automated via Stripe
**Users**: 1+ external users successfully using the service
**Next**: Scale to more users, add features based on feedback
