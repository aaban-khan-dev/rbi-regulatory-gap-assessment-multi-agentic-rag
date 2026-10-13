<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Security Incident Response Plan

| Field | Value |
|---|---|
| Document ID | KST-SEC-012 |
| Version | 2.0 |
| Owner | Chief Information Security Officer |
| Approved by | IT Steering Committee |
| Effective from | 2023-06-01 |
| Last reviewed | 2024-05-14 |
| Next review | May 2025 (overdue) |
| Regulatory basis | RBI Master Direction on Digital Payment Security Controls, 2021, paragraph 40 |

## 1. Purpose

1.1 This plan sets how Kestrel detects, contains, recovers from and learns from security incidents affecting the payment platform. Its structure follows paragraph 40 of the RBI Master Direction on Digital Payment Security Controls (2021), which Kestrel adopted as its benchmark for incident handling when this plan was first written.

## 2. Severity levels

| Severity | Description | Response start |
|---|---|---|
| Sev-1 | Confirmed compromise of customer funds or data, or full platform outage | 15 minutes |
| Sev-2 | Suspected compromise, or partial outage of a payment channel | 1 hour |
| Sev-3 | Contained event with no customer impact | Next business day |

## 3. Incident Response Team

3.1 The CISO leads. Core members: the SOC shift lead, the Head of Platform Engineering, the Head of Fraud Operations, the Legal counsel on duty and the Head of Customer Experience.

3.2 For Sev-1 the CEO is informed within one hour, and the Chair of the Risk Committee within 24 hours.

## 4. Stakeholder contact register

4.1 The Security Governance team maintains a contact register of everyone Kestrel may need during an incident: the sponsor bank, the escrow bank, the card network, the UPI switch operator, cloud providers, the managed SOC partner, the SMS gateway, and peer wallet issuers.

4.2 Every entry is verified by phone or email every six months. Each counterparty is asked to confirm or update its contact details, and the verification date is recorded.

## 5. Playbooks

5.1 Kestrel maintains written playbooks for the payment-ecosystem incidents most likely to cause customer loss:
- account takeover at scale;
- credential stuffing against login;
- compromise of an agent terminal or the Agent Portal;
- fraudulent API calls from a partner;
- leakage of customer data;
- ransomware on corporate IT.

5.2 Each playbook names the containment steps, the counterparties to contact from the register, and the actions that limit loss to customers or to Kestrel (for example, freezing affected wallets or pausing a channel in Sentinel).

## 6. Phases

6.1 **Detect:** SOC alert, Sentinel anomaly, staff report or customer report.

6.2 **Contain:** isolate affected systems, revoke credentials, pause channels.

6.3 **Eradicate and recover:** remove the root cause, restore from clean backups, monitor closely for 72 hours.

6.4 **Notify customers:** affected customers are told by SMS and email what happened and what to do, once Legal and the CISO approve the wording.

## 7. Post-incident review

7.1 Every Sev-1 and Sev-2 incident has a blameless post-incident review within 10 working days. Actions are tracked in the risk register under KST-SEC-001.

## 8. Testing

8.1 The plan is exercised through a tabletop exercise every six months, alternating between a fraud scenario and a data-breach scenario.
