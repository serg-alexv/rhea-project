# Host Build

Successful build command:

```sh
cd /Users/sa/rh.1/play && xcodebuild -project /Users/sa/rh.1/play/RheaPlay.xcodeproj -scheme RheaPlay -configuration Debug -derivedDataPath /tmp/RheaPlayDerivedData CODE_SIGNING_ALLOWED=NO build
```

Expected success signal:

```text
** BUILD SUCCEEDED **
```

Signing is not required for this command because it sets:

```text
CODE_SIGNING_ALLOWED=NO
```
