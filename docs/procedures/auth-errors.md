# Bridge Auth Error Procedures

## 401 — Bad Credentials

### Azure
1. Go to portal.azure.com → Azure OpenAI → Keys and Endpoints
2. Copy Key 1 or Key 2
3. Update AZURE_API_KEY in /Users/sa/rh.1/.env
4. Verify: bash ops/bridge-probe.sh

### OpenAI
1. Go to platform.openai.com/api-keys
2. Create or copy key
3. Update OPENAI_API_KEY in .env

## 402 — Insufficient Balance

### DeepSeek
1. Go to platform.deepseek.com → Billing
2. Top up balance (minimum $5)
3. Verify: bash ops/bridge-probe.sh

## 404 — Not Found

### HuggingFace
1. Bug in rhea_bridge.py _call_huggingface() URL construction
2. Fix: check the inference API URL format
3. Current URL pattern may be wrong — verify against https://huggingface.co/docs/api-inference

## 429 — Rate Limit / Quota

### Gemini T0
1. Go to console.cloud.google.com/billing
2. Check quota usage for Generative Language API
3. Wait for quota reset or upgrade plan

### Gemini T1 (400 geo-block)
1. User in Russia — direct API blocked
2. Workaround: use OpenRouter bypass (openrouter/google/gemini-2.5-pro-preview)
3. Already configured in bridge
