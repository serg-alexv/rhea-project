# Bootstrap

Host project: the macOS app in `play/`, generated from `play/project.yml`.

Regenerate the Xcode project:

```sh
cd /Users/sa/rh.1/play && xcodegen generate
```

Build the host:

```sh
cd /Users/sa/rh.1/play && xcodebuild -project /Users/sa/rh.1/play/RheaPlay.xcodeproj -scheme RheaPlay -configuration Debug -derivedDataPath /tmp/RheaPlayDerivedData CODE_SIGNING_ALLOWED=NO build
```
