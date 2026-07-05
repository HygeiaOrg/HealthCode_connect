# How invoice verification works in the real world, and how this engine maps onto it

Researched 2026-07-05 against healthcode.co.uk, insurer provider documentation (Bupa, AXA Health, Aviva, Vitality, WPA), gov.uk, ccsd.org.uk and the NHS Data Dictionary. Sources cited inline. Companion to the rule inventory in `backend/validation/`.

## The real pipeline: three checkpoints before money moves

A UK private-practice invoice passes three verification stages.

**Checkpoint 1, the practice.** Billing software runs local checks before submission. This is where our engine sits. The practice's incentive is to submit a "clean bill" the first time, because a failed bill sits parked until corrected and the payment clock never starts.

**Checkpoint 2, Healthcode clearing (VEDA).** Healthcode is the industry clearing house (about 1.05M invoices per month, Jan-Apr 2026 figures from healthcode.co.uk). Validation runs synchronously at submission against the specific insurer's rules; a bill either passes and waits for the insurer to collect it, or fails and is returned. Each VEDA error names the field, the error, and a recommended solution (ePractice biller User Guide pp. 27-28). What VEDA checks: membership numbers against the live insurer databases for Aviva, AXA Health, Bupa and Vitality (name, date of birth and postcode must match the record; other insurers get format-only checks), specialist/payee/site recognition mappings, CCSD and ICD code validity per insurer, charge-code mapping to Industry Standard Codes, net total against the insurer tariff, authorisation-number format, duplicate invoice numbers, and maximum invoice age. Healthcode's published top five failure categories: patient insurance details, controlling specialist, procedure code, service date, service item provider number (healthcode.co.uk/do-your-bills-pass-the-test/).

**Checkpoint 3, insurer adjudication.** After clearing, the insurer verifies eligibility at the treatment date, matches the pre-authorisation, applies its fee schedule caps (Bupa Benefit Limits at codes.bupa.co.uk, updated monthly; AXA/Aviva/Vitality/WPA publish per-CCSD-code maxima), applies unbundling and multiple-procedure formulas (typically 100%/50%/25%), and runs plausibility rules (AXA: one consultation per patient per day, max one a week; Vitality: no consultation billable on the day of a procedure; a published banned-code list). Failures here become rejections, queries, or shortfalls (paid at schedule rate, patient owes the rest). All five insurers refuse invoices older than six months from treatment.

## Coverage map: real check → engine rule

