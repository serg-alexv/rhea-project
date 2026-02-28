# RheaPreview iOS Quickstart

Fastest path to a running iOS app (simulator or device).

## 1) Ensure backend/web are up
- Atlas web: `http://localhost:3000`
- API: `http://localhost:8400`

Quick check:
```bash
bash scripts/ios_preview.sh status
```

## 2) Open app in Xcode
```bash
bash scripts/ios_preview.sh open
```

## 3) Run
- Select iPhone Simulator (or your device)
- Press Run

## 4) If using physical iPhone
`localhost` will not point to your Mac. In app:
- Open **Settings** tab
- Set:
  - Atlas URL: `http://<your-mac-ip>:3000`
  - API URL: `http://<your-mac-ip>:8400`
- Tap **Save**

## 5) Validate
- **Atlas** tab renders web UI
- **Governor** tab loads `/governor`
- **Tasks** tab loads `/tasks`

## Notes
- URLs are persisted in `@AppStorage`.
- Default URLs:
  - Atlas: `http://localhost:3000`
  - API: `http://localhost:8400`
