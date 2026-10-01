# Imaging benchmark delivery

The completed investigation is in [the decision report](runs/20260930T1418Z-graysby/DECISION-REPORT.md), with [the requirement audit](runs/20260930T1418Z-graysby/REQUIREMENT-AUDIT.md) and [reproduction guidance](runs/20260930T1418Z-graysby/DELIVERY-README.md). All 970 frozen assignments have terminal results; 919 qualified.

The committed package contains reports, aggregate audits, charts, the frozen protocol, research provenance and analysis scripts. `delivery-checksums.sha256` verifies its 90 original artifacts. Protected reference reports, source images, model weights, account state and full native traces are retained locally and excluded through an explicit file allowlist. Local regeneration requires the retained inputs and curator access described in the delivery guide. This Git package is not a self-contained replay of diagnostic inference.

Verify the delivered artifacts without running models:

```sh
cd benchmark/runs/20260930T1418Z-graysby
sha256sum -c delivery-checksums.sha256
```
