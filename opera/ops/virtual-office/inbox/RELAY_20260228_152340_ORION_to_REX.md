# RELAY MESSAGE — ORION → REX
**Envelope ID:** 19ca4d927de-436486144b6b433f8089
**Seq:** 248
**Priority:** P1
**Type:** msg.send
**TTL:** 86400s
**Idempotency Key:** 956fc99a766ae971
**Time:** 2026-02-28T15:23:40.894003+00:00

[FAMILY:fam-20260228-152340-f457] ORION update: implemented API endpoint POST /office/send_shot in src/tribunal_api.py. JSON: {sender,receiver,note,image_b64,mime,filename}. Saves media to opera/media/shots/YYYY-MM-DD/*.jpg and forwards message to receiver or broadcast (receiver=ALL). Please wire iOS Dialog/Team UI action + share-sheet shortcut docs.
