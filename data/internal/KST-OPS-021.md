<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Dormant Wallet Lifecycle SOP

| Field | Value |
|---|---|
| Document ID | KST-OPS-021 |
| Version | 1.4 |
| Owner | Head of Customer Operations |
| Approved by | Chief Operating Officer |
| Effective from | 2026-03-01 |
| Last reviewed | 2026-02-11 |
| Next review | February 2027 |

## 1. Purpose

1.1 Wallets that nobody uses are a fraud target: they can be taken over without the owner noticing. This SOP sets when a wallet becomes dormant, how the customer is told, and how a dormant wallet is brought back to life.

## 2. Definitions

2.1 **Money movement:** any customer-initiated debit or credit posted to Ledger Core. Fee postings, promotional credits and system adjustments do not count.

2.2 **Dormant wallet:** a Lite or Plus wallet with no money movement for 365 consecutive days.

## 3. Lifecycle

3.1 **Day 335 without money movement.** Notify sends a dormancy warning by SMS, push notification and, where held, email. The warning tells the customer that the wallet will be frozen in 30 days unless they use it, and that their balance remains safe.

3.2 **Day 365.** The nightly Ledger Core job moves the wallet to state DORMANT. All debits and credits are blocked. The balance remains a customer liability and stays inside the safeguarding calculation in KST-FIN-003.

3.3 **Day 365, after the job runs.** Notify sends a second message confirming the freeze and explaining how to reactivate.

## 4. Reactivation

4.1 A dormant wallet is reactivated only after the customer completes re-verification in Onboard:
- a fresh one-time code to the registered mobile number;
- a selfie with liveness check matched against the photograph on file;
- for Plus wallets, a fresh retrieval of the customer's record from CKYCR or a DigiLocker document pull, compared field by field with the record on file.

4.2 Any mismatch sends the case to KYC Operations for manual review. No reactivation goes ahead until the review closes.

4.3 Requests to change the registered mobile number at the same time as reactivation are refused. The customer must reactivate first, then follow the mobile-change process in KST-SEC-007.

## 5. Validity and expiry

5.1 Wallets stay valid for a minimum of twelve months after the most recent top-up. Expiry warnings are sent by Notify, in the customer's chosen language, at several points during the 45 days before expiry.

5.2 Balances on expired wallets are never written back to Kestrel's income. Customers can claim them at any time, and they are paid to a bank account in the customer's name.

## 6. Reporting

6.1 Customer Operations produces a monthly dormancy report for the COO: number of wallets turned dormant, the total balance held in them, and reactivations with their outcome.

6.2 The Risk Committee receives the dormancy figures each quarter as part of the operational risk dashboard.
