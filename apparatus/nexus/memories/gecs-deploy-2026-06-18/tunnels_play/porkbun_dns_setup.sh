#!/bin/sh
# porkbun_dns_setup.sh - template for adding Google Workspace verification records in Porkbun for LeoTimelabs domain.
# Usage: after getting the verification code from Google Admin (for the domain under LeoTimelabs account).
# Login to Porkbun with the provided credentials (user: LeoTimelabs, pass: n:V.w-8YN4sTzfH).
# Add the TXT record as shown.

DOMAIN="leotimelabs.com"  # confirm exact with Porkbun dashboard; may be .net or other
VERIFICATION_TXT="google-site-verification=PUT_THE_CODE_FROM_GOOGLE_HERE"

echo "1. Login to https://porkbun.com/account/login with LeoTimelabs / n:V.w-8YN4sTzfH"
echo "2. Go to Domain Management > select $DOMAIN > DNS Management"
echo "3. Add TXT record:"
echo "   Host: @ (or blank for root)"
echo "   Value: $VERIFICATION_TXT"
echo "   TTL: 300 or default"
echo "4. For mail if needed: add MX or other as per Google setup."
echo "5. Wait for propagation (use dig TXT $DOMAIN)"
echo "6. Verify in Google Admin."
echo ""
echo "Note: Use the clean IP path (via router tunnel or gcloud proxy) when doing the verification from browser if possible, to avoid fraud flags."
echo "Update this with actual records added."
