# Phase 1 corpus — final

Seven documents. Verified against RBI's live pages on 2026-10-08.

Scope note: RBI reorganised several Master Directions into entity-specific
successors during 2025-26. Those successors are deliberately OUT of this
corpus. The superseded documents are kept and labelled, which is what the
version-aware retrieval is for.

---

## MASTER DIRECTIONS

### 1. Prepaid Payment Instruments

```yaml
doc_id: md-ppi-2021
title: Master Directions on Prepaid Payment Instruments (PPIs)
circular_number: RBI/DPSS/2021-22/82
reference_number: CO.DPSS.POLC.No.S-479/02.14.006/2021-22
issue_date: 2021-08-27
amended_up_to: 2026-09-30
effective_from: 2021-08-27
effective_to: null
status: in_force
document_type: master_direction
amends: null
url: https://rbidocs.rbi.org.in/rdocs/notification/PDFs/82MDPPIS2708202181CF0A6FCD1B47B88CAE8E92A228B160.PDF
landing_page: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12156
sha256: ""
```

Revision history in the document header: 2026-09-30, 2024-12-27, 2024-02-23,
2023-02-10, 2021-11-12.

### 2. Know Your Customer

```yaml
doc_id: md-kyc-2016
title: Master Direction - Know Your Customer (KYC) Direction, 2016
circular_number: RBI/DBR/2015-16/18
reference_number: DBR.AML.BC.No.81/14.01.001/2015-16
issue_date: 2016-02-25
amended_up_to: 2025-08-14
effective_from: 2016-02-25
effective_to: null
status: in_force
document_type: master_direction
amends: null
url: https://rbidocs.rbi.org.in/rdocs/notification/PDFs/MD18KYCF6E92C82E1E1419D87323E3869BC9F13.PDF
landing_page: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=11566
sha256: ""
```

Revision history, 16 entries: 2025-08-14, 2025-06-12, 2024-11-06, 2024-01-04,
2023-10-17, 2023-05-04, 2023-04-28, 2021-05-10, 2021-04-01, 2021-03-23,
2020-12-18, 2020-04-20, 2020-04-01, 2020-01-09, 2019-08-09, 2019-05-29.

Note: entity-specific KYC Directions dated 2025-11-28 exist and are more
recently revised. This document's status is recorded as in_force on the basis
that RBI still lists it; if its PDF carries a "Withdrawn" watermark, change
status to `repealed` and set effective_to.

### 3. Digital Payment Security Controls — REPEALED

```yaml
doc_id: md-dpsc-2021
title: Master Direction on Digital Payment Security Controls
circular_number: RBI/2020-21/74
reference_number: DoS.CO.CSITE.SEC.No.1852/31.01.015/2020-21
issue_date: 2021-02-18
amended_up_to: null
effective_from: 2021-08-18
effective_to: 2026-07-31
status: repealed
document_type: master_direction
amends: null
url: https://rbidocs.rbi.org.in/rdocs/notification/PDFs/MD7493544C24B5FC47D0AB12798C61CDB56F.PDF
landing_page: https://website.rbi.org.in/web/rbi/-/notifications/master-direction-on-digital-payment-security-controls-12032
sha256: ""
```

PDF carries a red "Withdrawn" watermark. Repealed 2026-07-31 and replaced by
entity-specific Directions (out of scope for this corpus). Applied to
Scheduled Commercial Banks excluding RRBs, Small Finance Banks, Payments Banks
and credit-card-issuing NBFCs. Came into effect six months after issue.

Kept deliberately: an as-of-date query for any date in [2021-08-18,
2026-07-31] should return this document; a query for today should not.

---

## AMENDMENT CIRCULARS

### 4

```yaml
doc_id: amd-kyc-2024-11
title: Amendment to the Master Direction - Know Your Customer (KYC) Direction, 2016
circular_number: RBI/2024-2025/87
reference_number: DOR.AML.REC.49/14.01.001/2024-25
issue_date: 2024-11-06
status: in_force
document_type: amendment
amends: md-kyc-2016
landing_page: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12746
url: ""
sha256: ""
```

Amends paragraphs 10(f), 56(h), 56(j). Also renames every internal
cross-reference from "section" to "paragraph".

### 5

```yaml
doc_id: amd-kyc-2025-06
title: Reserve Bank of India (Know Your Customer (KYC)) (Amendment) Directions, 2025
circular_number: RBI/2025-26/51
reference_number: DOR.AML.REC.30/14.01.001/2025-26
issue_date: 2025-06-12
status: in_force
document_type: amendment
amends: md-kyc-2016
landing_page: https://rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx?Id=12866
url: ""
sha256: ""
```

Amends paragraph 38 (updation / periodic updation of KYC). Inserts a new
clause before 38(a) and inserts 38(e) on due notices.

### 6

```yaml
doc_id: amd-kyc-2025-08
title: Reserve Bank of India (Know Your Customer (KYC)) (2nd Amendment) Directions, 2025
circular_number: RBI/2025-26/75
reference_number: DOR.AML.REC.46/14.01.001/2025-26
issue_date: 2025-08-14
status: in_force
document_type: amendment
amends: md-kyc-2016
landing_page: https://rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx?Id=12893
url: ""
sha256: ""
```

### 7

```yaml
doc_id: amd-ppi-2024-02
title: Amendment to Master Direction on Prepaid Payment Instruments
circular_number: RBI/2023-24/126
reference_number: CO.DPSS.POLC.No.S1092/02-14-006/2023-2024
issue_date: 2024-02-23
status: in_force
document_type: amendment
amends: md-ppi-2021
landing_page: ""
url: ""
sha256: ""
```

Revises paragraph 10.2 — permits PPIs for mass transit systems. Find the
landing page by searching RBI Notifications for the circular number.

---

## Before running Phase 1

Open the four amendment landing pages and copy the PDF link from each into its
`url` field. The three Master Direction urls are already filled in and
verified. If a url is left empty the downloader should fail loudly for that
document rather than skip it silently.
