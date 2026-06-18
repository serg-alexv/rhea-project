#!/bin/sh
# porkbun_api_dns.sh - Automate DNS for LeoTimelabs domain using Porkbun API
# First: Login to https://porkbun.com/account/login with LeoTimelabs / n:V.w-8YN4sTzfH
# Then: Generate API Key + Secret in Account > API Access (or "API" section)
# Paste them below or pass as env: PORK_API_KEY=xxx PORK_SECRET_KEY=yyy ./porkbun_api_dns.sh add-txt "google-site-verification=THECODE"

API_KEY="${PORK_API_KEY:-YOUR_API_KEY_HERE}"
SECRET_KEY="${PORK_SECRET_KEY:-YOUR_SECRET_KEY_HERE}"

DOMAIN="leotimelabs.com"  # confirm exact from Porkbun dashboard
BASE_URL="https://porkbun.com/api/json/v3"

usage() {
  echo "Usage: $0 {add-txt|list|delete} [value]"
  echo "Example: $0 add-txt 'google-site-verification=abc123'"
  exit 1
}

if [ -z "$API_KEY" ] || [ "$API_KEY" = "YOUR_API_KEY_HERE" ]; then
  echo "ERROR: Set PORK_API_KEY and PORK_SECRET_KEY env or edit the script with keys from Porkbun dashboard."
  echo "Login at the provided URL, go to API section, create key/secret (they are shown once)."
  exit 1
fi

add_txt() {
  local value="$1"
  if [ -z "$value" ]; then
    echo "Provide the TXT value, e.g. google-site-verification=..."
    exit 1
  fi
  echo "Adding TXT @ = $value to $DOMAIN ..."
  curl -s -X POST "$BASE_URL/dns/create/$DOMAIN" \
    -H "Content-Type: application/json" \
    -d '{
      "apikey": "'$API_KEY'",
      "secretapikey": "'$SECRET_KEY'",
      "name": "",
      "type": "TXT",
      "content": "'"$value"'",
      "ttl": "300"
    }' | cat
  echo ""
  echo "Done. Check with: $0 list"
}

list_records() {
  echo "Listing DNS for $DOMAIN ..."
  curl -s -X POST "$BASE_URL/dns/retrieve/$DOMAIN" \
    -H "Content-Type: application/json" \
    -d '{
      "apikey": "'$API_KEY'",
      "secretapikey": "'$SECRET_KEY'"
    }' | cat
}

delete_record() {
  local id="$1"
  if [ -z "$id" ]; then
    echo "Provide record ID from list"
    exit 1
  fi
  echo "Deleting record $id ..."
  curl -s -X POST "$BASE_URL/dns/delete/$DOMAIN/$id" \
    -H "Content-Type: application/json" \
    -d '{
      "apikey": "'$API_KEY'",
      "secretapikey": "'$SECRET_KEY'"
    }' | cat
}

case "$1" in
  add-txt) add_txt "$2" ;;
  list) list_records ;;
  delete) delete_record "$2" ;;
  *) usage ;;
esac
