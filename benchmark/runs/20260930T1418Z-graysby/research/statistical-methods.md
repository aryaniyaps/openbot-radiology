# Statistical methods provenance — 2026-09-30

Development implementation, not results: binary_metrics.py uses the two-sided Wilson proportion interval from [NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm), and an exact symmetric binomial discordance test consistent with [statsmodels McNemar documentation](https://www.statsmodels.org/dev/generated/statsmodels.stats.contingency_tables.mcnemar.html). Seven synthetic validation cases pass known values and reconciliation invariants. Failure handling, zero-denominator nulls and missing-cost handling are separate benchmark conventions.

These functions do not establish clinical accuracy, provide equivalence testing, implement stratified design inference or yet implement paired difference confidence intervals. Clinical review and design-specific analysis remain required. No diagnostic records have been scored.
