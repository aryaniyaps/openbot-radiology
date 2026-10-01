# Doctor workspace access

Open **Radiology Assistant** from the local application launcher, or [the doctor worklist](https://doctor.radiology.demo/worklist/). Login details are in `.private/HOSPITAL-DEMO-ACCESS.txt` on this machine. Start with a practice case, review its chart and full supplied study, and choose **Prepare this case**.

The native assistant receives a visible case summary and labelled image packet. It obtains an independent image read and report check, then returns a provisional report. Review and edit it before saving **Radiology Notes** in Bahmni. The assistant cannot save, sign, release or place orders under the configured clinical workflow.

The doctor gateway permits native case conversations and one-shot handoff review. It blocks configuration, SOUL/profile/model changes, execution overrides, permanent permissions and administrator pairing. Presentation controls hide technical settings; actual restrictions are enforced separately by native client scope and the root-managed doctor boundary.

[Hospital deployment guide](HOSPITAL-DEPLOYMENT.md) contains the five practice cases, doctor steps, IT ownership, recovery and verified limitations. [Current evidence](evidence/hospital-deployment/) covers the TLS IT-server deployment. Evidence under `evidence/doctor-workspace/` records the earlier localhost-only setup and is historical.

This is a shared synthetic practice workspace. It does not add individual SSO or per-patient history isolation. Keep the owner desktop and raw native backend restricted to IT. Clinical drafts require physician review.
