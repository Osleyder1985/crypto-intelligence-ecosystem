# Issue 9 React Native chart reference PoC

This reference pins Expo SDK 58.0.17, React Native 0.88.0 and React 19.3.0. It uses React Native core components only, with no third-party chart library. It renders the canonical synthetic OHLCV fixture, candles and volume, horizontal panning, accessible zoom controls, and a text table.

## Scope and limits

- Fixture is synthetic, not historical market data.
- The chart is a lightweight native-View reference, not a production chart library.
- Horizontal scrolling pans; accessible zoom buttons change candle spacing. Physical-device screen-reader checks remain pending.
- It does not connect to exchanges, submit orders or provide investment advice.
- CI generates a lockfile from exact direct dependency pins, runs `npm ci`, and uploads the lock/inventory artifact. Review and commit the generated lock before production use.

## Run locally

```bash
cd pocs/issue-9/react-native
npm install
npm run test:fixture
npx expo start
```
