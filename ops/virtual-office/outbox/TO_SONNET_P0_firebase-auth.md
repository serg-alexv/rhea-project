# TO: Sonnet Worker | P0 | Add Firebase Auth to REST Client

## Task
Read /Users/sa/rh.1/ops/rhea_firebase.py and /Users/sa/rh.1/firebase/service-account.json.

Firestore rules now require `request.auth != null`. The REST client uses unauthenticated requests → 403.

Fix: Add service account JWT auth to the REST client.
1. Read service-account.json to get `client_email` and `private_key`
2. Generate a signed JWT (Google OAuth2 service account flow)
3. Exchange JWT for access token via https://oauth2.googleapis.com/token
4. Add `Authorization: Bearer <token>` to all Firestore REST requests
5. Cache token (expires in 3600s), refresh when expired

Use only stdlib (json, urllib, base64, hmac/hashlib) + PyJWT if available, otherwise raw JWT construction.

Update /Users/sa/rh.1/ops/rhea_firebase.py in place. Test with `health` command.

NEVER pause. Execute fully. Best-effort + [ASSUMPTION] tags.
