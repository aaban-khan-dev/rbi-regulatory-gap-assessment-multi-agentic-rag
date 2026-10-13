<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Records Retention Schedule

| Field | Value |
|---|---|
| Document ID | KST-DAT-002 |
| Version | 2.6 |
| Owner | Head of Data Governance |
| Approved by | Board of Directors |
| Effective from | 2026-04-01 |
| Last reviewed | 2026-03-05 |
| Next review | March 2027 |

## 1. Purpose

1.1 This schedule sets how long each class of Kestrel record is kept, where, and when it is destroyed. Keeping records too briefly breaks legal duties; keeping them too long increases privacy risk and storage cost.

## 2. Principles

2.1 Records needed for legal, regulatory or audit purposes are moved to Vault, Kestrel's write-once archive in Indian data centres, when they leave the live system. Records in Vault cannot be altered or deleted before their retention period ends.

2.2 Records under a legal hold (litigation, investigation, regulator request) are kept until Legal releases the hold, whatever the schedule says.

2.3 When a retention period ends, records are destroyed by the quarterly purge job. Data Governance signs off each purge.

2.4 Records must be retrievable within 48 hours of a request from a competent authority.

## 3. Schedule

| Record class | System of record | Kept for | Clock starts |
|---|---|---|---|
| Wallet ledger postings and payment messages (all top-ups, payments, transfers, cash-outs, with amount, currency, date, counterparties and channel) | Ledger Core, then Vault | 5 years | Date of the transaction |
| Customer identity and address records, document images, V-CIP recordings and activity logs | Onboard, then Vault | 5 years | Date the customer relationship ends |
| Sanctions and PEP screening results and analyst decisions | Watchlist Hub, then Vault | 5 years | Date the customer relationship ends |
| Suspicious activity case files and reports filed with FIU-IND | FCC case system | 5 years | Date of filing |
| Daily safeguarding positions and auditor certificates | TreasuryDesk | 8 years | End of the financial year |
| Complaint tickets and disputed-transaction cases | CareDesk | 5 years | Date the ticket is closed |
| Notify delivery receipts for alerts | Notify, then Vault | 3 years | Date of delivery |
| Kestrel Points outlet vetting files | Agent Portal | 5 years | Date the outlet is exited |
| Application and security logs | SOC data lake | 2 years | Date of the event |

3.1 **Basis.** The 5-year periods for transaction and identity records follow the record-keeping rules under PMLA 2002. They apply to every product.

## 4. Responsibilities

4.1 Every system owner confirms each year that their system follows this schedule. Internal Audit tests a sample of record classes each year.
