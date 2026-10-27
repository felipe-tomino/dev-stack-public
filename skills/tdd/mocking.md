# Dependency substitutes

Use when a test needs to control a dependency. Follow the repository's permitted seams: prefer its real/emulated database and endpoint path, with substitutes at approved process boundaries such as external payment/email APIs.

Do not mock owned in-process behavior or replace a required real/emulated path with a mocked DAO. Approved database assertions after a real endpoint remain valid; a database dependency alone does not justify a fake.

Use existing controls for time, randomness and filesystem behavior. A substitute should drive a meaningful outcome, including boundary failures, rather than merely echo the expected result.

Reuse the existing external contract. Where a real design need calls for injection, a function parameter can suffice; do not create an SDK, port or wrapper solely for mock convenience. Keep substitutes faithful to the relevant input, result, error and ordering guarantees.

If the test can only prove interactions with its own fake, reconsider the seam. [tests.md](tests.md) illustrates outcome assertions; [SKILL.md](SKILL.md) owns the loop.
