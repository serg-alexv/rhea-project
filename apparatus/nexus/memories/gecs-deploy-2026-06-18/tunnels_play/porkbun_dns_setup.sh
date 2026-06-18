#!/bin/sh
# porkbun_dns_setup.sh - for LeoTimelabs domain at Porkbun
# Login: https://porkbun.com/account/login
# User: LeoTimelabs
# Pass: n:V.w-8YN4sTzfH
# Domain likely leotimelabs.com or similar (check in dashboard after login)
# Use for Google Workspace verification (get code from Google Admin > verify domain)

# After user gets verification from Google:
DOMAIN="leotimelabs.com"  # confirm exact in Porkbun
VERIFICATION_TXT="google-site-verification=REPLACE_WITH_CODE_FROM_GOOGLE"

echo "=== Porkbun DNS Setup for LeoTimelabs ==="
echo "1. Open https://porkbun.com/account/login"
echo "2. Login with LeoTimelabs / n:V.w-8YN4sTzfH"
echo "3. Go to Domains > Manage > $DOMAIN > DNS Management"
echo "4. Add new record:"
echo "   Type: TXT"
echo "   Host: @"
echo "   Answer: $VERIFICATION_TXT"
echo "   TTL: 300"
echo "5. Save, wait 5-60 min, then verify in Google Admin."
echo ""
echo "Note: To avoid fraud, do this while on clean IP (run the router bootstrap, connect iPhone/Mac to blueshoes WiFi or use gcloud proxy 35.224.79.36:8888)."
echo "Update this script with actual code and push to memory."
echo "For Porkbun API (better automation): after login, generate API key/secret in account settings, then use curl for DNS edits."
