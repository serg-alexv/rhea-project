# PROC-001 — Firebase Office Usage
Symptom: Need to send/receive messages between agents across terminals
Cause (guess): No shared real-time channel exists besides git
Fix (exact commands):
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/Users/sa/rh.1/firebase/service-account.json
# Heartbeat
/usr/bin/python3 /Users/sa/rh.1/ops/rhea_firebase.py heartbeat <DESK> ALIVE
# Send message
/usr/bin/python3 /Users/sa/rh.1/ops/rhea_firebase.py send <FROM> <TO> "<message>"
# Check inbox
/usr/bin/python3 /Users/sa/rh.1/ops/rhea_firebase.py inbox <DESK>
# Save gem
/usr/bin/python3 /Users/sa/rh.1/ops/rhea_firebase.py gem <ID> "<text>" "<source>" "<topic>"
# Full status
/usr/bin/python3 /Users/sa/rh.1/ops/rhea_firebase.py status
```
Verify: `status` command shows your desk with recent timestamp
Rollback: Fall back to file-based inbox/outbox in ops/virtual-office/
Notes: Service account key at firebase/service-account.json (gitignored). Python 3.9 warnings are cosmetic.
