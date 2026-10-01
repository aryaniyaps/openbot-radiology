# Reusable clinical workspace settings

Use the official OpenMausBot application and its existing profile settings. No custom app build or backend is required. The doctor starts with **Clinical Assistant**, supplies a case identifier and a task, and reviews the result. See the [doctor guide](../../docs/DOCTOR_QUICK_START.md).

## Setup operator

1. Complete the normal app installation and model-provider sign-in. Connect the institution's applications and sign each required role into its assigned read-only account. Keep the doctor's write/sign session separate.
2. Use `role-guidance.json` for each profile's name, title and description. Its standing instructions are the role's `instructions` followed by `shared`. These templates contain no institution, person, patient, application address or deployment identifiers.
3. Designate Clinical Assistant as the native Chief of Staff and pin it. Keep only the roles needed by this installation. For each role, explicitly select its allowed teammates before disabling **Ask me before contacting other bots**. Do not leave future bots implicitly included.
4. Use native **Approve for me** for the six clinical roles and keep the existing bounded browser access. Apply `routine-permissions.json` through the paired IT session with `scripts/operations/apply-routine-permissions.py --apply` while the team is idle. This updates the bot defaults and existing current/internal handoff threads. OpenMausBot 0.1.91 mounts its internal team MCP server for each turn. Do not add a tools-only `mcp_servers.agents` entry to Codex's configuration: without a command or URL, Codex rejects it with `invalid transport`.
5. Record the installation's application addresses and access instructions separately in the role's operator-managed context. Never put passwords in standing instructions or memory. Do not set a default patient. Keep approved formatting preferences optional and specific to the doctor who supplied them.
6. Start a fresh conversation for the doctor, collapse the specialist list, and verify a simple help request and a nonclinical team handoff. Verify current application sign-in separately before handing over the workspace.

The dedicated provider uses its existing ChatGPT login and the app-managed Codex CLI. OpenMausBot mounts the internal team connection and enforces its peer lists. The provider automatically reviews tool permissions, including browser evaluation, within its sandbox. Full access is not enabled. Automatic review is a permission mechanism, not a diagnostic quality check.

## Doctor experience

The assistant routes the requested task to relevant teammates and carries information between them. It asks for missing case information, discrepancies and human decisions. The doctor does not select models, configure connections or approve unfamiliar code as part of ordinary case work.

The official app can still show technical controls and permission cards for requests the provider cannot automatically approve. If one blocks a task, the setup operator must resolve it. Routine coordination and read-only case work are already authorized; clinical decisions and identity discrepancies go to the doctor. Record writes, signing, release and orders remain in the doctor's separate session. Bot creation, history deletion and configuration changes belong to IT. Do not describe this installation as zero-touch or independently diagnostic. New threads preserve earlier history and logs; they are not a data-erasure mechanism.

## Existing installation

The current hospital applications contain synthetic demonstration data. Generalizing the role instructions does not turn that dataset into real patient care or qualify the workflow for production. Historical evidence and records retain their original identities. Previous chat history and case activity logs were backed up privately and removed from the active workspace: this version automatically includes recent chat excerpts even in a new thread, so editing profile instructions alone does not remove old case examples. Archive and clear such context through native controls when repurposing a demo. Current profile snapshots and verification are in `docs/evidence/local-hospital/final-profile-state.json`; private backups preserve the previous profile and memory settings.

The current portable native team backup is [backups/openmausbot.backup.json](../../backups/openmausbot.backup.json). See the root README for import limitations and the private full-system backup.

Native team exports omit execution permissions. After importing the profiles, the operator must configure the six existing teammates/read-only workstations and apply the separate routine-permission policy; importing standing instructions alone does not enable automatic tool review.