| Real-world check (source) | Engine rule | Status |
|---|---|---|
| Field/error/solution error format (VEDA) | `Issue` wire shape | Matches the real taxonomy |
| Mandatory bill fields (Healthcode billing guide: invoice no./date, provider, patient, policy, setting, dates, codes, totals) | `structural.*` over schema.json | Covered |
| Membership number format per insurer (VEDA "Invalid Format") | `format.membership` (WPA, Bupa Global, Allianz regexes) | Covered for format-published insurers |
| Live membership DB lookup + demographics match (Aviva/AXA/Bupa/Vitality) | `cross.demographics` requires surname/DOB/postcode present for those insurers | Partial: presence, not live match |
| Specialist recognised and mapped to insurer (VEDA "Specialist: Invalid Code"; The PPR) | `dict.specialist` + `cross.specialist_mapping` | Covered against the local register |
| Payee provider mapped (VEDA) | `dict.payee` + `cross.payee_mapping` | Covered |
| Treatment site mapped (VEDA) | `dict.site` + `cross.site_mapping` + `cross.setting_site` | Covered |
| CCSD code valid, correct shape (CCSD Technical Guide: letter+4 digits or 5 digits) | `format.ccsd` + `dict.ccsd` | Covered on a 32-code demo subset (real schedule is licensed) |
| ICD-10 diagnosis required for Bupa/Bupa Global/AXA/Vitality (healthcode.co.uk VEDA errors page) | `cross.icd10_required` with exactly those four flagged in insurers.json | Covered, matches reality |
| ICD-10 code shape + membership of code list | `format.icd10` + `dict.icd10` (63-code subset) | Covered |
| Charge code mapped to ISC, billable for this insurer (VEDA "Code not Mapped" / "not valid for Insurer") | `dict.charge_code` + `cross.not_billable` | Covered |
| Net total vs insurer tariff (VEDA "Net total exceeds insurer tariff") | `cross.tariff` (per-code caps summed) | Partial: illustrative caps, single ceiling not per-line |
| Authorisation number format per insurer (VEDA) | `format.preauth` | Covered |
| Setting valid for the procedure (I/D/O) | `structural.enum` + `cross.setting_procedure` | Covered |
| Inpatient needs admission/discharge dates (Healthcode billing guide) | `cross.inpatient_dates` + `cross.admission_order` | Covered |
| Date sanity (treatment after invoice, DOB after treatment, real calendar dates) | `cross.treated_after_invoice`, `cross.dob_after_treatment`, `format.date` | Covered |
| Duplicate invoice number (VEDA "Duplicate Invoice"; HMRC unique sequential numbering) | `cross.duplicate_number` (ledger) | Covered |
| Same claim resubmitted under a new number (insurer counter-fraud) | `dedup.duplicate_claim` (SHA-256 content fingerprint) | Covered; goes beyond VEDA's number check |
| NHS number Modulus-11 checksum (NHS Data Dictionary) | `format.nhs_number` | Covered, exact algorithm |
| GMC number 7 digits (GMC register) | `format.gmc` | Covered |
| UK postcode format (GOV.UK standard incl. GIR 0AA) | `format.postcode` | Covered |
| VAT exemption on medical care (Notice 701/57: exempt when protecting health; reports/cosmetic standard-rated) | `cross.vat_exempt` warning + per-line vat_rate | Covered as a warning, correct severity choice |
| Totals arithmetic | `cross.net_mismatch`, `cross.gross_mismatch` | Covered |
| Maximum invoice age (six months from treatment, all five insurers) | none | **Gap** |
| Unbundling / invalid code combinations (Bupa applies all CCSD unbundling rules; Aviva's six scenarios; Vitality banned codes) | none | **Gap** |
| Multiple-procedure fee formulas (100/50/25) | none | **Gap** |
| Itemisation: one line per treatment date (Bupa pays only first+last session otherwise) | none | **Gap** |
| Eligibility at treatment date, pre-auth number MATCH (not just format) | none | Not possible offline; needs insurer/Healthcode APIs |

Against Healthcode's top five real failure categories, the engine covers four locally (insurance details, controlling specialist, procedure code, provider mapping); service-date age is the fifth and is a small rule away.

## What production would add

1. Live lookups through Healthcode's own services: Membership Enquiry (real-time policy check against Aviva/AXA/Bupa/Bupa Global/Vitality databases), The PPR for practitioner recognition, and the Clinical Coding Toolkit for code mapping. Healthcode publishes REST APIs (apidocs.healthcode.co.uk). The engine's dictionaries/providers.json is the offline stand-in for exactly these registries, so the seams already exist.
2. Licensed data: the real CCSD schedule (maintained by the CCSD Group, whose members are Bupa, AXA, Aviva and Vitality; updated via bi-monthly bulletins) and per-insurer tariff files replacing the illustrative `tariff_cap` values. The dictionary format was built so a licensed export drops in unchanged.
3. Three cheap rules the research surfaced: invoice age (reject when invoice_date is more than six months after treatment_date; note the real limit runs to the submission date, so this is a lower bound), one-line-per-treatment-date itemisation, and a first pass at unbundling from the published code-pair lists.
4. The submission loop itself: on a real integration the bill goes to VEDA after passing local checks, and VEDA's response (pass, or field-level errors) feeds the same Fix-queue UI, since the error shape is already identical.

## The demo sentence

"Before an invoice leaves the practice, it passes the same classes of check the industry clearing house runs: membership format and demographics, provider and site recognition, CCSD and ICD-10 validity, insurer-specific tariff and authorisation rules, duplicate detection, and HMRC/VAT arithmetic, and it reports failures in the same field/error/solution format Healthcode returns, so every rejection is actionable at the point where it is cheapest to fix."
