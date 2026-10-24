# Kotlin Android chart reference PoC

This native Android reference renders the canonical synthetic OHLCV fixture using a custom Canvas view, volume bars, horizontal panning, zoom buttons, accessible descriptions and a textual table of all candles. It intentionally has no market-data connection, provider secrets, network permission or trading functionality.

## Build

The workflow generates the Gradle wrapper using the runner's installed Gradle and pins it to Gradle 8.11.1 before building. For local builds, install JDK 17 and Android SDK Platform 36 / Build Tools, then run:

```powershell
gradle wrapper --gradle-version 8.11.1
.\gradlew.bat assembleDebug
.\gradlew.bat assembleRelease
```

The fixture is synthetic test data, not historical market data. Build and runtime evidence must remain separated by host environment; the Kotlin Android reference does not represent an iOS implementation.
