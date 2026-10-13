<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Customer Onboarding and CKYCR SOP

| Field | Value |
|---|---|
| Document ID | KST-AML-004 |
| Version | 4.0 |
| Owner | Head of KYC Operations |
| Approved by | Principal Officer |
| Effective from | 2025-05-01 |
| Last reviewed | 2025-04-22 |
| Next review | April 2026 (overdue) |

## 1. Purpose

1.1 This SOP describes, step by step, how a person becomes a KestrelPay customer in Onboard and how their KYC record reaches the central registry. It implements sections 4 and 5 of the KYC, AML and CFT Policy (KST-AML-001).

## 2. Lite wallet

2.1 The applicant enters their mobile number and confirms it with a one-time code.

2.2 The applicant types their name and selects one identity document type (Aadhaar, passport, driving licence, voter ID, PAN or NREGA job card) and enters its number. No document image is collected.

2.3 Watchlist Hub screens the name. Onboard checks that the mobile number and identity number have not been used for a previous Lite wallet.

2.4 The product summary is sent by SMS before the first top-up.

## 3. Upgrading to Plus

3.1 The app offers three routes, in this order:
- **Video verification (V-CIP).** A live video call with a Kestrel KYC officer (section 4). Offered first to every applicant.
- **DigiLocker.** The applicant authorises a pull of their Aadhaar or driving licence and their PAN from DigiLocker.
- **CKYCR download.** The applicant gives their KYC identifier and consents to Kestrel downloading their record from the central registry.

3.2 For every route, Onboard sends the document images and the live selfie to VeriDoc, our document-verification vendor. VeriDoc returns authenticity, face-match and liveness results. PAN is verified against the Income Tax Department's service.

3.3 Watchlist Hub screens the applicant against sanctions and PEP data before activation (see KST-AML-009 and KST-AML-001).

3.4 Applicants using the DigiLocker or CKYCR routes start in risk band M with the 180-day "New Remote" watch described in KST-AML-001.

## 4. Video verification calls

4.1 **Runbook.** KYC Operations keeps a written V-CIP runbook that scripts every step of the call, from greeting to the final decision screen. Officers follow it step by step, and any departure is logged in Onboard against the session with a reason.

4.2 **Who runs calls.** Only KYC officers who have passed Kestrel's V-CIP certification course, and the yearly refresher, can take a call. Onboard checks the certification flag at login and refuses the call to anyone else.

4.3 **Liveness and spoof check.** During the call the officer asks the applicant to turn their head left and right, blink twice, and read aloud a random four-digit number shown on screen. The officer watches for replayed video, masks, a second person prompting off-camera, or a screen held up to the lens. If they see any of these, they end the call and mark the session as suspected fraud.

4.4 Applicants who cannot complete the head-turn, blink and read-aloud prompts after two attempts are declined on the video route and may try again after 30 days.

4.5 Every session is recorded, geo-tagged and time-stamped, and stored in Vault in India. A second KYC officer audits each session before the Plus wallet is switched on.

## 5. Central KYC Records Registry

5.1 Once a Plus wallet is live, KYC Operations must send the customer's complete KYC record set (the individual template, document images and photograph) to the CKYC registry run by CERSAI. Records travel in the nightly CERSAI batch file.

5.2 The hard deadline is the tenth calendar day after the Plus wallet goes live. Onboard's ageing report flags every pending record at day 7. The KYC Operations lead clears anything flagged by day 9.

5.3 When the registry returns the customer's KYC identifier, Notify texts the identifier to the customer.

5.4 Records the registry bounces back are corrected and resent inside two business days, and the tenth-day deadline still applies.

## 6. Quality checks

6.1 KYC Operations quality-checks a 5% random sample of activated Plus wallets every week. Errors are fed back to the officers concerned and to the VeriDoc account manager.
