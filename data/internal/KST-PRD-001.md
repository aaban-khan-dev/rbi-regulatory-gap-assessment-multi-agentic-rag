<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Wallet Product and Limits Policy

| Field | Value |
|---|---|
| Document ID | KST-PRD-001 |
| Version | 4.2 |
| Owner | Head of Product |
| Approved by | Board of Directors |
| Effective from | 2026-04-01 |
| Last reviewed | 2026-03-18 |
| Next review | March 2027 |

## 1. Purpose and scope

1.1 This policy defines the stored-value products KestrelPay offers, who may hold them, how money may enter and leave them, and the hard ceilings the platform enforces. It is the single reference for every cap configured in the Rules Console.

1.2 It covers KestrelPay Lite, KestrelPay Plus and the KestrelPay Card. It does not cover merchant acquiring, which is governed by the Merchant Services Policy.

1.3 Any cap in this policy may be made stricter by Fraud Operations for a customer segment under the Fraud Risk Management Framework (KST-RSK-002). No team may configure a cap that is looser than the figures below.

## 2. Product catalogue

2.1 **KestrelPay Lite.** An entry-level wallet opened with a mobile number confirmed by one-time code and a self-declared name and identity-document number. Lite can only be spent at merchants on the KestrelPay acceptance network. It cannot send money to other people, to bank accounts, or be cashed out.

2.2 **KestrelPay Plus.** A wallet for customers whose identity has been fully established under the KYC, AML and CFT Policy (KST-AML-001). Plus can pay merchants, send money to saved payees, pay any UPI ID through the Kestrel UPI handle, and be cashed out at agents or ATMs.

2.3 **KestrelPay Card.** A RuPay-network prepaid card, issued as a virtual card on request and as a chip-and-PIN plastic card for a fee. The card draws on the linked Plus wallet balance; it has no balance of its own.

2.4 No product pays interest, cashback-as-yield, or any return linked to the balance held. Promotional cashback is a marketing expense and is governed by the Promotions Standard.

## 3. How money comes in

3.1 **Funding channels for Lite.** A Lite wallet can only be topped up from a bank account (UPI, net banking, debit card), a credit card, or the customer's own Plus wallet. Cash top-ups are blocked for Lite at the agent terminal and in Sentinel.

3.2 **Lite inflow ceilings.** Ledger Core keeps two running counters for every Lite wallet: credits in the current calendar month and credits in the current April-to-March year. Sentinel declines any top-up that would take the monthly counter past ₹10,000 or the yearly counter past ₹1,20,000. The Lite balance itself can never go above ₹10,000.

3.3 **Plus balance ceiling.** A Plus wallet's ledger balance is capped at ₹2,00,000. Any top-up or incoming transfer that would lift the balance above this figure is rejected in full, never part-applied. The only credits allowed to breach the ceiling are reversals of the customer's own earlier wallet payments (failed or cancelled merchant transactions).

3.4 **Cash top-ups.** Plus customers can add cash at Kestrel Points outlets. Ledger Core aggregates every cash-funded credit per customer per calendar month, across all outlets. Once the month's cash-funded credits reach ₹50,000, Sentinel declines further cash top-ups until the first day of the following month. This counter never increases the wallet's ₹2,00,000 balance ceiling; both checks apply.

3.5 Top-ups in any currency other than Indian rupees are rejected.

## 4. How money goes out

4.1 **Merchant spends.** There is no separate cap on merchant spends; they are bounded only by the available balance and by Fraud Operations rules.

4.2 **Transfers to saved payees.** A Plus customer can save up to the number of payees fixed in KST-RSK-002. Transfers to any single saved payee are capped at ₹2,00,000 per calendar month. Customers can choose a lower personal cap in the app.

4.3 **Transfers to unsaved recipients.** Transfers to a recipient that is not a saved payee are capped at ₹10,000 per calendar month in total.

4.4 **Cash-out.** Plus balances can be withdrawn as cash through two channels. Each channel has its own counter in the Rules Console:

| Channel | Per withdrawal | Per calendar month |
|---|---|---|
| Kestrel Points agent cash-out | ₹2,000 | ₹10,000 |
| ATM withdrawal with KestrelPay Card | ₹2,000 | ₹10,000 |

4.5 The two monthly counters are maintained and reset independently on the first day of each month. A withdrawal in one channel does not reduce the allowance available in the other.

4.6 Lite balances can never be withdrawn as cash or sent to anyone. On closure, the Lite balance is returned to the bank account or card it came from.

## 5. Closure and balance return

5.1 Customers may close any wallet whenever they like, from the app or through CareDesk. For Plus, the customer nominates a bank account in their own name, confirmed by a ₹1 penny-drop name match, to receive the balance.

5.2 Balances on closed or expired wallets are never moved into Kestrel's income. Treasury Operations holds them as customer liabilities until claimed, as described in KST-FIN-003.

## 6. Disclosures

6.1 Before a customer's first top-up, Notify sends a plain-language product summary by SMS and in-app message listing the applicable caps, fees and validity terms in the customer's app language, with English and Hindi versions always available.

6.2 The fee schedule is published in the app, on the website, and at every Kestrel Points outlet.

## 7. Governance

7.1 The Product Council approves any change to Rules Console caps. The change is logged with a ticket reference, and Internal Audit samples these changes each quarter.

7.2 The Board reviews this policy every twelve months and whenever the regulatory framework for prepaid instruments changes.
