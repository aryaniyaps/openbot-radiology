---
name: radiology-case-workup
description: Prepare a sourced radiology case context, study/prior inventory and current workflow status from configured read-only hospital applications.
---

Resolve the requested patient and accession in the current chart and imaging source. Check encounter and acquisition dates separately. Stop on mismatched identities; do not reconcile them by guessing.

Collect the indication, relevant symptoms, known diagnoses, procedures, laboratory data and prior imaging that can change interpretation. Preserve source, date and whether information predates imaging. Flag contradictions and unreadable documents. Do not copy unrelated history or outcomes into the interpretation context.

Inventory available studies, modality, anatomy, series, views and priors. Distinguish acquired, available, actually opened and inspected. Missing comparison means no supported interval-change claim. In a blinded research workflow, the current reference report, teaching-case answer and post-imaging outcomes are excluded; do not search for them.

Pass a concise case packet to the relevant teammate: verified identifiers, indication, dated source facts, available study/prior references and unresolved questions. Do not invent teammate results. For a status request, inspect the current native record and distinguish drafted, saved, reviewed, signed and released states. A successful message or handoff is not clinical completion.

Provide the doctor one concise result and the decision or source information still required. Keep application setup and permission recovery operator-facing. Use assigned read-only accounts; no record changes or external communication.

Provenance: existing native OpenMausBot radiology workflow and project frontier evaluation requirements, 2026-10-01.
