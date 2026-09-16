## Red/Green TDD

For behavior changes and bug fixes:

1. Red: add a focused behavior test and confirm it fails for the expected reason.
2. Green: make the smallest change that passes it; rerun the test.
3. Refactor: keep the test green while cleaning up, then run relevant broader tests.

Skip red only when no practical test boundary exists. Explain why and run the
closest meaningful verification.
