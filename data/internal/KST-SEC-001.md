<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Information Security Policy

| Field | Value |
|---|---|
| Document ID | KST-SEC-001 |
| Version | 6.0 |
| Owner | Chief Information Security Officer |
| Approved by | Board of Directors |
| Effective from | 2026-04-01 |
| Last reviewed | 2026-03-26 |
| Next review | March 2027 |

## 1. Purpose and authority

1.1 This is Kestrel's top-level security policy. The Board adopts it and has delegated day-to-day ownership to the CISO. Every security standard and runbook in the company (KST-SEC-007, KST-SEC-012, KST-SEC-015 and the engineering hardening baselines) derives from it.

1.2 It applies to every employee, contractor and vendor with access to Kestrel systems or customer data, and to every environment: production, staging, corporate IT and cloud.

## 2. Security objectives

2.1 Customer money and data are protected from unauthorised access, alteration and loss.

2.2 The payment platform (Ledger Core, Sentinel, Onboard, the UPI switch interface and the card processor interface) stays available within the targets in the Business Continuity Plan.

2.3 Kestrel can show, on any day, which controls exist and whether they are working.

## 3. Risk-based control set

3.1 The CISO maintains a register of information security risks and the controls that treat them, mapped to ISO/IEC 27001 Annex A.

3.2 **When the control set is reassessed.** The CISO reassesses the risk register and the controls against it:
- (a) on a fixed annual cycle, with the results presented to the Risk Committee every fourth quarter;
- (b) within 30 days after any Severity-1 or Severity-2 security event is closed, whether or not customer data was affected;
- (c) as a gate in the Release Board process. Any release classed Tier A (new data store, new external interface, network re-architecture, or rework of authentication flows) needs a security design sign-off before go-live and a control effectiveness check within two weeks after go-live.

3.3 Gaps found in any reassessment are logged in the risk register with an owner and a due date, and tracked to closure by the Security Governance team.

## 4. Core control domains

4.1 **Access.** Minimum necessary access, role-based access, quarterly access recertification, privileged access through the PAM vault only, and no shared accounts.

4.2 **Cryptography.** Customer data is encrypted at rest with keys held in the cloud KMS. TLS 1.2 or higher is required in transit. Card data is handled only inside the PCI-scoped card zone.

4.3 **Logging and monitoring.** Server, application and mobile-backend logs stream to the Kestrel SOC (run jointly with our managed security partner) for 24x7 correlation.

4.4 **Secure development.** Threat modelling for new features, static and dynamic code scanning in CI, and independent code inspection before release.

4.5 **Vulnerability management.** Internet-facing systems are scanned weekly. Critical findings are fixed within 7 days, high within 30 days.

4.6 **Third parties.** Vendors with access to customer data are assessed before onboarding and annually thereafter, under KST-VND-001.

4.7 **Resilience.** The platform runs active-passive across two cloud regions in India. Recovery objectives are set in the Business Continuity Plan and tested every six months.

## 5. Data residency

5.1 All payment data is stored only in India. Copies processed abroad for any purpose are deleted within the window allowed by applicable RBI instructions.

## 6. Roles

6.1 **Board:** adopts this policy and the security risk appetite.

6.2 **Risk Committee:** receives quarterly security dashboards and the annual reassessment.

6.3 **CISO:** owns the policy, the risk register and the SOC relationship.

6.4 **Engineering leads:** build controls into their services and attest to them each quarter.

## 7. Exceptions

7.1 Exceptions to this policy need CISO sign-off, a compensating control and an expiry date of no more than six months. They are reported to the Risk Committee.
