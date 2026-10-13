<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Periodic KYC Refresh SOP

| Field | Value |
|---|---|
| Document ID | KST-AML-006 |
| Version | 2.0 |
| Owner | Head of KYC Operations |
| Approved by | Principal Officer |
| Effective from | 2024-04-01 |
| Last reviewed | 2025-03-14 |
| Next review | March 2026 (overdue) |

## 1. Purpose

1.1 Customer details go out of date. This SOP sets how often KestrelPay Plus customers must confirm or update their KYC details, and what happens if they do not.

## 2. Refresh interval

2.1 The refresh date is calculated from the date of onboarding or the last completed refresh, whichever is later, according to the customer's risk band:

| Risk band | Refresh due after |
|---|---|
| H | 24 months |
| M | 96 months |
| L | 120 months |

2.2 A move to a higher band brings the refresh date forward to the date the new band would give.

## 3. How customers refresh

3.1 **Nothing has changed.** The customer confirms this in the app (Profile, then Confirm my details). The confirmation is authenticated with the device key and PIN.

3.2 **Only the address has changed.** The customer enters the new address in the app. KYC Operations confirms it within 60 days by sending a confirmation code by post to the new address.

3.3 **Anything else has changed, or documents have expired.** The customer goes through the full Plus verification again (KST-AML-004 section 3).

3.4 KYC Operations checks the customer's PAN against the Income Tax Department's service at every refresh. The customer receives an in-app confirmation with the date their details were updated.

## 4. Customer reminders

4.1 Thirty days before the refresh date, Notify sends one push notification and one in-app banner asking the customer to refresh.

## 5. Missed refresh

5.1 If the refresh is not completed by the due date, Ledger Core pauses all outgoing payments from the wallet, whatever the customer's risk band. Incoming credits and the customer's ability to complete the refresh are not affected.

5.2 The pause lifts automatically once the refresh is complete.

## 6. Customer duty to update

6.1 The terms and conditions require customers to tell Kestrel within 30 days whenever any of their identity or address documents change.

## 7. Monitoring

7.1 KYC Operations reviews a weekly report of refreshes due, completed and overdue.
