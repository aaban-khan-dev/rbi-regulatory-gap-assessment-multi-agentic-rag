<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Customer Authentication Standard

| Field | Value |
|---|---|
| Document ID | KST-SEC-007 |
| Version | 3.2 |
| Owner | Chief Information Security Officer |
| Approved by | IT Steering Committee |
| Effective from | 2026-02-15 |
| Last reviewed | 2026-02-02 |
| Next review | February 2027 |

## 1. Purpose

1.1 This standard sets how KestrelPay proves that the person operating a wallet is its owner, at login and when money leaves the wallet. It implements section 4.1 of the Information Security Policy (KST-SEC-001) for customer-facing channels.

## 2. Credentials Kestrel uses

2.1 **Device binding key.** At registration, the app generates a key pair inside the phone's secure hardware and registers the public key with Onboard against the customer's verified mobile number. The binding is tied to the SIM: if the SIM changes, the binding is revoked.

2.2 **Kestrel PIN.** A 4 to 6 digit secret chosen by the customer. It is never stored in clear text; the platform holds only a salted hash.

2.3 **On-device biometric.** Fingerprint or face unlock, used only to release the device binding key, never sent to Kestrel.

2.4 **One-time code.** A six-digit code sent by Notify to the registered mobile number, valid for 3 minutes.

## 3. Login

3.1 App login requires the device binding key plus either the PIN or the on-device biometric.

3.2 Five consecutive wrong PIN entries lock the wallet for 24 hours. Unlocking requires a one-time code plus selfie liveness. The customer is notified by SMS after the third wrong attempt and again on lockout.

3.3 Sessions end after 5 minutes of inactivity and whenever the app is sent to the background for more than 60 seconds. A logout button is always visible on the home screen.

## 4. Money leaving a wallet

4.1 Every instruction that reduces a Lite or Plus wallet balance must be approved with two independent proofs belonging to different categories:
- something the customer has: the device binding key on their enrolled phone; and
- something the customer knows or is: the Kestrel PIN or the on-device biometric.

4.2 This applies without exception to merchant payments, sending money to people, transfers to bank accounts, UPI payments from the wallet, and agent cash-out.

4.3 **Agent cash-out.** The customer approves the withdrawal on their own phone with the device key plus PIN. The outlet enters a one-time code that the customer reads out from the approval screen. The outlet can never complete a withdrawal alone.

4.4 Sentinel rejects any debit request that does not carry both proofs, whatever the channel.

## 5. KestrelPay Card

5.1 Card transactions follow the same additional-authentication rules that the RuPay network and RBI apply to bank debit cards: PIN at ATMs and point-of-sale terminals, and a one-time code for online card-not-present payments.

## 6. Sensitive profile changes

6.1 Changing the registered mobile number, email, PIN or nominated bank account requires the device key, the PIN and a selfie liveness match. The old mobile number is notified. Outgoing transfers are blocked for 24 hours after any such change.

## 7. Shared login

7.1 KestrelPay uses one login for the wallet and the Kestrel Rewards service. Customers are told this by email and in-app notice when they register.
