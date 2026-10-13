<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Escrow Safeguarding and Reconciliation Procedure

| Field | Value |
|---|---|
| Document ID | KST-FIN-003 |
| Version | 2.3 |
| Owner | Head of Treasury Operations |
| Approved by | Chief Financial Officer |
| Effective from | 2026-02-01 |
| Last reviewed | 2026-01-22 |
| Next review | January 2027 |

## 1. Purpose

1.1 Customer money held in KestrelPay wallets does not belong to Kestrel. This procedure makes sure that, every night, there is enough money ring-fenced at our partner bank to pay every customer and every merchant we owe.

1.2 It applies to Treasury Operations, Finance, and the engineering team that maintains TreasuryDesk.

## 2. Accounts

2.1 **Safeguarding Account.** Customer money is held in an escrow account at our partner scheduled bank, opened under a tripartite agreement that limits its use to the purposes listed in section 5. Kestrel may open a second escrow account at a different scheduled bank with CFO approval. If it does, both accounts are treated as one pool for the nightly test in section 3.

2.2 **Operating Account.** Kestrel's own money. It never receives customer money, except to cover a safeguarding deficit under paragraph 3.4.

## 3. Nightly safeguarding cycle

3.1 Every inflow that adds money to a customer wallet (app top-ups, card top-ups, cash collected by Kestrel Points outlets) must be swept into the Safeguarding Account on the same working day it is posted to Ledger Core. Agent cash collected after the bank's cut-off is swept before the cut-off on that day using the intraday prefunding line, never the next morning.

3.2 At 21:00 every night, TreasuryDesk calculates the nightly position:
- **Liability:** the total of all customer wallet balances in Ledger Core, plus amounts owed to merchants that have not yet been paid out.
- **Safeguarded:** the 21:00 bank balance in the Safeguarding Account(s), excluding any money held with RBI.

3.3 If Safeguarded is at least equal to Liability, TreasuryDesk records a green result, and the Treasury Operations analyst on duty signs it off before 22:00.

3.4 If Safeguarded is below Liability, the analyst raises a P1 alert. Treasury Operations moves the deficit across from the Operating Account the same evening. The Head of Treasury emails the RBI DPSS regional office about the deficit that same evening, copying the Chief Compliance Officer. A deficit is never carried overnight without that notification.

3.5 Sign-offs, alerts and notifications are retained in TreasuryDesk for the period set in the Records Retention Schedule (KST-DAT-002).

## 4. Interest-bearing core portion

4.1 With CFO approval, Treasury may place the stable core of the safeguarded balance in a linked interest-bearing deposit at the same bank. The core is calculated from the lowest balance seen in each fortnight over the preceding 26 fortnights. The linked deposit stays available to meet any deficit, carries no lien, and is never borrowed against.

## 5. Permitted movements

5.1 TreasuryDesk allows only these debits from the Safeguarding Account: merchant settlements, payments to the sponsor bank for UPI and card network settlement, refunds to the original funding source, taxes collected with top-ups, Kestrel's pre-agreed fees and commissions moved to the designated Kestrel account at a fixed frequency, and debits ordered by a court, regulator or law-enforcement agency.

5.2 Any other debit request is blocked by the bank under the tripartite agreement.

5.3 Merchants paid through marketplace or aggregator partners appear on the payee list we share with the partner bank. We update this list weekly.

## 6. Auditor certification

6.1 Kestrel's statutory audit firm certifies, every quarter, that the safeguarded balance covered the liability on every day of the quarter, using the format prescribed by RBI. The same firm audits both escrow accounts where two are held, and the certificate covers both.

6.2 Treasury Operations files the quarterly certificate with the RBI DPSS regional office within 30 days after each quarter.

6.3 An annual certificate covering the full financial year is obtained from the same firm and filed alongside the statutory accounts.

## 7. Records available on demand

7.1 TreasuryDesk keeps the nightly liability-versus-safeguarded position for every date in a form that can be handed to RBI or the partner bank on request.

## 8. Moving the Safeguarding Account

8.1 Moving the Safeguarding Account to another bank requires Board approval, a written migration plan that keeps merchant payment cycles uninterrupted, and prior written intimation to RBI.
