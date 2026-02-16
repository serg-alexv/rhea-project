#!/usr/bin/env bash
# bridge-probe.sh — Health probe for all 6 Rhea bridge providers
# Runs a 1-token cheap test against each provider and produces a status table.
# Usage: bash ops/bridge-probe.sh
#
# Compatible with bash 3.2+ (macOS default).
set -euo pipefail

RHEA_ROOT="/Users/sa/rh.1"
BRIDGE="$RHEA_ROOT/src/rhea_bridge.py"
ENV_FILE="$RHEA_ROOT/.env"
TMPJSON=$(mktemp /tmp/bridge-probe-XXXXXX.json)
trap 'rm -f "$TMPJSON"' EXIT

# ── Load .env ────────────────────────────────────────────────────────────────
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^\s*$' | xargs)
    set +a
fi

# ── Timestamp ────────────────────────────────────────────────────────────────
TIMESTAMP=$(date '+%Y-%m-%d %H:%M %Z')

# ── Provider / model table ───────────────────────────────────────────────────
# One cheap model per provider.  Format: display_name|bridge_spec|display_model
PROBES=(
    "OpenAI|openai/gpt-4o-mini|gpt-4o-mini"
    "OpenRouter|openrouter/anthropic/claude-sonnet-4|anthropic/claude-sonnet-4"
    "Google Gemini|gemini/gemini-2.0-flash|gemini-2.0-flash"
    "DeepSeek|deepseek/deepseek-chat|deepseek-chat"
    "Azure AI Foundry|azure/gpt-4o-mini|gpt-4o-mini"
    "HuggingFace|huggingface/mistralai/Mistral-7B-Instruct-v0.3|Mistral-7B-Instruct-v0.3"
)

