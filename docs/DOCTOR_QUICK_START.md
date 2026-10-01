# Doctor quick start

Open **Radiology Assistant** from the local application launcher or [the practice worklist](https://doctor.radiology.demo/worklist/). Read `.private/HOSPITAL-DEMO-ACCESS.txt` for the separate gateway and hospital-record logins.

1. Choose a DX, CT, MRI, ultrasound or mammography case.
2. Open **Patient record** and **Review images**. Confirm the patient and accession and review the full supplied series.
3. Inspect the assistant packet and its stated sampling limits. Choose **Prepare this case** to start a fresh native Clinical Assistant conversation.
4. Allow the requested teammate handoffs once. Sol prepares the draft; Astra reads the assigned images and checks the proposal. Keep uncertainty and missing coverage explicit.
5. Review and edit the proposal yourself. Open **Write / save report**, expand the order, enter the reviewed text in **Radiology Notes**, and choose **Save**. Reload to verify persistence.

Start with **PRACTICE002 / ORD-23** for a fresh CT case. **PRACTICE001 / ORD-22** is used for the recorded save/reload rehearsal and may already contain a clearly labelled provisional practice note. Native assistant history is shared in this practice workspace. No clinician certification, report signing/release or complete-examination reliability is claimed.

[Full deployment guide](HOSPITAL-DEPLOYMENT.md) explains all five cases, IT management and recovery. Earlier five-modality workflow videos remain at [hospital demonstrations](https://radiology.demo/demos/).
