# Issue 9 Expo CLI dependency audit finding and disposition

**Date:** 2026-10-24  
**Initial run:** [40059144482](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059144482)  
**Scope:** first, discarded Expo-based React Native reference; these findings are not attributed to the current bare React Native candidate without its own audit result.

## Finding

The first React Native prototype used Expo SDK 58.0.17. `npm audit --audit-level=high` reported five high-severity advisories, including:

- `node-forge@1.4.0`, pulled through Expo CLI and `@expo/code-signing-certificates`. GitHub advisory [GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv) reports affected versions through 1.4.0 and lists no patched version in the advisory record available on 2026-10-24.
- `zod@3.25.76`, pulled through Expo CLI. GitHub advisory [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5) identifies a high-severity resource-consumption issue and indicates a fix in Zod 4.6.6 or later. Expo CLI's declared range was `^3.25.76`, so forcing a major-version override without compatibility tests would be unsafe.

The audit suggested `npm audit fix --force` would downgrade Expo to 44.0.6. That is a destructive downgrade and was not applied.

## Disposition

The candidate was changed to the bare React Native Community CLI scaffold, without Expo CLI. This avoids the specific Expo CLI dependency chain rather than silently suppressing the findings or forcing an incompatible downgrade. The bare candidate's own `npm audit --audit-level=high` and build workflows must complete before this disposition can be considered verified.

## Security boundary

The findings were in build/development tooling dependencies. They are not automatically proof that the generated application runtime is exploitable; however, they are material to developer workstations and CI execution and therefore block approval of the Expo-based candidate until a compatible remediation exists. No exception is granted for production use.

## References

- [GitHub Advisory Database: node-forge GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv)
- [GitHub Advisory Database: Zod GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5)
- [Official React Native: Get Started Without a Framework](https://reactnative.dev/docs/getting-started-without-a-framework)
