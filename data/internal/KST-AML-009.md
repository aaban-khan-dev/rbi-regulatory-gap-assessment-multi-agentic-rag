<!-- SYNTHETIC DOCUMENT. Kestrel Wallet Services Private Limited is a fictional company created for the RBI Regulatory Gap Assessment project. This is not real company data. -->

# Sanctions and Name Screening Procedure

| Field | Value |
|---|---|
| Document ID | KST-AML-009 |
| Version | 3.3 |
| Owner | Head of Financial Crime Compliance (Principal Officer) |
| Approved by | Principal Officer |
| Effective from | 2026-01-10 |
| Last reviewed | 2026-01-05 |
| Next review | January 2027 |

## 1. Purpose

1.1 Kestrel must not provide services to people or organisations that the United Nations or the Government of India has designated as linked to terrorism or weapons proliferation. This procedure sets how Watchlist Hub keeps them off the platform.

## 2. Watchlist Hub

2.1 Watchlist Hub is the screening service used by Onboard, Sentinel and the Agent Portal. It fuzzy-matches names, dates of birth, nationalities and identity numbers against the lists in section 3 and returns a match score.

## 3. Lists screened

3.1 Watchlist Hub loads the following lists:
- the UN Security Council ISIL (Da'esh) and Al-Qaida sanctions list;
- the UN Security Council Taliban sanctions list;
- the individuals and organisations listed under the 2007 Prevention and Suppression of Terrorism Order and the UAPA terrorist-organisation schedules maintained by MHA;
- the WMD Act section 12A designation list, downloaded from the FIU-India portal;
- Kestrel's internal block list of customers exited for financial crime.

3.2 **Refresh.** FCC's screening analyst downloads every list from its official source at 06:00 each day and loads it into Watchlist Hub. Additions, deletions and amendments take effect the same morning. The analyst signs off the daily load in the screening log.

## 4. Screening points

4.1 **New customers.** No Lite or Plus wallet is switched on until Watchlist Hub returns either no match or a match that an FCC analyst has cleared as a false positive. Onboard holds the application in a pending state until then.

4.2 **Existing customers.** Every night, the full customer base is re-screened against the day's lists.

4.3 **Outlets and payees.** Kestrel Points outlet owners are screened at vetting and nightly. Payees added in the app are screened when they are saved.

## 5. Handling a true match

5.1 The wallet is frozen immediately, and no payment to or from it is allowed.

5.2 The Principal Officer notifies FIU-IND and the MHA nodal officer the same day, copying RBI. Freeze or release orders from the authorities are actioned the moment they arrive.

5.3 If a customer applies to have funds released, FCC passes the application and a statement of the frozen balance to the nodal officer inside two working days.

## 6. Quality assurance

6.1 Each quarter, FCC tests Watchlist Hub with seeded test names to confirm match quality, and keeps the results for audit.