LIVE=0
DOWN=0
TOTAL=${#PROBES[@]}

# ── Helper: parse bridge JSON output ─────────────────────────────────────────
# Reads $TMPJSON, prints: status_icon|latency_ms|error_msg  (pipe-delimited)
parse_bridge_json() {
    /usr/bin/python3 -c "
import json, re, sys
try:
    with open(sys.argv[1]) as f:
        raw = f.read()
    d = json.loads(raw)
    err = d.get('error') or ''
    lat = d.get('latency_s', 0)
    if not err:
        ms = int(float(lat) * 1000)
        print('OK|%dms|' % ms)
    else:
        m = re.search(r'(\d{3})', err)
        code = m.group(1) if m else 'ERR'
        # Replace pipes in error msg to avoid breaking delimiter
        safe_err = err.replace('|', '/')
        print('%s||%s' % (code, safe_err))
except Exception as e:
    print('ERR||JSON parse error: %s' % str(e).replace('|', '/'))
" "$TMPJSON"
}

# ── Collect results ──────────────────────────────────────────────────────────
# We store results as pipe-delimited strings in a flat array
# Each entry: "provider|model|status|latency|error"
RESULTS=()

idx=0
for entry in "${PROBES[@]}"; do
    IFS='|' read -r display_name bridge_spec display_model <<< "$entry"

    echo -n "  Probing $display_name ($display_model)... "

    # Run the bridge ask command; capture stdout+stderr into temp file
    set +e
    /usr/bin/python3 "$BRIDGE" ask "$bridge_spec" "ping" > "$TMPJSON" 2>&1
    exit_code=$?
    set -e

    if [[ $exit_code -ne 0 ]]; then
        status_icon="FAIL"
        latency_ms=""
        error_msg="bridge exit code $exit_code"
        DOWN=$((DOWN + 1))
        echo "FAIL"
    else
        # Parse the pipe-delimited line from the JSON parser
        parsed=$(parse_bridge_json)
        IFS='|' read -r status_icon latency_ms error_msg <<< "$parsed"

        if [[ "$status_icon" == "OK" ]]; then
            LIVE=$((LIVE + 1))
            echo "OK (${latency_ms})"
        else
            DOWN=$((DOWN + 1))
            echo "$status_icon"
        fi
    fi

    RESULTS+=("${display_name}|${display_model}|${status_icon}|${latency_ms}|${error_msg}")
    idx=$((idx + 1))
done

# ── Print table ──────────────────────────────────────────────────────────────
SEP="--------------------------------------------------------------------------------------------------------------"

echo ""
echo "RHEA BRIDGE HEALTH PROBE -- $TIMESTAMP"
echo "================================================"
printf "%-18s %-34s %-10s %-10s %s\n" "Provider" "Model" "Status" "Latency" "Error"
echo "$SEP"

for row in "${RESULTS[@]}"; do
    IFS='|' read -r prov model st lat err <<< "$row"

    [[ -z "$lat" ]] && lat="--"
    [[ -z "$err" ]] && err="--"

    printf "%-18s %-34s %-10s %-10s %s\n" "$prov" "$model" "$st" "$lat" "$err"
done

echo "$SEP"
echo "LIVE: $LIVE/$TOTAL | DOWN: $DOWN/$TOTAL"
echo ""

# ── Suggested fixes for failures ─────────────────────────────────────────────
printed_header=false
for row in "${RESULTS[@]}"; do
    IFS='|' read -r prov model st lat err <<< "$row"
    [[ "$st" == "OK" ]] && continue

    if ! $printed_header; then
        echo "SUGGESTED FIXES"
        echo "==============="
        printed_header=true
    fi

    fix=""
    case "$prov" in
        "Google Gemini")
            if echo "$err" | grep -q "429"; then
                fix="Rate-limited. Check billing at console.cloud.google.com/billing or wait for quota reset."
            elif echo "$err" | grep -q "400"; then
                fix="Geo-blocked or bad request. Use OpenRouter bypass: openrouter/google/gemini-2.5-pro-preview"
            elif echo "$err" | grep -q "403"; then
                fix="API key lacks permission. Re-enable Generative Language API at console.cloud.google.com/apis"
            else
                fix="Check GEMINI_API_KEY in .env. Dashboard: console.cloud.google.com/apis"
            fi
            ;;
        "DeepSeek")
            if echo "$err" | grep -q "402"; then
                fix="Insufficient balance. Top up at platform.deepseek.com"
            elif echo "$err" | grep -q "401"; then
                fix="Bad API key. Rotate at platform.deepseek.com/api_keys"
            else
                fix="Check DEEPSEEK_API_KEY in .env. Dashboard: platform.deepseek.com"
            fi
            ;;
        "Azure AI Foundry")
            if echo "$err" | grep -q "401"; then
                fix="Bad credentials. Rotate key at portal.azure.com -> Azure OpenAI -> Keys"
            elif echo "$err" | grep -q "403"; then
                fix="Access denied. Check Azure subscription and model deployment."
            elif echo "$err" | grep -q "404"; then
                fix="Model not deployed. Check Azure AI Foundry model catalog deployments."
            else
                fix="Check AZURE_API_KEY in .env. Portal: portal.azure.com"
            fi
            ;;
        "HuggingFace")
            if echo "$err" | grep -q "404"; then
                fix="Model URL not found. Check URL construction in rhea_bridge.py _call_huggingface()"
            elif echo "$err" | grep -q "401"; then
                fix="Bad token. Rotate at huggingface.co/settings/tokens"
            elif echo "$err" | grep -q "503"; then
                fix="Model loading. HuggingFace Inference API may need a cold start. Retry in 60s."
            else
                fix="Check HF_TOKEN in .env. Dashboard: huggingface.co/settings/tokens"
            fi
            ;;
        "OpenAI")
            if echo "$err" | grep -q "401"; then
                fix="Bad API key. Rotate at platform.openai.com/api-keys"
            elif echo "$err" | grep -q "429"; then
                fix="Rate limited. Check usage at platform.openai.com/usage"
            elif echo "$err" | grep -q "insufficient"; then
                fix="Insufficient credits. Top up at platform.openai.com/settings/billing"
            else
                fix="Check OPENAI_API_KEY in .env. Dashboard: platform.openai.com"
            fi
            ;;
        "OpenRouter")
            if echo "$err" | grep -q "401"; then
                fix="Bad API key. Rotate at openrouter.ai/keys"
            elif echo "$err" | grep -q "402"; then
                fix="Insufficient credits. Top up at openrouter.ai/credits"
            elif echo "$err" | grep -q "429"; then
                fix="Rate limited. Check usage at openrouter.ai/activity"
            else
                fix="Check OPENROUTER_API_KEY in .env. Dashboard: openrouter.ai/keys"
            fi
            ;;
        *)
            fix="Check API key and provider config in rhea_bridge.py"
            ;;
    esac

    echo "  $prov ($st): $fix"
done

if $printed_header; then
    echo ""
fi
