# Imaging benchmark delivery

For leadership review, read the [executive PDF](../output/pdf/Imaging-Benchmark-Executive-Report.pdf). It summarizes the audited evidence in seven pages with vector charts, decisions, limitations and linked source artifacts. To rebuild it, install `reportlab==5.0.1` in an isolated Python environment and run `python scripts/operations/build-executive-report.py` from the repository root. The builder uses system Lato fonts and verifies the original artifact checksums before rendering; it makes no diagnostic calls.

The completed investigation is in [the decision report](runs/20260930T1418Z-graysby/DECISION-REPORT.md), with [the requirement audit](runs/20260930T1418Z-graysby/REQUIREMENT-AUDIT.md) and [reproduction guidance](runs/20260930T1418Z-graysby/DELIVERY-README.md). All 970 frozen assignments have terminal results; 919 qualified.

The committed package contains reports, aggregate audits, charts, the frozen protocol, research provenance and analysis scripts. `delivery-checksums.sha256` verifies its 90 original artifacts. Protected reference reports, source images, model weights, account state and full native traces are retained locally and excluded through an explicit file allowlist. Local regeneration requires the retained inputs and curator access described in the delivery guide. This Git package is not a self-contained replay of diagnostic inference.

Verify the delivered artifacts without running models:

```sh
cd benchmark/runs/20260930T1418Z-graysby
sha256sum -c delivery-checksums.sha256
```
