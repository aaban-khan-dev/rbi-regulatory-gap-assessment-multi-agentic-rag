<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Fraud Risk Management Framework

| Field | Value |
|---|---|
| Document ID | KST-RSK-002 |
| Version | 5.1 |
| Owner | Head of Fraud Operations |
| Approved by | Risk Committee of the Board |
| Effective from | 2026-05-01 |
| Last reviewed | 2026-04-09 |
| Next review | April 2027 |

## 1. Purpose

1.1 This framework sets how Kestrel prevents, detects and responds to fraud against customers and against the company. It covers payment fraud, account takeover, mule activity and abuse of promotions. Money-laundering monitoring is covered separately in the KYC, AML and CFT Policy (KST-AML-001).

## 2. Three lines of defence

2.1 **First line.** Product and Engineering build controls into the payment flows; Fraud Operations runs Sentinel and works the alert queues.

2.2 **Second line.** The Enterprise Risk team challenges rule coverage, tracks fraud loss against appetite and reports to the Risk Committee.

2.3 **Third line.** Internal Audit tests the framework annually.

## 3. Sentinel

3.1 Sentinel is Kestrel's real-time decision engine. Every payment, top-up, payee addition, login and profile change passes through Sentinel before Ledger Core posts it. Sentinel returns allow, step-up (ask for an extra authentication factor), hold or decline.

3.2 Rules and thresholds live in the Rules Console. Every change needs a Fraud Operations maker and a separate checker, and is logged with a ticket reference.

3.3 Sentinel combines deterministic rules with a gradient-boosted scoring model retrained monthly on confirmed fraud labels from the case management system.

## 4. Hold periods on fresh accounts, fresh money and fresh payees

4.1 **New wallet.** For the first 24 hours after a Plus wallet is activated, Sentinel blocks sending money to other people or bank accounts and blocks agent or ATM cash-out. Merchant payments are allowed.

4.2 **Fresh top-up.** Money from a top-up can be spent at merchants immediately. It cannot be sent onward or withdrawn as cash until 30 minutes after the top-up posts.

4.3 **New payee.** A newly saved payee stays in a probation state for 4 hours. During probation, transfers to that payee are capped at ₹1,000 in total. The customer gets an SMS and push message the moment a payee is saved, with a one-tap option to remove it.

4.4 Fraud Operations may lengthen any of these holds for a risk segment. They may not shorten them without Risk Committee approval.

## 5. Payment-count ceilings

5.1 Sentinel keeps two rolling counters for every wallet: payments made in the current calendar day, and payments made to each individual payee in the current calendar day.

5.2 Each counter has a ceiling, configured in the Rules Console and differentiated by product and customer risk band. Fraud Operations reviews the ceilings every quarter against the latest fraud patterns.

5.3 When a wallet reaches either ceiling, Sentinel declines further payments of that type for the rest of the day and raises a Tier-2 alert to the Fraud Operations queue.

## 6. Payee additions

6.1 A wallet may add at most five new payees in a calendar day. Additional attempts are declined and raise a Tier-3 alert.

## 7. Alerts and escalation

7.1 **Tier 1:** automated customer contact (SMS or IVR confirmation). **Tier 2:** analyst review within 2 hours. **Tier 3:** analyst review within 30 minutes and a temporary hold on the wallet.

7.2 Confirmed fraud cases are escalated to the Fraud Operations lead. Suspected money laundering is referred to Financial Crime Compliance through the case management system. Cases involving staff or agents are escalated to the Chief Risk Officer.

7.3 Customers are told by SMS when a payment is held for review.

## 8. Customer-set controls

8.1 Customers can set their own daily caps on the number and value of payments, separately for merchant payments, transfers and cash-out. Raising a cap requires PIN plus one-time code re-entry.

## 9. Mule detection

9.1 Sentinel scores wallets for mule behaviour: many small inbound transfers from unrelated senders followed by rapid cash-out, new devices, and shared device fingerprints across wallets. High scores raise a Tier-3 alert and are referred to Financial Crime Compliance.

## 10. Loss reporting

10.1 Fraud Operations reports gross and net fraud loss monthly to the Chief Risk Officer and quarterly to the Risk Committee, against the loss-appetite metrics approved by the Board.
