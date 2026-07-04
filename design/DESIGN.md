# DESIGN.md: Competitive UX analysis for HealthCode Connect

## 1. Purpose and scope

This document records how 22 comparable products present dashboards, invoices, and payment pipelines, then turns that evidence into design decisions for our app: a cashflow and invoice-lifecycle dashboard for UK private-practice doctors whose invoices travel doctor → Semble → Healthcode → insurer.

Scope covers UX and information architecture only. We do not assess clinical features, pricing, or backend quality. Evidence (screenshots, objective observations) is kept separate from interpretation (scores, takeaways) throughout.

Method: every product was studied on 4 July 2026 from public sources: official product tours, help centers, training videos, and review-site galleries. Screenshots live in `design/references/<app>/` and are cited by ID (`C07-S2` means AdvancedMD, screen 2). The study set is 15 EHR and practice-management apps (C01 to C15), 5 finance dashboards (C16 to C20), and the two incumbents our users suffer today: Semble (C21) and Healthcode ePractice (C22).

## 2. Evaluation rubric

Each product is scored 1 to 5 on nine axes. A 0 means the axis could not be assessed from available evidence, and 0s are excluded from averages.

| Axis | Question it answers |
|---|---|
| navigation | Is the nav model clear, with few destinations? |
| hierarchy | Does information hierarchy balance density against legibility? |
| metric surfacing | Are the KPIs the user cares about visible on landing? |
| pipeline visibility | Can the user see where money or work sits in a multi-step process? |
| dataviz | Are charts legible and honest? |
| task speed | How few steps to the core answer? Our reference question is "when do I get paid?" |
| error prevention | Does the product validate before mistakes become failures? |
| states | Are empty, loading, and error states designed? |
| mobile | Is there usable mobile or responsive support? |

## 3. Synthesis

Read this section first. The teardowns in section 4 are the evidence behind it.

The headline: **pipeline visibility is the weakest axis in the entire field** (2.6 average, and 2.0 for the incumbents), while the finance tools dominate metric surfacing (4.6 versus 2.7 for EHRs). Nobody in this set shows a doctor where an invoice sits end to end, and nobody but Stripe states when money will actually arrive. That gap is our product.

### 3.1 Score matrix

| # | App | navigation | hierarchy | metric surfacing | pipeline visibility | dataviz | task speed | error prevention | states | mobile |
|---|---|---|---|---|---|---|---|---|---|---|
| C01 | Epic (Hyperspace/Hyperdrive) | 4 | 2 | 4 | 3 | 2 | 2 | 4 | 2 | 0 |
| C02 | Oracle Health / Cerner PowerChart | 2 | 2 | 2 | 3 | 0 | 2 | 4 | 1 | 0 |
| C03 | MEDITECH Expanse | 3 | 2 | 3 | 2 | 1 | 3 | 2 | 3 | 3 |
| C04 | athenaOne (athenahealth) | 4 | 3 | 2 | 3 | 3 | 2 | 3 | 2 | 0 |
| C05 | eClinicalWorks V12 | 2 | 1 | 2 | 3 | 1 | 2 | 3 | 0 | 3 |
| C06 | NextGen Office | 3 | 3 | 2 | 3 | 2 | 2 | 2 | 0 | 2 |
| C07 | AdvancedMD | 4 | 3 | 4 | 2 | 3 | 4 | 0 | 0 | 0 |
| C08 | DrChrono | 4 | 3 | 2 | 2 | 0 | 4 | 3 | 2 | 5 |
| C09 | Tebra (ex Kareo) | 3 | 4 | 4 | 3 | 3 | 4 | 3 | 0 | 0 |
| C10 | Elation Health | 4 | 4 | 3 | 3 | 2 | 3 | 5 | 0 | 3 |
| C11 | Practice Fusion | 4 | 3 | 2 | 2 | 0 | 2 | 4 | 3 | 0 |
| C12 | CareCloud | 3 | 3 | 2 | 4 | 0 | 2 | 4 | 2 | 0 |
| C13 | SimplePractice | 4 | 4 | 3 | 2 | 0 | 3 | 3 | 3 | 2 |
| C14 | Jane App | 4 | 4 | 3 | 4 | 2 | 3 | 0 | 0 | 0 |
| C15 | Healthie | 4 | 4 | 2 | 2 | 2 | 2 | 0 | 3 | 0 |
| C16 | Xero Analytics Plus | 4 | 4 | 4 | 2 | 4 | 3 | 0 | 3 | 0 |
| C17 | QuickBooks Online | 4 | 4 | 4 | 4 | 3 | 4 | 0 | 4 | 0 |
| C18 | Fathom | 4 | 4 | 5 | 1 | 4 | 3 | 2 | 3 | 0 |
| C19 | Syft Analytics | 4 | 4 | 5 | 2 | 4 | 3 | 2 | 2 | 0 |
| C20 | Stripe Dashboard | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 3 | 0 |
| C21 | Semble | 4 | 3 | 2 | 2 | 0 | 1 | 2 | 0 | 0 |
| C22 | Healthcode (ePractice) | 3 | 2 | 2 | 2 | 2 | 2 | 3 | 2 | 0 |

Category averages, zeros excluded: EHRs score 2.7 on metric surfacing against 4.6 for finance tools; task speed is 2.7 for EHRs, 3.6 for finance, and 1.5 for the incumbents. Stripe (C20) is the strongest single product in the set and the closest thing to a benchmark for us.

### 3.2 Table stakes

Patterns so widespread that omitting them would make the app feel broken. We implement all of these.

- Status chips on every list row, encoded with color plus icon plus label. Finance tools do all three (C20, C17); products that use bare dots or unlabeled color boxes force memorization (C01, C22, C05). Triple encoding is the standard we adopt.
- KPI cards that pair the number with a delta and a plain-language explainer. All five finance tools share this grammar (C16, C17, C18, C19, C20); Tebra brings it to healthcare billing (C09).
- Aging buckets (0-30, 31-60, 61-90, 91+ days) as the default framing for outstanding money. Doctors already meet these bands in Jane (C14), Tebra (C09), NextGen (C06), and Healthcode itself (C22).
- An action queue on landing with live counts per category: "Requiring Action 3" in Elation (C10), task counters in Healthcode (C22), badge counts in Practice Fusion and Healthie (C11, C15).
- Inline actions on list rows, so an exception is resolved without opening a detail page: "Receive payment" per row in QuickBooks (C17), chip-plus-action rows in Healthie (C15).
- Empty states that teach. QuickBooks shows a SAMPLE-badged chart before data exists (C17); Xero Analytics ships demo data with a banner (C16). Silent blank panels (C02, C05) read as breakage.
- A small nav: four or five labeled destinations. Every product with a 12-plus-item rail or tab strip scored poorly on findability (C02, C05, C17).

### 3.3 Differentiation opportunities

Gaps that most or all of the field leaves open. These are where we win, and each maps to a value prop.

1. **An end-to-end invoice timeline, past "collected", through to money in the bank.** The single largest gap in the set. Semble's status vocabulary dies at "Collected" and only updates on manual page refresh (C21); Healthcode's three-box tracker stops at insurer collection, with payment entered by hand afterwards (C22); SimplePractice knows only paid or unpaid (C13); Fathom and Syft have no per-invoice view at all (C18, C19). Our per-invoice timeline (Draft → Semble → Healthcode → insurer → paid, each stage dated) answers a question no competitor answers.
2. **An expected payment date as the hero.** Only Stripe states a date ("Expected Feb 21", C20). Tebra names the latency metric ("Payment Velocity: 38 DAYS", C09), Syft has debtors days (C19), Xero has average time to get paid (C16). We combine both: a named latency metric split per insurer, and a dated cashflow answer on landing.
3. **Validation before submission, not after.** Both incumbents validate only after the invoice leaves: Semble surfaces insurer API errors as toasts backed by a help-centre error catalogue (C21); Healthcode shows red error panels after Save & Send (C22). Elation's pre-submit Billing Analysis panel with named pass/fail checks is the model (C10), Cerner's "0 Missing Required Details" counter is the gate (C02), and Healthcode's own Field / Error / Solution triplet is the message format worth keeping (C22).
4. **Private versus NHS as a first-class comparison.** The pieces exist scattered: Jane splits insurer and patient invoices with shared numbering (C14), NextGen stacks insurance against patient A/R per month (C06), Tebra and Syft offer payer-type toggles and dual-series bars (C09, C19). Nobody presents two income streams side by side as the organizing question. We do.
5. **Pounds, not counts.** Healthcode charts the number of outstanding bills, never their value (C22); AdvancedMD shows "910" charge slips with no currency (C07). Every figure we show carries a £ value; days-stuck follows the QuickBooks "Overdue 47 days" pattern (C17) rather than a bare "pending".

### 3.4 Friction patterns to avoid

Failures common enough across the set to treat as anti-requirements.

- Money buried two or three levels deep. Flagged in athenaOne, NextGen, Tebra, Jane, Healthie, and Elation (C04, C06, C09, C14, C15, C10). Our landing screen is the cashflow view.
- Chrome stacking: three or four persistent bars before content starts (C01, C04, C05). We keep one nav layer.
- Status that requires a legend: icon-only dots (C01), unlabeled color boxes with hover tooltips (C22), icon clusters (C05).
- Stale-by-default data: refresh-to-update status in Semble (C21) and a manual refresh button on Tebra's dashboard (C09) undermine trust in a visibility product.
- Raw system output shown to clinicians: SOAP XML as the audit trail in Semble (C21), opaque payment ids in Stripe (C20). Our audit trail is a human-readable event list.
- Configuration as a substitute for opinion: 15-metric chart editors (C20), freeform card builders (C19). We ship one opinionated view.

### 3.5 What we build

Decisions carried into the MVP, in priority order.

1. Landing screen is the cashflow answer: expected money with dates, outstanding total, named latency metric per payer, and an action queue of invoices needing attention. Zero clicks to "when do I get paid?".
2. A pipeline strip in the QuickBooks money-bar style (C17): one segmented bar, each lifecycle stage labeled with £ amount and count, doubling as the filter for the invoice list below (the AdvancedMD donut-as-filter idea, C07, in bar form).
3. Every invoice row expands in place to its dated timeline (the Epic snapshot-expansion pattern, C01), with stage chips using color, icon, and label.
4. A pre-submission validation panel in Elation's pass/fail style (C10), messages in Healthcode's Field / Error / Solution format (C22), gated by a live "0 issues remaining" counter (C02).
5. A compare view: private versus NHS income as paired series (C19), aging buckets per payer (C14), rejection rates side by side.
6. Non-goals for the MVP: no mobile app (responsive layout only), no dashboard builder or chart configuration, no schedule or calendar views, no patient-facing surfaces.

## 4. Competitor teardowns

### C01 — Epic (Hyperspace/Hyperdrive)

Dominant hospital/clinic EHR; clinicians live in its patient chart, orders, and results workflows all day.

Navigation model: Persistent patient "storyboard" left rail + horizontal activity tabs (Summary, Chart Review, Results, Notes, Orders, Navigators) inside each chart; open-patient tab bar and toolbar rows above. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C01-S1 | Chart Summary rounding report: widget grid plus storyboard rail | video frame |
| C01-S2 | Chart Review encounter timeline with report preview and note sidebar | video frame |
| C01-S3 | Results Review flowsheet grid, abnormal flags, time-range slider | video frame |
| C01-S4 | Admission navigator med reconciliation with mark-as-reviewed audit | video frame |
| C01-S5 | Multi-patient list with status dot columns and inline snapshot | video frame |

Observations (evidence):

- A persistent left storyboard rail shows patient photo, age/sex, bed, code status, allergies (red text), attending, admission date, and risk banners on every activity in the chart.
- Chart activities are horizontal tabs: Summary, Chart Review, Results Review, Notes, Orders, Intake/Output, Navigators, Care Teams, History, Flowsheets; a second tab bar above switches between open patients.
- The Summary tab is a 'Rounding Report' widget grid: Patient Summary, Vitals, I/O, Weights (Last 2), Current Oxygen Device/Flow, Microbiology Results (last 21 days), Radiology (last 24 hours), and Lines, Drains and Airways with an annotated body diagram.
- Chart Review lists encounters as a dated table with type icons and filter checkboxes (Outpatient, Inpatient, Admissions, ED); selecting a row opens a preview containing Hospital Problem List, Care Timeline, Discharge, and Medication List at Discharge panels.
- Results Review pairs a left category tree with checkboxes against a central flowsheet grid of date columns; abnormal values show red text plus a '!' icon, and a bottom slider sets the time window ('Viewing: -3 yr').
- The admission navigator's med reconciliation gives each home med a row with 'Unable to Obtain', Last Dose (Optional) fields, and 'Taking?' checkboxes, ending in a 'Mark as Reviewed' control that records reviewer name and timestamp, with Previous/Next steppers.
- The multi-patient list has columns for MRN, Handoff Summary, Temp, BP, Pulse, Resp, plus colored-dot indicator columns (New Rslt Flag, New Notes, RQD MD Doc, Code Status); expanding a row shows a '24 hour snapshot' report inline.
- A note editor can be pinned as a right sidebar so clinicians write the H&P while reading the chart; a yellow sticky-note overlay carries handoff text across screens.
- Empty states are single plain-text lines, e.g. 'No results found for the last 504 hours' and 'You're viewing all available results'.
- Three stacked chrome bars (system toolbar, patient tabs, activity toolbar) and sub-11px type produce very high on-screen density.

Scores: navigation 4 · hierarchy 2 · metric surfacing 4 · pipeline visibility 3 · dataviz 2 · task speed 2 · error prevention 4 · states 2 · mobile n/a

Worth copying:

- Persistent context rail: keep one invoice's key facts (payer, amount, days outstanding, current pipeline stage) pinned on every screen the way the storyboard pins patient identity.
- Inline row expansion to a snapshot: the patient list expands into a '24 hour snapshot' without navigation; our invoice list should expand a row into the doctor-to-Semble-to-Healthcode-to-insurer timeline in place.
- Audit-stamped review: 'Mark as Reviewed' with reviewer name and timestamp is a clean pattern for our pre-submission validation sign-off.
- Compact status-flag columns on list rows (new result, needs doc) map directly to invoice flags like 'data error', 'awaiting insurer', 'paid' — but add labels, not dots alone.
- Care Timeline panel with dated milestones inside a record preview is the exact shape of our invoice-lifecycle timeline.

Worth avoiding:

- Wall-of-table density with three stacked toolbars and tiny type; our dashboard needs one hero metric (cashflow) with generous hierarchy, not 40 widgets at equal weight.
- Answers buried behind module tabs: Epic needs third-party training videos to learn; 'when do I get paid?' must be answered on landing, zero clicks.
- Icon-only colored dots that require a memorized legend for status meaning.
- Plain one-line empty states with no explanation or next action.
- Time-window sliders and checkbox trees as the primary filter model — too heavy for a small-practice finance tool.

### C02 — Oracle Health / Cerner PowerChart

Hospital-grade EHR for clinicians; classic PowerChart is a dense Windows-style chart browser, with a next-gen Oracle rebuild adding AI summaries and adaptive shortcuts.

Navigation model: Persistent left "Menu" rail (20+ chart sections) + patient demographics banner + toolbar row + breadcrumb; next-gen version moves to schedule-first landing with bottom tabs and a global message/search bar. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C02-S1 | Classic Orders view: left rail, tree filter, dense order table | video frame |
| C02-S2 | Diagnosis and Problems: two stacked tables, mostly empty space | video frame |
| C02-S3 | Provider View with tabbed workflows and section outline | video frame |
| C02-S4 | Order reconciliation: before/after columns with status checkmarks | video frame |
| C02-S5 | Next-gen schedule landing with AI patient summary card | marketing render |
| C02-S6 | New Prescription search suggests drugs from frequent order history | marketing render |

Observations (evidence):

- Classic PowerChart uses a fixed left 'Menu' rail with 20+ text links (Orders, Medication List, Allergies, MAR Summary, Documentation); frequently-used items carry inline '+ Add' shortcuts directly in the rail.
- A blue patient banner spans the top of every chart screen showing name, age, DOB, MRN, allergies, attending, location and discharge dates in one dense strip.
- The Orders screen combines a collapsible tree filter (Plans / Orders / categories with checkboxes), a scoping dropdown ('All Orders 5 Days Back'), and a grouped table with Order Name, Ordering Physician, Status and Details columns.
- Order status is conveyed as plain text values ('Ordered', 'Documented', 'Prescribed') in a Status column, not as colored chips.
- The order-reconciliation screen shows a two-column before/after layout ('Orders Prior to Reconciliation' vs 'Orders After Reconciliation') with per-row radio decisions and a footer showing '0 Missing Required Details / All Required Orders Reconciled'.
- A 'Reconciliation Status' widget with three checkmarks (Meds History, Admission, Discharge) marks progress through the reconciliation workflow.
- The Orders toolbar includes a 'Check Interactions' action and an 'External Rx History' lookup before signing orders.
- Provider View organises documentation as browser-style tabs (Inpatient Workflow, Discharge, Pediatric Quick Orders) with a left outline of note sections (Chief Complaint, Assessment and Plan).
- Next-gen Oracle Health lands on the day's schedule with a header count ('26 patients scheduled', '0 of 26 patients seen') and an expandable AI-generated patient summary citing its sources inline.
- Next-gen prescription search pre-populates four drug suggestions labelled 'Based on my frequent order history' before the user types.

Scores: navigation 2 · hierarchy 2 · metric surfacing 2 · pipeline visibility 3 · dataviz n/a · task speed 2 · error prevention 4 · states 1 · mobile n/a

Worth copying:

- Reconciliation status checkmarks (Meds History / Admission / Discharge) are a compact multi-stage progress widget; mirror it for the invoice pipeline: Submitted to Semble / Sent to Healthcode / With insurer / Paid.
- '0 Missing Required Details' footer counter before signing maps directly to our pre-submission validation: show a live count of unresolved issues that must hit zero before an invoice can go out.
- Adaptive shortcuts ('Based on my frequent order history' drug suggestions) fit invoicing: pre-suggest the doctor's most-billed procedure codes and insurers at invoice creation.
- Next-gen landing pattern of a headline progress count ('0 of 26 patients seen') translates to a cashflow hero: 'X of Y invoices paid this month, GBP Z outstanding.'
- Inline '+ Add' shortcuts on nav items cut a click from the most common create actions; useful for 'New invoice' from anywhere.

Worth avoiding:

- A 20+ item flat left rail where everything has equal weight; our doctors have five core jobs, so keep the nav to that.
- Status as plain grey text in a table column ('Ordered', 'Documented'); invoice states need color + icon + label chips readable at scanning speed.
- No KPIs on landing in classic PowerChart; the user must open sections to learn anything, the opposite of cashflow-as-hero.
- Mostly-empty white tables with no empty-state guidance (Diagnosis and Problems screen); empty pipeline stages should explain what happens next.
- Stacking three filter mechanisms (tree checkboxes, scope dropdown, column filters) on one screen; one clear timeline filter beats layered scoping.

### C03 — MEDITECH Expanse

Web-based hospital/ambulatory EHR with a widget-composed chart summary and a companion mobile task app, aimed at physicians in MEDITECH health systems.

Navigation model: Persistent black icon toolbar (Home/Chart/Document/Orders/Discharge/Sign/Workload) + three stacked rows of folder-style chart tabs + right-rail workload panel. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C03-S1 | Rounds patient list with workload rail and quick links | video frame |
| C03-S2 | Chart Summary with folder tabs and widget columns | video frame |
| C03-S3 | Widget-based summary: My Widget, Orders Snapshot, statuses | video frame |
| C03-S4 | Widget Preferences modal composing left/right column layout | video frame |
| C03-S5 | Expanse Now mobile app, Workload to Reminders toggle | video frame |
| C03-S6 | Summary widgets showing No Data to Display empty states | video frame |

Observations (evidence):

- Persistent black top toolbar holds icon+label actions: Home, Chart, Document, Orders, Discharge, Sign, Workload, Menu, Suspend; patient search sits in the same bar.
- Chart navigation uses a file-folder tab metaphor with 12 category tabs (Summary, Diagnostics, Provider Notes, Medications, Flowsheets, Health Mgmt...) arranged in three stacked rows.
- Rounds Patients list shows a red count badge (102) and rows combining name, color-coded age/sex chip (blue M, pink F), complaint, days-since-admission, care team, and per-row LAB/IMG/DEPT/NOTE quick-link stack.
- Right-rail 'My Workload' panel groups pending tasks into Administrative, Results, and Other with '1 of 1' counts and red alert icons.
- Summary screen is assembled from collapsible widgets (Triage Info, Common Labs, Orders Snapshot, Documents, Visits, COVID-19 Patient Status); a Widget Preferences modal lets users add widgets to left/right columns under a named template ('TestWidget', 'Rename Custom Template').
- Abnormal lab values are yellow-highlighted with reference range and H/L flag, e.g. '110 g/L (140-160) L'; pending results show the literal word 'Pending' with an expected date.
- Empty widgets display the explicit text 'No Data to Display' rather than hiding.
- Patient header shows demographics, MRN, allergies, BMI, and a red 'Full Resuscitation' status chip.
- Expanse Now mobile app uses a Workload/Reminders dropdown toggle, grouped cards for Messages, Prescriptions, Results, and a bottom tab bar with a floating action button.
- No charts appear in any captured screen; visualization is limited to a 'Growth Chart' text link and small sparkline-style icons in the right rail.

Scores: navigation 3 · hierarchy 2 · metric surfacing 3 · pipeline visibility 2 · dataviz 1 · task speed 3 · error prevention 2 · states 3 · mobile 3

Worth copying:

- Composable widget home with saved named templates (Widget Preferences modal): let doctors arrange cashflow, aged-invoice, and NHS-vs-private widgets and persist the layout.
- Right-rail work queue with grouped counts ('Results 1 of 1', red alert icon): mirror as invoice-state groups with counts, e.g. 'Rejected 2', 'Awaiting insurer 14'.
- Per-row quick-link stack (LAB/IMG/DEPT/NOTE) that deep-links into detail: give each invoice row one-tap jumps to timeline, validation errors, and remittance.
- Explicit 'No Data to Display' text in every empty widget; never render a silent blank panel.
- Scoped mobile companion (Expanse Now) that carries only tasks, messages, and reminders instead of the full app: matches a 'what needs action today' mobile view for doctors.

Worth avoiding:

- Three stacked rows of twelve folder tabs; flat top-level nav collapses past about seven sections, so keep our nav to a handful of destinations.
- One highlight color (yellow) meaning three things at once: active tab, abnormal value, and editable field; reserve each status color for one meaning in the invoice pipeline.
- Ultra-dense rows with truncated labels ('Training,Re...') that force users to hover or memorize; invoice rows must stay legible at a glance.
- Status shown only as words and counts with zero charts; payment latency needs a plotted timeline, not just a 'Pending' label.

### C04 — athenaOne (athenahealth)

Cloud EHR + practice management + RCM suite for US ambulatory practices, spanning scheduling, clinical encounters, claims, and payments in one browser app.

Navigation model: Persistent purple top nav (Calendar, Patients, Claims, Financials, Reports, Quality, Apps) + patient-context banner + encounter stepper; left icon rail inside the chart; global ID search top-right. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C04-S1 | 2026 clinical encounter with diagnosis gaps and AI toggle | video frame |
| C04-S2 | Check-in screen with patient banner and workflow stepper | video frame |
| C04-S3 | Insights dashboard: visits trend with year-over-year comparison | video frame |
| C04-S4 | Chart view: problems, outstanding orders, follow-up ticklers | video frame |
| C04-S5 | Schedule Appointment modal with required-field labels | video frame |
| C04-S6 | Marketing wheel: payments, engagement, clinical module map | marketing render |

Observations (evidence):

- Top nav is a fixed module bar: Calendar, Patients, Claims, Financials, Reports, Quality, Apps, Support, plus a numeric patient-ID search field at top right.
- Every patient screen carries a full-width context banner: photo, name, age/sex/pronouns, DOB, patient ID, contact, next appointment, provider, and primary insurance (e.g. 'Primary MEDICARE-CA SOUTHE...').
- Encounter flow is a horizontal dot stepper labeled Check-in > Intake > Exam > Sign-off > Checkout, with the current stage filled; the 2026 build uses tab labels Review, HPI, ROS, PE, Sign-off.
- 2026 encounter view shows a '2 Diagnosis Gaps' badge with an amber dot above the Active Problems list, and problems grouped by system (Cardiac and Vasculature, Endocrine and Metabolic).
- A 'Try AI-native encounter' toggle sits in the encounter header; a right panel titled 'DIAGNOSES & ORDERS' lists items added during the visit.
- Insights dashboard ('See More Patients') pairs a left rail of drill-in questions with a line chart comparing current vs previous year Total Visits, with MOM/YOY/TTM period toggles and tabs for Total/Patient/Ancillary visits.
- Two left-rail items on the Insights page read 'Future page!' as placeholder content.
- Chart home is a three-column card layout: Problems and Care Episodes left; Outstanding Orders, Follow Up ticklers (dated), and Recent Activity (dated medication list) right.
- Scheduling modal marks each field inline as 'First name - Required', 'Insurance - Required', with a disabled grey Next button until completion.
- A bottom status strip shows a task counter (e.g. '6 tasks') and department selector; secondary patient actions sit in a dropdown row: Registration, Messaging, Scheduling, Billing, Clinicals, Communicator.

Scores: navigation 4 · hierarchy 3 · metric surfacing 2 · pipeline visibility 3 · dataviz 3 · task speed 2 · error prevention 3 · states 2 · mobile n/a

Worth copying:

- The encounter stepper (Check-in > Intake > Exam > Sign-off > Checkout) is exactly the pattern our invoice timeline needs: named stages, filled dot for current position, one glance answers 'where is it now'. Apply it to Draft > Semble > Healthcode > Insurer > Paid.
- Persistent context banner: insurance and next-event data pinned to every screen of a record. Our invoice detail should pin payer, submission date, and expected-payment date the same way.
- Gap badges ('2 Diagnosis Gaps' with amber dot) surface fixable problems before sign-off; mirror this for pre-submission validation errors on an invoice.
- Insights' question-led drill-ins ('Ways to see more patients' with a KPI, delta, and red arrow per question) frame analytics around user goals, not chart types; frame ours as 'When do I get paid?' and 'What is stuck?'.
- Inline '- Required' field labels plus a disabled Next button block bad submissions cheaply; use for claim-critical fields.

Worth avoiding:

- Money answers live three levels deep (Financials module, then Reports, then a separate Insights product); our cashflow number must be the landing screen, not a destination.
- Three stacked chrome layers (top nav, patient banner, action-dropdown row) eat a third of the viewport before content; keep our invoice list under one header.
- Shipping visible 'Future page!' placeholders in a production dashboard undermines trust; hide unfinished drill-ins instead.
- Dense grey forms with browser-default controls (legacy athenaNet screens) make error-spotting hard; status needs color + icon + label chips, not text in tables.

### C05 — eClinicalWorks V12

All-in-one ambulatory EHR plus practice management covering scheduling, charting, and billing for US clinics of every size.

Navigation model: Left icon rail of module shortcuts plus a dense top toolbar with patient-hub tab bar (Medical Summary, Labs, Encounters...) and a collapsible right context panel. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C05-S1 | V12 browser progress note with labs and right panel | video frame |
| C05-S2 | V12 structured template dialog over progress note | video frame |
| C05-S3 | Orders grouped under ICD codes with CPT reassociation | video frame |
| C05-S4 | Resource schedule with appointment and visit-status dialog | video frame |
| C05-S5 | healow kiosk check-in and mobile arrival confirmation | marketing render |
| C05-S6 | healow Pay invoice lookup and mobile balance-due card | marketing render |

Observations (evidence):

- Chrome stacks four persistent bands before content: window title, module toolbar, patient demographics banner with photo, then a tab strip (Medical Summary, CDSS, Rx, Labs, DI, Procedures, Growth Chart, Imm, T.Inj, Encounters).
- Patient banner uses a row of colored sticky-note style widgets (yellow NOTES, pink SECURE NOTES, green insurance/balance card) each with 6-8pt text.
- Right-hand panel lists resulted orders as a dense table with per-row icon clusters: orange squares, green plus, red exclamation, paperclip attachment, plus a date column.
- Lab results render as an HTML table with abnormal values flagged in red text plus H/L/PH suffix letters, reference ranges printed under every value.
- Orders screen groups orderable items under ICD-10 code headings (e.g. 'G47.33 Obstructive sleep apnea syndrome') with CPT lines nested beneath; billing codes are edited inline in the note.
- Top-right shows a row of single-letter jellybean counters (P, E, S, D, R, T, L, M, TV) with numeric badges acting as global work queues.
- Bottom toolbar of the note carries 12+ buttons in one row: Send, Print, Fax, Record, Lock, Details, Templates, Claim, Letters, Ink, Attachments.
- Scheduling uses a resource-column day grid; the appointment dialog exposes visit type, status dropdown, insurance, and copay fields in one modal (C05-S4).
- healow Pay (patient side) shows a 'Balance Due $143.63' card with a single Pay button, statement amount, past transactions link, and 'Find My Invoice' by statement code + last name (C05-S6).
- Kiosk check-in offers identification via driver's license scan, QR code, or card swipe as three large tiles; phone shows 'Check-in Complete' with green check and appointment details card (C05-S5).

Scores: navigation 2 · hierarchy 1 · metric surfacing 2 · pipeline visibility 3 · dataviz 1 · task speed 2 · error prevention 3 · states n/a · mobile 3

Worth copying:

- Jellybean counters: tiny always-visible badges for each work queue (labs, docs, messages) — adapt as invoice-state counters (draft, submitted, queried, paid) pinned in our header.
- healow Pay's mobile card leads with one number, 'Balance Due $143.63', and one Pay action — same discipline for our cashflow hero metric and 'chase payment' action.
- Visit-status dropdown updated from the schedule grid drives the whole clinic pipeline; a one-click status change on the invoice row beats opening a detail page.
- Kiosk check-in's three large labeled tiles show how to make one decision per screen for infrequent tasks like onboarding an insurer connection.
- Attaching CPT/billing codes inside the clinical note at point of care prevents downstream claim errors — our pre-submission validation should run where data is entered, not at submit time.

Worth avoiding:

- Four stacked persistent bands plus left rail plus right panel leave under half the viewport for actual content; keep our chrome to one nav layer.
- Color-coded sticky-note widgets with 6-8pt text encode meaning by hue alone and are illegible; use labeled status chips with icon + text.
- Icon clusters (orange square, red bang, green plus, paperclip) per row with no visible legend force memorization; every status glyph we ship needs an inline label.
- 12-button bottom toolbars treat every action as equal; expose the two actions that matter per state and fold the rest into a menu.
- No visible charts anywhere in the clinical or billing screens — money data buried in tables is exactly the zero-visibility pain we are solving; do not ship tables without a timeline view.

### C06 — NextGen Office

Cloud EHR + practice management (formerly MediTouch) for US small practices, bundling scheduling, eligibility, billing, and A/R reporting.

Navigation model: Left icon rail (search, print, notes, tasks, dashboard) plus a horizontal tab strip of workflow views with overflow arrows; analytics uses its own tab row. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C06-S1 | YourHealthFile patient portal: six color-coded action tiles | real UI |
| C06-S2 | Open Encounters tab with Billed/Not Billed filters and Claim ID | real UI |
| C06-S3 | Patient Tracker: status segmented filter and appointment table | real UI |
| C06-S4 | All Locations View grouping appointments by practice site | real UI |
| C06-S5 | Multi-provider day scheduler in tablet marketing frame | marketing render |
| C06-S6 | Accounts Receivable analytics: stacked Insurance vs Patient A/R bars | marketing render |

Observations (evidence):

- EHR dashboard is a horizontal tab strip of seven workflow views (Patient Tracker, Room Tracker, Resident Roster, 2-hour View, All Locations View, Recent Patients, Open Encounters) with left/right overflow arrows.
- Open Encounters has a three-axis filter block: Type (All/Office/Phone), Status (All/Open/Re-Opened/No Cosigner/Clinically Sig), Billing (All/Billed/Not Billed), rendered as segmented button groups.
- Encounter table columns include Service Date, Provider, Diagnosis (ICD code), Encounter Status, Signed By, Co-Signed By, and Claim ID, linking clinical work to the claim.
- Default encounter list window is 30 days, extendable via 30/60/90 Day toggles and a date-range picker; a yellow-bulb Note explains the limit.
- Patient Tracker uses a green dot inside each patient chip plus a Patient Status segmented filter (All/Waiting/In Room/Checked Out).
- All Locations View groups the day's appointments under practice-name headings (e.g. LJ Family Practice) with Time/Patient/Appt Type/Status columns.
- Billing analytics (S6) is a tabbed row: Appointment, Adjustment, Charges, Payments, Accounts Receivable; the A/R tab shows four chart cards including stacked monthly bars split Insurance A/R vs Patient A/R, Days to Bill and Pay, Collection Ratios, and Percent of Total A/R > 120 Days.
- Patient portal landing is a 2x3 grid of color-coded tiles, each with a headline metric ("$0.00 Balance Due", "2 New Messages", next appointment date) above the action label.
- Scheduler shows side-by-side provider day columns with color-coded appointment blocks and Day/Week/Month toggles.
- Left edge of every EHR screen carries a persistent vertical icon rail; a "Need Help?" button sits top-right on each tab.

Scores: navigation 3 · hierarchy 3 · metric surfacing 2 · pipeline visibility 3 · dataviz 2 · task speed 2 · error prevention 2 · states n/a · mobile 2

Worth copying:

- Billed/Not Billed as a first-class filter on the work list plus a Claim ID column ties clinical events to money; our invoice timeline should keep the clinical-event-to-invoice link one click away.
- Splitting A/R bars into Insurance vs Patient per month maps directly onto our private-vs-NHS (and insurer-vs-patient) comparison; a stacked monthly bar is the right form.
- Percent of A/R over 120 days as a named chart is a blunt, honest latency metric; we should surface an equivalent 'invoices older than X days' figure on landing.
- Portal tiles that lead with the number ($0.00 Balance Due, 2 New Messages) before the action label make each tile a mini-KPI; our dashboard cards should do the same with cash figures.
- Segmented status filters (All/Waiting/In Room/Checked Out) beat dropdowns for pipeline stages; use the same pattern for Draft/Submitted/With Insurer/Paid.

Worth avoiding:

- Money metrics live three levels deep in a Reports area under their own tab row; cashflow must be the landing screen, not a report you navigate to.
- A tab strip that overflows into arrow-scrolling hides whole workflows; keep our nav to a handful of always-visible destinations.
- Charts with unlabeled axes and tiny legends (S6) force squinting; label values on bars and keep one chart per question.
- A 30-day default data window with an explanatory footnote surprises users into thinking records vanished; make time-range scope explicit in the header, not a note.
- Status conveyed by a bare green dot with no label or color variation carries almost no information; status chips need color plus label plus, ideally, an icon.

### C07 — AdvancedMD

US practice-management EHR whose physician dashboard turns each task category into a clickable donut counter feeding a worklist.

Navigation model: Top module tabs (Patients / Dashboard) over a fixed three-column layout: schedule rail, donut widget column, worklist table. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C07-S1 | Full donut dashboard: schedule, donut widgets, worklist table | real UI |
| C07-S2 | Notes donut filtering worklist, Not Signed 169 of 696 | real UI |
| C07-S3 | Donut widgets with urgent and held satellite badges | real UI |
| C07-S4 | Priority, Unsigned, Held summary circles above category donuts | real UI |
| C07-S5 | Angled marketing render of donut column and message worklist | marketing render |

Observations (evidence):

- Dashboard is a three-column layout: color-coded appointment schedule on the left, donut task widgets in the center, a checkbox worklist table on the right.
- Three summary circles sit at the top of the donut column labeled Priority (red), Unsigned (white), Held (grey), each showing only a count (e.g. 2.1k, 12.5k, 1.6k).
- Each task category (Notes, Orders, Rx, eRx Requests, Charge Slips, Docs & Images, Messages, Reputation Mgmt) is its own donut with a total count on top and two satellite badges: red for urgent/unreviewed and grey for held/reviewed.
- Donut rings are segmented by status color (green/blue/grey), and clicking a donut or badge filters the worklist to that category and status.
- The worklist header states scope and progress as text, e.g. "Not Signed 169 of 696" and "All 28", with Sign / Review actions and Priority / Hold dropdown buttons above it.
- Worklist rows carry a red or grey priority dot, patient name in caps, item description, item-type icon, responsible provider with an italic "status: Unreviewed/Reviewed" line, and a timestamp.
- The left schedule rail uses pastel color-coded appointment cards with visit type and duration (e.g. "PT VISIT 60min"), grouped under hour markers.
- The only money-related widget is Charge Slips, a count of unprocessed billing slips; no currency amounts appear anywhere on the dashboard.
- Counts on the marketing dataset run to four digits (Notes 3469, Rx 3898), and the red urgent badge can overlap the ring, partially obscuring its own number.

Scores: navigation 4 · hierarchy 3 · metric surfacing 4 · pipeline visibility 2 · dataviz 3 · task speed 4 · error prevention n/a · states n/a · mobile n/a

Worth copying:

- Donut-as-filter: each widget is both a status summary and a one-click filter on the adjacent worklist; our invoice-status donut (draft / submitted / with insurer / paid) should filter the invoice table the same way.
- Two-badge convention per widget: a red badge for urgent items and a grey badge for held items reads instantly; map to overdue invoices (red) and disputed/held invoices (grey).
- Progress-as-text in the list header ("Not Signed 169 of 696") gives a concrete sense of remaining work; use "12 of 40 invoices unpaid, GBP 8,400 outstanding" on our worklist.
- Fixed triptych of urgent / total / held summary circles at the top gives a stable landing anchor before the detail widgets; our hero row could be overdue / in-flight / paid-this-month.

Worth avoiding:

- Raw counts without money: Charge Slips shows "910" but never a currency value, so the user cannot judge financial impact; our hero metric must be GBP cashflow, not item counts.
- No pipeline stage view: donuts show category totals, not where an item sits in a multi-step flow; we need a per-invoice timeline (Semble -> Healthcode -> insurer -> paid), which this design cannot express.
- Badge collision at scale: four-digit counts and overlapping red badges become illegible; cap displayed counts (99+) and keep badges outside the ring.
- Nine near-identical donuts flatten priority; everything looks equally urgent, so limit our dashboard to three or four widgets with clearly ranked visual weight.

### C08 — DrChrono

iPad-first US EHR and practice management app for small-practice clinicians who chart, schedule and bill from a tablet.

Navigation model: iPad: bottom tab bar (Dashboard, EHR, Messages, Tasks, Account) + left appointment-list rail with a persistent day filter; each appointment opens a full-screen detail panel. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C08-S1 | iPad appointment detail: billing fields, CDS warnings, Start Visit | video frame |
| C08-S2 | iPad day list with patient header and Eligibility button | video frame |
| C08-S3 | Appointment set to In Session; payment field populated | video frame |
| C08-S4 | Body-diagram annotation tool with pen and colour palette | video frame |
| C08-S5 | eRx pharmacy search over a map, radius slider | video frame |
| C08-S6 | Four-digit PIN login screen on iPad | video frame |

Observations (evidence):

- iPad app uses a bottom tab bar with five items: Dashboard, EHR, Messages, Tasks, Account; Messages carries a red badge count (C08-S1).
- Left rail is a searchable appointment list for the selected day; each row shows patient photo, time, exam room, and a small coloured status dot (C08-S1, C08-S2).
- Appointment detail is a label/value form split into named sections: Appointment Details, Billing Details, Patient Flags, CDS Matches, Vitals; editable values render as blue links (e.g. 'Cash', 'ICD-10', 'None Selected') (C08-S1).
- Billing Details on the appointment screen exposes Payment profile, Co-Pay, Payment, Payment Type, Payment Options and a Billing Status field directly in the clinical view (C08-S1, C08-S2).
- Patient header shows photo, name, sex, age, DOB, plus quick actions: Appointment Options, Super Bill, Vitals, and a prominent outlined 'Start Visit' button (C08-S1).
- CDS Matches section lists rule-based warnings with a red count, e.g. 'Patient must have documented allergies' (C08-S1).
- Status changes use a modal spinner overlay labelled 'Update Appointment Status...'; a yellow banner flags 'This is a sample patient' (C08-S1).
- Older iPad version (2014) includes an 'Eligibility' button with a green check, a schedule button, and appointment status dropdown that can be set to 'In Session' (C08-S2, C08-S3).
- Freehand body-diagram annotation tool offers pen thickness and an 8-colour palette, with 'Embed in Note' as the commit action (C08-S4).
- Login is a 4-digit drchrono PIN rather than full credentials (C08-S6).

Scores: navigation 4 · hierarchy 3 · metric surfacing 2 · pipeline visibility 2 · dataviz n/a · task speed 4 · error prevention 3 · states 2 · mobile 5

Worth copying:

- Put billing fields (payment, co-pay, billing status) inside the appointment record itself: the money conversation starts at the point of care, which matches our invoice-created-at-consult moment.
- CDS Matches pattern: a named section with a red count listing rule violations before the visit proceeds; direct template for our pre-submission validation panel ('2 issues will delay this claim').
- One-tap primary action per screen ('Start Visit', 'Embed in Note', 'Eligibility' with green check): each screen answers one question fast; ours should answer 'when do I get paid?' with equal directness.
- Coloured status dot on every list row so state is scannable before opening the record; apply to invoice rows in the lifecycle list.
- 4-digit PIN login for a device that gets picked up 30 times a day; low-friction re-entry matters for between-patient checks.

Worth avoiding:

- Billing status buried as one 'None Selected' link among ~12 form fields: money state has no visual weight; our invoice status must be a hero element, not a field.
- No aggregate money view surfaced in the clinician flow: cashflow only exists per-appointment, so the user never sees where all their money sits; this is exactly the visibility gap we are solving.
- Blue-link-on-white for every editable value flattens hierarchy; important states (unpaid, rejected) look identical to trivia (exam room).
- Modal blocking spinner for a simple status update; prefer optimistic inline updates with a subtle pending state.
- Dropdowns defaulting to 'None Selected' invite incomplete records that later become claim errors; use required, validated pickers before submission instead.

### C09 — Tebra (ex Kareo)

All-in-one EHR + practice management + billing SaaS for independent US small practices, with a dedicated A/R analytics dashboard.

Navigation model: Web app: teal top bar with module icons (home, clinical, billing, patients, analytics) + persistent patient search; legacy desktop PM: menu bar + icon toolbar + left nav rail. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C09-S1 | A/R Dashboard: KPI tiles, aging bars, top payer balances | real UI |
| C09-S2 | Desktop Practice Home: Payment Velocity gauge, KPIs, To-Do list | real UI |
| C09-S3 | Web dashboard with Analytics menu and Outstanding Items counters | real UI |
| C09-S4 | Billing composite: charge entry, QR pay-online, eligibility badge | marketing render |
| C09-S5 | Video frame: patient facesheet with left-rail chart sections | video frame |
| C09-S6 | Legacy Kareo dashboard: Billing menu, Outstanding Items counts | real UI |

Observations (evidence):

- A/R Dashboard opens with a five-tile 'Summary & Benchmarks' row: Outstanding A/R with donut split (insurance vs patients), Gross collection rate 92%, Total adjustments, Avg days in A/R 32, Credits; each tile has an info tooltip and a short plain-language explainer sentence.
- Below the KPI row sit Insights/Trends tabs; Insights shows an 'A/R aging bucket' horizontal bar chart (Unbilled, 0-30, 31-60, 61-90, 91-120, 121+ days) with dollar and percent labels on every bar, and a 'Top outstanding balances' table by payer (Total Balance, % of A/R, Charges) with a 0+ days filter.
- Both aging chart and payer table carry an Insurance/Patients segmented toggle; the dashboard header shows 'Refresh to update data. Last updated: [timestamp]' plus a filter pill 'Show Aging By: First Billed Date'.
- Desktop PM Practice Home lands on four panels: a Workflow diagram of the billing pipeline (new patient -> track claim status -> send claims -> receive payment -> generate reports), a Payment Velocity gauge showing '38 DAYS' on a green-to-red arc, a To Do List, and a Key Performance Indicators table.
- The To Do List is written as sentences with embedded counts as links: 'You have 23 Claims to send', 'You have 8 Rejected claims that need follow-up', 'You have 1 Denied claim that needs to be resolved', split into daily and monthly closing activities.
- KPI table rows include Charges, Receipts, Refunds, A/R Balance, Days in A/R, Days Revenue Outstanding, Days to Bill, each with Amount and '% Last' delta, switchable Month/Quarter/Year.
- Web dashboard right rail lists 'Outstanding Items' as label + count badges (Flagged Messages 2, Open Notes 0, Tentative Appointments 2, Patient Intake 1); agenda cards show a 'Charge not started' status chip per appointment.
- Navigation in the current web app is a teal top bar of module icons plus an always-visible 'Start typing a patient name or DOB' search; Analytics opens a dropdown (A/R Dashboard, Appointments, Claims, Encounters, Patients, Unsigned Notes).
- Marketing billing composite shows a Services Rendered charge-entry table with a warning triangle icon beside a $0.00 charge amount, an 'Add Procedure Code' inline field, and a patient invoice with QR code 'Pay online' plus phone and mail alternatives.
- Eligibility is surfaced pre-visit: green check 'Eligible for visit on 06/06/2025' on appointment cards and a 'Check Eligibility For All' button on the dashboard.

Scores: navigation 3 · hierarchy 4 · metric surfacing 4 · pipeline visibility 3 · dataviz 3 · task speed 4 · error prevention 3 · states n/a · mobile n/a

Worth copying:

- Payment Velocity as a single named number ('38 DAYS' to get paid) with a gauge — this is literally our reference question; name the metric and make it the hero.
- KPI tiles that pair the number with a one-sentence plain-language explainer and an insurance-vs-patient split — maps directly to our private-vs-NHS comparison toggle.
- A/R aging buckets as horizontal bars labeled with both pounds and percent, toggleable by payer type — the clearest 'where is my money stuck' visual we found.
- To-do list written as actionable sentences with linked counts ('You have 8 Rejected claims that need follow-up') — turns pipeline errors into next actions, good model for our validation failures queue.
- Status chips on operational cards ('Charge not started', green-check eligibility before the visit) — pre-submission validation surfaced at the moment of scheduling, not after rejection.

Worth avoiding:

- Two visual generations coexisting (2015-era desktop PM and modern web app) with different nav models — pick one design language and keep it.
- Pipeline shown as a static workflow diagram of icons rather than live per-invoice status — we should make the timeline data-bearing, not decorative.
- Aging analytics live two clicks away under Analytics > A/R Dashboard while the landing screen is scheduling-centric — for a cashflow product the money view must be the landing view.
- Dashboard requires manual 'Refresh to update data' with a last-updated timestamp — undermines trust in a visibility product; prefer live or clearly auto-refreshed data.
- KPI overload in the desktop table (nine rows of near-synonymous metrics like Days in A/R vs Days Revenue Outstanding vs Days to Bill) — curate to the few numbers a doctor actually acts on.

### C10 — Elation Health

Clinical-first EHR for US independent primary care; a three-panel console keeps chart, timeline, and active note on one screen.

Navigation model: Slim top bar (Practice Home / Find Chart / Reports / Elation Billing) + per-patient icon toolbar (Visit Note, Rx, Orders, Reports, Referral...); no left rail — three side-by-side content panels carry the workload. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C10-S1 | Real three-panel chart: summary, timeline, live visit note | real UI |
| C10-S2 | Bill screen with AI Billing Analysis validation checklist | real UI |
| C10-S3 | Elation Billing dashboard: Charges, Adjustments, Payments, Write Off | real UI |
| C10-S4 | Insights module: revenue KPI list and bar chart | real UI |
| C10-S5 | Practice Home render: schedule, message queue, action feed | marketing render |
| C10-S6 | Elation Go mobile calendar and appointment detail | marketing render |

Observations (evidence):

- Patient chart uses three fixed panels: left = patient summary (allergies, problem list, history), center = searchable chronological record with a 'Requiring Action' section and count badge, right = the active visit note; no navigation is needed between them.
- Practice Home is also three panels: day schedule (left), message queue grouped by type with count badges — Urgent 3, Office Messages 2, Rx Requests 4, Reports, Reminders, Patient Letters, Provider Letters, Draft Notes, Draft Letters (center), and an item feed with a 'Launch First Patient' button (right).
- Top bar has only four global destinations (Practice Home, Find Chart, Reports, Elation Billing) plus account; per-patient actions live in an icon toolbar of ~14 items (Visit Note, Notes, Msg, Rx, Orders, Handouts, Meds Hx, Reports, Referral, Letter, Forms, Care Team, Templates, Note Prep).
- The bill screen shows a 'Billing Analysis' side panel that runs four pre-submission checks, each with a green 'Success' chip and a 'Show Logs' link: AI Coding, Insurance Eligibility ('Verified patient has active primary insurance'), NCCI Edits ('No NCCI coding errors found'), Claim Edits ('Basic clearinghouse validation passed').
- Coding on the bill is a dense editable table (Procedure, Modifiers, Amt $, Qty, Subtotal) with attached Dx rows, a 'Generate Codes' AI button, and inline confidence-style scores (e.g. '0.2') next to ICD codes.
- Elation Billing landing shows four MTD stat cards — Charges $5,438.10, Adjustments $979.53, Payments $3,303.12, Write Off $0.00 — above a Practice Revenue line chart with Practice/Provider/Location toggles.
- Insights reporting offers KPI presets (Revenue-Practice, Revenue-Provider, Revenue-Location, Claims, Charges), a green filter banner (date range, posting date, providers, locations), four output modes (Snapshot, Visualization, Narrative, Printed Reports), and a single-series light-blue bar chart with dropdowns for chart type and granularity.
- Problem list entries carry year, ICD-10 code, and an orange 'Last addressed: Never' flag; allergies render as red bold text; patient header shows pill-style '3 ALLERGIES' (red) and 'RISK 0.40' (orange outline) chips.
- Urgency in the message queue is encoded with color-filled rows (red Urgent, teal selected) plus yellow numeric count badges; the schedule alternates blue/orange appointment cards by type.
- Elation Go mobile app is a separate companion with bottom tab bar (Home, Patients, Calendar, Account); appointment cards show status ('Scheduled'), time range, visit-type tags (SICK, PHYSICAL, FOLLOW-UP) and a Start Video action.

Scores: navigation 4 · hierarchy 4 · metric surfacing 3 · pipeline visibility 3 · dataviz 2 · task speed 3 · error prevention 5 · states n/a · mobile 3

Worth copying:

- The Billing Analysis panel is the exact pattern for our pre-submission validation: named checks (eligibility, coding edits, clearinghouse rules) each with a pass/fail chip, one-line human explanation, and a 'Show Logs' link for detail — run before the invoice leaves the doctor.
- 'Requiring Action' with a count badge as the first section of the workspace: our dashboard should lead with 'invoices needing you' (rejected, missing data, stale) before any charts.
- Count badges on queue categories (Urgent 3, Rx Requests 4) give instant workload triage; apply the same to invoice-lifecycle stages so the pipeline doubles as a to-do list.
- Everything-on-one-screen console: doctor context (practice), work list, and detail panel visible simultaneously means zero navigation to answer the core question — mirror this so 'when do I get paid?' never requires a page change.
- Status chips that combine color + label + code ('Signed' green pill, red allergy text, orange RISK chip) survive scanning at speed; use the same triple encoding for invoice states.

Worth avoiding:

- Money is buried: cashflow KPIs live two hops away inside a separate 'Elation Billing' module and an 'Insights' page, and the landing metric cards are bare MTD totals with no trend, target, or expected-payment date — our product must put cashflow on the first screen.
- Dataviz is an afterthought: default-styled single-series bar/line charts, one color, no annotations, chart-type dropdowns pushed onto the user; ship one opinionated, readable cashflow chart instead.
- The Insights module looks and feels like a different product (different palette, ALL-CAPS green filter banner) from the EHR; keep clinical and financial views in one visual system.
- A 14-icon toolbar works for trained daily users but punishes occasional ones; doctors check finances weekly, so cap primary actions at ~5.
- No visible timeline of where a claim sits after submission (checks are pre-submit only); our status timeline from doctor to Semble to Healthcode to insurer to paid is the differentiator — do not stop at 'submitted'.

### C11 — Practice Fusion

Cloud EHR for small US ambulatory practices, built around fast charting with billing-partner integration rather than native revenue tools.

Navigation model: Flat module nav: older UI uses horizontal top tabs (Home, Schedule, Charts, eRx, Labs, Reports); newer UI a dark icon left rail (Home, Schedule, Tasks, Charts, Messages, Reports) with numeric badges. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C11-S1 | Patient chart facesheet with summary rail and tabbed sections | real UI |
| C11-S2 | SOAP note editor with vitals row and labeled S-O-A-P fields | real UI |
| C11-S3 | New lab order with required-field highlighting and specimen table | real UI |
| C11-S4 | Week schedule with new-appointment modal and provider filters | video frame |
| C11-S5 | Encounter screen showing clinical decision support warning banner | video frame |

Observations (evidence):

- Left rail (newer UI) carries numeric badges on modules: Schedule 4, Tasks 59, and Appointment requests 4, exposing pending work counts at nav level
- Patient chart uses a persistent header band (name, age, DOB) above tabs: Facesheet, Activity, Appointments, Referrals, eScripts, Messages, Documents, Access History
- Open patient charts appear as closable tabs in a bar (Patients / Unsigned Charts / named patients), with a dedicated Unsigned Charts tab tracking incomplete work
- Lab order form marks fields with two yellow-highlight levels labeled 'Required To Save' and 'Required to Order', and required inputs render with yellow backgrounds
- Encounter screen shows a yellow CDS banner: 'Documentation: Current medication allergies not documented.' before signing
- Encounter status is displayed as a plain text field 'STATUS: Unsigned' next to Save and Sign buttons
- Empty states are written as explicit sentences: 'No known drug allergies', 'No chief complaint recorded.'
- SOAP note auto-computes BMI from height/weight fields in a single vitals strip; sections are labeled by single letters S, O, A, P in the left gutter
- Schedule week view color-codes appointments by type/status and offers a chief-complaint free-text field inside the new-appointment modal
- No revenue, claims, or cashflow widgets appear in any captured screen; Reports is a single nav item and billing is handled through partner integrations per the vendor site

Scores: navigation 4 · hierarchy 3 · metric surfacing 2 · pipeline visibility 2 · dataviz n/a · task speed 2 · error prevention 4 · states 3 · mobile n/a

Worth copying:

- Two-tier required-field highlighting ('Required To Save' vs 'Required to Order') maps directly to our pre-submission validation: distinguish 'can save draft invoice' from 'can submit to Healthcode'
- Nav badges with pending counts (Tasks 59, Unsigned Charts) give a zero-click sense of queued work; use the same for invoices stuck at each pipeline stage
- Inline warning banner before signing ('allergies not documented') is the right moment for validation: warn at submit time, in context, not in a separate report
- Explicit sentence empty states ('No known drug allergies') remove ambiguity between 'no data' and 'not checked'; apply to invoice states like 'No insurer response yet'

Worth avoiding:

- Status as bare text ('STATUS: Unsigned') with no color, icon, or timeline; our status chips should combine all three and link to a lifecycle view
- Financial visibility outsourced to partner tools: the doctor never sees money in the main product, which is exactly the zero-visibility pain we solve; keep cashflow on the landing screen
- Dense multi-level tab nesting (module tabs, patient tabs, chart tabs, section tabs) forces recursive scanning; keep our hierarchy to two levels
- No charts anywhere on operational screens; a dashboard product cannot follow suit since trend context is our hero content

### C12 — CareCloud

Cloud practice-management + EHR suite for US ambulatory clinics, built around badge-counted worklists for scheduling, charting, and claims billing.

Navigation model: Top bar of ~12 icon-only app buttons with numeric badges, browser-style sub-tabs per open record, left rail of filterable worklist counts. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C12-S1 | Billing Encounters worklist with unfulfilled-encounter counts | video frame |
| C12-S2 | Claims inbox filtered to 20 error-state claims | video frame |
| C12-S3 | Charge entry form with ICD-10 codes and totals | video frame |
| C12-S4 | Scheduler kanban: Upcoming, In Progress, Completed columns | video frame |
| C12-S5 | Task inbox with Sign/Approve/Review/Fulfill counters | video frame |

Observations (evidence):

- Top navigation is a row of roughly 12 colored icon-only app buttons, most carrying numeric badges (e.g. 120, 155, 147, 37); open records appear as closable browser-style tabs below.
- Billing Encounters left rail shows a count-labeled pipeline: All 306, Unfulfilled Encounters 146, Saved 9, Posted Pending Submit 151.
- Claims module splits into Inbox (148) with Ready (128) and Errors (20) sub-buckets plus Outbox (0); error rows carry red or yellow warning triangle icons per claim.
- Claims sidebar has a 'Filter Error Type' checkbox list (Physicians, Entity Setup, Patient Demographics, Insured, Encounter, Case, Insurance Policy, Location Setup) and a 'Reassemble All Claims' primary button.
- Encounter tables are dense: 30+ rows visible with columns Patient Name, Date of Service, Encounter Status, Nature of Visit, Insurance Profile, Prov, Loc, Unbilled, Value; a footer row totals amounts.
- Charge entry form auto-calculates Total Amount, Total RVU, and Total Value from CPT/ICD-10 line items, with 'Save for Later' and green 'Post Charges' actions and a 'Skip Charge Routing Validation' checkbox.
- Required charge-entry fields (Provider, Location, Insurance Profile) are marked with red asterisks; diagnosis fields use lookup buttons in a 12-slot ICD-10 grid.
- Scheduler is a three-column kanban (Upcoming, In Progress, Completed) with patient photo cards, status timers, greyed 'EXAM ROOM AVAILABLE' placeholder slots, and a 'Drop Item Here' drag target.
- Task inbox shows a segmented counter strip: Sign 2577, Approve 10, Review 87, Fulfill 478, All 3228, above a checkbox task list sortable 'Present to Past'.
- No charts, graphs, or financial trend visualizations appear anywhere in the captured billing or charting flows.

Scores: navigation 3 · hierarchy 3 · metric surfacing 2 · pipeline visibility 4 · dataviz n/a · task speed 2 · error prevention 4 · states 2 · mobile n/a

Worth copying:

- Count-labeled pipeline buckets in the left rail (Unfulfilled 146 / Saved 9 / Posted Pending Submit 151) map directly to our invoice-lifecycle stages: show live counts per stage so backlog is visible before opening anything.
- Errors as a first-class inbox bucket with per-cause filters (Patient Demographics, Insurance Policy, etc.) is a strong model for our pre-submission validation: group failed invoices by fix type, not just flag them.
- Row-level severity icons (red vs yellow triangles) plus a bulk 'Reassemble All Claims' action: pair per-invoice error signals with one-click batch resubmission after fixes.
- Live-computed totals in the entry form (Total Amount updates as line items change) gives immediate feedback before posting; do the same for invoice value during creation.

Worth avoiding:

- Icon-only top navigation with unlabeled colored squares forces memorization; our doctors are occasional users, so label every nav item.
- Badge-count overload (a dozen competing red numbers) buries the one metric that matters; make cashflow the single hero, not another badge.
- No money-over-time view anywhere in the billing flow: counts and totals exist but nothing answers 'when do I get paid'; our status timeline and cashflow chart are the differentiators.
- Uniform 30-row table density with 9+ columns and no visual grouping makes scanning slow; use progressive disclosure and stage-colored status chips instead.
- Escape hatches like 'Skip Charge Routing Validation' undermine data quality; keep validation mandatory before submission to Healthcode.

### C13 — SimplePractice

All-in-one practice-management EHR (scheduling, notes, billing, telehealth) for US solo and small-group health practitioners.

Navigation model: Fixed left rail (Calendar, Clients, Billing, Insurance, Analytics, Account Activity, Reminders, Settings) plus dark top bar with client search, live monthly-income readout, and Create / Requests / Messages actions. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C13-S1 | Signup form with live password requirement checklist | real UI |
| C13-S2 | Clients and contacts list with left rail | real UI |
| C13-S3 | Week calendar with Learn the basics onboarding checklist | real UI |
| C13-S4 | Appointment flyout: fee, Unpaid invoice chip, Add Payment | real UI |
| C13-S5 | Global Create menu: client, appointment, availability | real UI |

Observations (evidence):

- Left rail has eight fixed items in workflow order: Calendar, Clients, Billing, Insurance, Analytics, Account Activity, Reminders, Settings; Reminders carries a red count badge.
- Top bar persistently shows a mini sparkline icon with 'Jul income $100.00' on every screen, next to global client search.
- Appointment flyout on the calendar combines schedule fields, service code (e.g. '90834 Psychotherapy, 45 min'), Fee, Billing Type ('Self-pay'), Appointment Total, invoice link 'INV #3' with a pink 'Unpaid' pill, 'Client Balance: $200', and a green 'Add Payment' button in one panel.
- Calendar offers Day/Week/Month segmented toggle, Today button, an Availability mode, and green appointment blocks with time and client name.
- A 'Learn the basics' onboarding checklist overlays the first-run calendar with a 0% progress bar and six tasks (e.g. 'Create a test client', 'Sign up for online payments').
- Signup form validates password inline against four listed requirements and masks the phone field as '(___) ___-____'.
- Global '+ Create' menu exposes three actions: Create client, Schedule appointment, Add availability.
- Clients list is a low-density three-column table (Name, Contact info, Relationship) with an 'Adult' tag, per-row Manage dropdown, and a 'Sort: last name' control.
- Left rail footer includes a 'Download free app' button and a 'Privacy Off' toggle that blurs client names when on.
- No analytics-dashboard screenshots were capturable (help center behind Cloudflare); the Analytics nav item is visible but its charts are not in evidence.

Scores: navigation 4 · hierarchy 4 · metric surfacing 3 · pipeline visibility 2 · dataviz n/a · task speed 3 · error prevention 3 · states 3 · mobile 2

Worth copying:

- Persistent month-to-date income readout in the top bar: cashflow visible from every screen, not just a dashboard tab — matches our cashflow-as-hero value prop and goes further than a landing page.
- Invoice status pill ('Unpaid') attached directly to the clinical event that generated it, with fee, balance, and an Add Payment action in one flyout — a model for tying each appointment to its invoice lifecycle step.
- Inline requirement checklist during input (password rules turn into checkable bullets) — reuse this pattern for pre-submission Healthcode validation so errors are fixed before sending.
- Onboarding checklist with progress bar as the empty state, ending in 'Sign up for online payments' — a good template for first-run setup of Semble/Healthcode connections.
- Privacy toggle that blurs patient names — cheap trust win for doctors demoing or screen-sharing financial views.

Worth avoiding:

- Money is fragmented across three nav items (Billing, Insurance, Account Activity), so no single view shows where an invoice sits in the chain — exactly the visibility gap we are solving; keep one lifecycle timeline instead.
- 'Unpaid' is the only visible payment state; a binary paid/unpaid chip hides the submitted → insurer-processing → remitted stages our users need.
- Analytics is buried as a mid-rail item with no chart preview elsewhere; if cashflow is the product's point, the landing screen should be the chart, not a calendar.
- Client balance shown as a bare underlined figure ('Client Balance: $200') with no aging or due-date context — avoid unqualified balances in a latency-focused product.

### C14 — Jane App

Schedule-first clinic management and billing platform for small allied-health and private practices.

Navigation model: Persistent top tab bar (Schedule, Patients, Staff, Billing, Reports, Settings) with a contextual left sidebar per module. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C14-S1 | Week schedule with color-coded appointment status blocks | marketing render |
| C14-S2 | Patient profile stat row with outstanding-balance action card | marketing render |
| C14-S3 | Patient billing tab: dual insurer and patient invoice rows | marketing render |
| C14-S4 | Accounts Receivable report with aging buckets per patient | marketing render |
| C14-S5 | AR report by insurer with print and export menu | marketing render |
| C14-S6 | Insurer claims list with two-level Submitted/Paid status | marketing render |

Observations (evidence):

- Top navigation is a fixed teal tab bar; the Schedule tab sits first and is the default landing module.
- Schedule view is a staff-column week grid; appointment blocks are color-coded (red striped, green, teal, grey) and carry inline icons for group visits, payment-linked visits, and telehealth.
- Left sidebar in Schedule holds patient search and a selectable staff roster; in Billing and Reports it becomes a report/claim-type list (Payroll, Billing, Claim Submissions, Insurer Invoices).
- Patient profile header shows a horizontal stat row: No Shows, Days Since Last Visit, Claims Outstanding ($545.00), Private Outstanding ($240.00), Credit, Private Balance.
- A 'Billing Notices' card states the balance in a sentence ('Owen has a balance of $240.00') with three buttons: Email Reminder, Text Reminder, and a teal Receive Payment primary.
- Each visit generates two linked invoices shown in one table cell: 'Insurer Invoice 617-C01 Canada TELUS eClaims' and 'Patient Invoice 617-P01 [name]'.
- Invoice status is a two-line chip pair per row: briefcase icon + insurer state (Submitted / Paid) and person icon + patient state (Paid / No Charge); overdue balances render in red, settled in green.
- Insurer claim screen header repeats the stat-row pattern: 21 Open Policies, $312.00 Unpaid Invoices, $0.00 Available Credit, above a filterable claims table.
- Accounts Receivable report is a dense table with aging bucket columns (Amount Owing, 0-30 Days, 31-60 Days, 61-90 Days), filter dropdowns for Location/Staff/Account Type, and Print/Export to Excel/CSV actions.
- All captured reporting screens are tables; no charts appear in any captured screen.

Scores: navigation 4 · hierarchy 4 · metric surfacing 3 · pipeline visibility 4 · dataviz 2 · task speed 3 · error prevention n/a · states n/a · mobile n/a

Worth copying:

- Two-level status chip per invoice (payer state + patient state, each icon + color + label) maps directly to our doctor->Semble->Healthcode->insurer chain; extend to three or four hops on one row.
- Stat-row header above every detail table (Claims Outstanding, Private Outstanding, Credit) puts money numbers before the data grid; use the same pattern with cashflow as the first tile.
- Splitting each visit into a linked insurer invoice and patient invoice with shared numbering (617-C01 / 617-P01) gives clean private-vs-payer separation, the analogue of our private-vs-NHS split.
- Aging buckets (0-30/31-60/61-90) as first-class table columns answer 'how late is my money' at a glance; pair them with expected-payment dates.
- Plain-sentence balance card with the action inline ('Owen has a balance of $240.00' + Receive Payment) collapses read-then-act into one widget.

Worth avoiding:

- No cashflow or revenue chart anywhere on landing; the money picture lives behind Reports > Accounts Receivable, so 'when do I get paid' takes several clicks. Make it the hero screen instead.
- Table-only reporting with Export to Excel as the escape hatch signals the product does not answer trend questions itself; we should chart latency and cashflow natively.
- Status vocabulary stops at Submitted/Paid; nothing shows where a claim sits between those states, which is exactly the black hole our timeline must fill.
- Schedule-first landing suits front-desk staff but buries finances; for a cashflow product, do not inherit the calendar-as-home default.

### C15 — Healthie

Wellness-focused EHR whose provider home is a day organiser: today's appointments beside a prioritised task list, for solo and group practices.

Navigation model: Dark labeled left rail (Home, Chat, Clients, Calendar, Billing, Reports...) + persistent top client search; home content under Overview / Journal Entries / Dashboard tabs. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C15-S1 | Provider home: appointments list beside grouped task list | real UI |
| C15-S2 | Journal Entries tab: client metric and food-log feed | real UI |
| C15-S3 | Dashboard tab: appointment bar charts and outcome pies | real UI |
| C15-S4 | Current home with labeled rail and Smart Tasks tab | real UI |
| C15-S5 | Billing card: payment methods, dated claim chips | marketing render |

Observations (evidence):

- Home is a two-column layout: Appointments (left) and Tasks (right) under a time-of-day greeting ('Good afternoon, Dr. Melanie').
- Appointments have sub-tabs with counts in the labels: 'Today (3)', 'Week (6)', 'Unconfirmed (3)'; the list is grouped into collapsible PAST / UPCOMING sections with counts.
- Each appointment card shows a time block, client avatar, visit type ('Healthie Video Call - Initial Assessment'), duration, an orange all-caps status chip ('UNCONFIRMED' / 'UNCONFIRMED BY CLIENT'), and an inline 'Confirm' action.
- Tasks panel splits into 'My Tasks' / 'Smart Tasks (10)' tabs and collapsible groups 'CREATED BY ME', 'ASSIGNED TO ME', 'COMPLETED', each with a count; tasks carry due dates and assignee avatars.
- Empty task group shows an illustration with the caption 'All tasks completed!'.
- Left rail lists 13 labeled modules including Billing, Reports, Labs, Faxing; a red badge on the top bell icon shows unread count.
- The home's Dashboard tab shows bar charts of appointments per month with numeric labels on every bar (future months rendered as 0) and pie charts of appointment outcomes where 'Occured 409 (99%)' dwarfs three 0% slices; a 'View Organizational Dashboard' button sits above.
- No revenue, payments, or claims figures appear anywhere on the provider home; billing lives in a separate rail item.
- Marketing billing card lists claims as date + pill-label rows ('05/12/23 Prescription Payment') with a 'View All Claims' link and shows the primary payment method as a 'VISA*4160' chip.

Scores: navigation 4 · hierarchy 4 · metric surfacing 2 · pipeline visibility 2 · dataviz 2 · task speed 2 · error prevention n/a · states 3 · mobile n/a

Worth copying:

- Counts embedded in tab and group labels ('Unconfirmed (3)', 'MY TASKS (3)') triage workload before a single click; do the same for invoice states ('Rejected (2)', 'Awaiting insurer (14)').
- Status chip plus inline action on the same row ('UNCONFIRMED' + 'Confirm') resolves an exception without leaving the list; pair our 'Validation failed' chip with an inline 'Fix' action.
- Time-of-day greeting and a today/week split make the landing feel like 'your day'; frame our hero as 'cash expected this week' vs 'this month'.
- Positive empty state ('All tasks completed!' with illustration) rewards a clean queue; use one for 'No invoices need attention'.

Worth avoiding:

- No money metric on landing: billing is buried in a rail item, so 'when do I get paid?' takes several hops. Cashflow must be the hero card on our home.
- Pie charts where one slice is 99% and three are 0% convey nothing; use a horizontal stacked bar or status-count row for invoice outcomes.
- Bar charts that plot future months as labeled zeros make the trend read as a collapse; truncate the axis at the current period.
- Status vocabulary describes only one hop ('unconfirmed by client'); our chips must name the pipeline stage (with Semble / at Healthcode / at insurer), not just a binary state.

### C16 — Xero Analytics Plus

Syft-powered analytics layer inside Xero giving small-business owners a Business Snapshot dashboard and a paid short-term cash flow projection.

Navigation model: Xero global top nav (Dashboard/Business/Accounting/...) with Snapshot under Accounting > Reporting; Analytics itself uses horizontal tabs (Profitability, Cash, P&L accounts, Balance Sheet accounts, KPIs) plus a filter-dropdown toolbar. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C16-S1 | Business Snapshot: Profitability, Efficiency, Financial position sections | real UI |
| C16-S2 | Short-term cash flow projection with projected end balance | video frame |
| C16-S3 | Syft-powered Analytics: Net cash flow tab with filters | real UI |
| C16-S4 | Early-access Analytics banner on the Xero dashboard | real UI |
| C16-S5 | Marketing render of chart hover and Top transactions drill-down | marketing render |
| C16-S6 | Syft dashboard marketing shot with AI Insights callout | marketing render |

Observations (evidence):

- Business Snapshot sits under an Accounting > Reporting breadcrumb inside Xero's global top nav (Dashboard, Business, Accounting, Payroll, Projects, Contacts) and carries a Pilot tag.
- Snapshot groups all content into three labeled sections: Profitability, Efficiency, and Financial position and cash.
- KPI cards pair a large number with a colored up/down arrow, a comparison line ('3% from FY18'), and a plain-English footnote such as 'Profit is the amount of money made after paying expenses'.
- A dedicated card reads 'Average time to get paid: 30 days' with a red delta arrow and an 'Outstanding receivables: 2,000' subline; a matching card shows 'Average time to pay suppliers: 14 days'.
- Income and expense charts overlay the current year as a solid line and the prior year as a dashed line on shared axes.
- The 'Largest operating expenses' table lists five categories with FY19/FY18 columns and per-row red/green direction arrows.
- The Short-term cash flow projection page carries a green 'Plus' plan tag, a 'Projected end balance -$2,535' headline, a line chart colored green above zero and red below with a shaded Today marker, and a collapsible 'Projection breakdown' section.
- The Syft-powered Analytics screen uses horizontal tabs (Profitability, Cash, Profit and Loss accounts, Balance Sheet accounts, KPIs) with a toolbar of dropdowns: metric selector, Monthly, month, year, Graph options, and an Export button.
- A purple badge on the Analytics chart states 'We're showing you demo data' when real data is absent.
- The Xero dashboard surfaces Analytics through an 'Early access' banner ('Visualize your financial performance in new ways with Xero Analytics powered by Syft') with an Access visualizations button.

Scores: navigation 4 · hierarchy 4 · metric surfacing 4 · pipeline visibility 2 · dataviz 4 · task speed 3 · error prevention n/a · states 3 · mobile n/a

Worth copying:

- KPI card grammar: big number + delta arrow + 'X% from last period' + one-line plain-English explainer; ideal for doctors who are not accountants.
- Cashflow projection chart colored green above zero and red below, with a Today marker and a single 'Projected end balance' headline; direct template for our cashflow hero metric.
- 'Average time to get paid' as a first-class named metric; we can split it per insurer to expose payment latency in the Semble-Healthcode-insurer chain.
- Solid-vs-dashed line pairing for period comparison; reusable as the private-vs-NHS income comparison.
- 'We're showing you demo data' badge: an empty state that still teaches the layout before real data arrives.

Worth avoiding:

- Projection stops at the balance level; there is no drill-down to which invoice pays when, which is exactly the per-invoice timeline gap we fill.
- Receivables shown as one aggregate number ('Outstanding receivables: 2,000') with no status breakdown; the pipeline stays invisible.
- Gating the cashflow projection behind a paid 'Plus' tag inside the product; for our users the cashflow view is the product, not an upsell.
- Full-width single-series charts (Net cash flow tab) leave large empty regions; keep the denser multi-card snapshot layout instead.

### C17 — QuickBooks Online

Market-leading small-business accounting suite whose dashboard splits into an action-oriented "Get things done" tab and a metrics-oriented "Business overview" tab.

Navigation model: Dark left rail (14+ modules, customizable with bookmarks) + persistent "+ New" mega-button + per-page horizontal tabs + top search/help/gear. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C17-S1 | Business overview: cash flow forecast, P&L, expenses, invoices | real UI |
| C17-S2 | Invoices list with money bar and Receive payment actions | real UI |
| C17-S3 | Get things done tab: task shortcut grid, bank accounts | real UI |
| C17-S4 | Customers page with segmented estimate-to-paid money bar | real UI |
| C17-S5 | Banking: account cards, bank vs QuickBooks balance, review queue | real UI |
| C17-S6 | +New menu grouped by Customers, Suppliers, Employees, Other | real UI |

Observations (evidence):

- Dashboard has two tabs: 'Get things done' (default; a grid of 8 icon shortcuts like Add invoice, Receive payment, Pay bill) and 'Business overview' (metric cards).
- Business overview leads with a full-width 'Cash flow forecast' bar chart: paired Money in (green) / Money out (teal) bars per month, a 'TODAY' marker, and hatched bars for forecast months.
- Empty cash flow chart is labeled with a SAMPLE badge and a pill-shaped CTA 'Link a bank account to see your cash flow'.
- Invoices widget on the dashboard is two horizontal stacked bars: Unpaid split into Overdue (orange) vs Not due yet (grey), and Paid split into Not deposited (light green) vs Deposited (dark green), each with dollar totals and time windows (Last 365 days / Last 30 days).
- The Sales > Invoices page repeats the same money bar at full width above a table with columns Date, No., Customer, Amount, Status, Action; status cells show an orange warning icon plus text like 'Overdue 47 days' or 'Due in 29 days'.
- Every invoice row carries an inline 'Receive payment' action plus an edit pencil and a dropdown for more actions.
- Customers page shows a five-segment colored money bar spanning Estimates (blue) -> Unbilled activity (blue) -> Overdue (orange) -> Open invoices (grey) -> Paid last 30 days (green), each segment showing amount and count.
- Banking page shows per-account cards contrasting 'Bank balance' with 'In QuickBooks' balance and a count badge of transactions awaiting review, with For review / Categorized / Excluded tabs.
- A 'Privacy' toggle on the dashboard hides all monetary amounts; a 'Customize' control (Beta) lets users rearrange overview widgets.
- The '+ New' button opens a four-column menu grouped by Customers / Suppliers / Employees / Other, with Invoice and Receive payment as the top two items.

Scores: navigation 4 · hierarchy 4 · metric surfacing 4 · pipeline visibility 4 · dataviz 3 · task speed 4 · error prevention n/a · states 4 · mobile n/a

Worth copying:

- The two-stage invoice money bar (Unpaid: Overdue vs Not due yet; Paid: Not deposited vs Deposited) maps directly onto our doctor->Semble->Healthcode->insurer pipeline: render each lifecycle stage as a labeled segment with amount + count, in one glance-able strip.
- Repeat the same money bar on both the dashboard widget and the full Invoices page so the mental model carries across zoom levels.
- Empty-state pattern: show a SAMPLE-badged chart of what cashflow will look like plus one CTA ('Link a bank account'); we should preview the status timeline before Semble/Healthcode data is connected.
- Inline 'Receive payment' action on every invoice row keeps the get-paid task one click from the answer; our rows should carry 'chase' or 'fix error' actions the same way.
- Status text encodes urgency with a number ('Overdue 47 days'), not just a color chip; days-stuck-at-stage is more actionable than a bare 'pending' label.

Worth avoiding:

- Defaulting the landing tab to a shortcut grid with zero metrics ('Get things done'); our cashflow number must be the first thing on screen, not behind a second tab.
- Splitting bank balance vs in-app balance without explaining the delta; if we show Healthcode-submitted vs bank-received amounts, reconcile them explicitly or doctors will distrust the numbers.
- A 14+ item left rail (Payroll, Mileage, Projects...) buries the two or three jobs a solo practitioner has; keep our nav to a handful of items.
- Donut chart for expenses adds little over a ranked list at small-practice scale; skip decorative charts in favor of the cashflow bar and the status pipeline.

### C18 — Fathom

Financial analysis, KPI-tracking and management-reporting layer over Xero/QuickBooks/MYOB, built for accountants and advisors managing client portfolios.

Navigation model: Slim icon-only left rail (portfolio, insights, reports) under a dark top bar; page-level toolbar with Search / Sort / Filters and a plain-language period selector top-right. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C18-S1 | Insights Dashboard: portfolio table with KPIs and sparklines | real UI |
| C18-S2 | Summary report builder with template page gallery | real UI |
| C18-S3 | Metric Drill Down modal with two-year trend comparison | real UI |
| C18-S4 | Thresholds screen assigning threshold groups per company | real UI |
| C18-S5 | Tags settings with inline empty states | real UI |
| C18-S6 | Branded cover page of a management accounts report | marketing render |

Observations (evidence):

- Insights Dashboard lands on aggregate KPIs (Revenue $246,261 +0.45%, Expenses $146,291 -0.2% labelled 'Avg value and growth') above a table of 81 companies.
- Each table row packs three signals per metric: absolute value, a color-coded growth chip (green/amber/red percentage), and a 12-month sparkline.
- Period control reads as a sentence: 'For the Month of Jan 2025', with underlined editable words for granularity and period.
- Filter bar shows chip dropdowns for Revenue, Expenses, Tags (with active-count badge '2'), Thresholds and Companies, plus a 'Clear all filters' link.
- Clicking a metric opens a 'Metric Drill Down' modal over the dimmed dashboard: Revenue and Expenses cards with 'vs last month' deltas, a 2-year line chart against a dotted comparison series, and a 'Summary report' link.
- Report builder presents prebuilt page templates (Revenue & Expenses, Profitability, Cash flow, Assets & Liabilities, Debt & Equity, Working Capital) as a checkbox gallery of page thumbnails.
- Thresholds screen assigns a named threshold group per company ('Construction %', 'Information Technology %'); subtitle states thresholds 'better visualise the status of dashboard metrics'.
- Every company row in Thresholds lists its source system underneath (QuickBooks, Xero, Excel, Sage Business Cloud, Access Financials).
- Tags settings uses inline empty states: 'You don't have any tags in this category yet. Would you like to add a tag?' with the action as a text link.
- Sample management reports open with full-bleed branded cover pages carrying the client logo, report title and period.

Scores: navigation 4 · hierarchy 4 · metric surfacing 5 · pipeline visibility 1 · dataviz 4 · task speed 3 · error prevention 2 · states 3 · mobile n/a

Worth copying:

- Triple-signal metric rows (value + colored delta chip + sparkline) compress a lot into one scan line; apply to per-insurer outstanding balance and payment-latency rows.
- Drill-down as a modal over the dimmed dashboard preserves context; use the same move for opening an invoice's status timeline from the cashflow view.
- Plain-language period selector ('For the Month of Jan 2025') with inline editable words beats a date-picker widget for report framing.
- User-defined threshold groups drive chip colors, turning raw numbers into red/amber/green status; map this to payment-latency SLAs per insurer.
- Report builder as a visual checkbox gallery of prebuilt pages lets an accountant assemble a client pack in seconds; reuse for private-vs-NHS comparison packs.

Worth avoiding:

- No process pipeline anywhere: Fathom tells you what the numbers are, never where money sits in a multi-step flow, which is exactly the gap our invoice timeline fills.
- Source system is displayed but data is trusted as-is; no pre-report validation or error flags, so bad Semble/Healthcode data would flow straight into charts.
- Layout is tuned to multi-company portfolios; a single-practice doctor needs one hero entity with cashflow front and center, not an 81-row comparison table.
- Sparklines carry no axis or values, fine for trend glance but useless for 'how much and when', which is our user's core question.

### C19 — Syft Analytics

Card-based financial dashboard builder for accountants and SMBs, acquired by Xero to power Xero Analytics.

Navigation model: Dark left rail grouped into Favorites / Tools / Configure, with entity switcher and global period selectors (Monthly / month / year) in a top bar. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C19-S1 | Dashboard home: left rail, KPI cards, period selectors | real UI |
| C19-S2 | Expenses dashboard with donut charts and custom image card | real UI |
| C19-S3 | Balance sheet table card beside cash-in-vs-out charts | real UI |
| C19-S4 | Options menu: presentation mode, template, favorites | real UI |
| C19-S5 | Per-card AI explain button under each chart | real UI |
| C19-S6 | Card settings popover: size, type, color picker | real UI |

Observations (evidence):

- Every KPI card uses one repeated header pattern: metric name, trend arrow with percent change (e.g. 'Debtors days 98.3%'), current value in color, and grey 'balance last year' / 'average last year' comparison text.
- Dashboard grid is configurable via two dropdowns in the toolbar: '12 periods' and '3 columns', plus an 'Add card' button and a 'Loop animations' play toggle.
- Global context bar pins frequency (Monthly), month (Oct) and year (2024) selectors top-left; the subtitle spells out the exact comparison range: 'GBP, November 01 2023 - October 31 2024 vs November 01 2022 - October 31 2023'.
- Chart types on cards: single-series bar, area-filled line, dual-series bar (teal vs navy/green for prior year), donut with legend, and a hierarchical balance-sheet table card with expandable rows (Current Assets > Bank Accounts > Cash and cash equivalents) and right-aligned totals.
- Each card carries a gear icon opening a settings popover with Card size, Card type (bar / line / number), a full hex color picker, preset swatches, an 'Update all graphs' toggle, and Cancel / Confirm buttons.
- An 'AI' pill button sits centered under every chart; a top-right 'AI NEW' button, Download, and Options (Presentation mode, Add to template, Read a help article, Add to favorites) complete the page actions.
- Debtors days and Creditors days appear as first-class dashboard cards (e.g. '46.4 days' vs '2679.7 days balance last year').
- A 'Saving...' text indicator appears next to Share dashboard / Save during autosave; dashboards are shared 'as unique links'.
- Left rail Visualize section lists Dashboard, KPIs & Accounts, Profitability, Cash, Customers, Suppliers, Products; 'UPDATED' badges mark recently changed modules.
- Cards accept free content too: an 'Enter a description' placeholder under each chart and an uploaded cupcake image used as a card.

Scores: navigation 4 · hierarchy 4 · metric surfacing 5 · pipeline visibility 2 · dataviz 4 · task speed 3 · error prevention 2 · states 2 · mobile n/a

Worth copying:

- The card header formula (metric name + trend arrow + percent delta + current value + grey prior-period comparison) answers 'is this good or bad' in one glance; use it verbatim for cashflow and days-to-payment cards.
- Debtors days as a first-class KPI card maps directly to our 'when do I get paid' question; pair the number with a per-insurer breakdown.
- Spelling the exact comparison date range in plain text under the dashboard title ('GBP, Nov 01 2023 - Oct 31 2024 vs ...') removes ambiguity about what a delta means; do this for private-vs-NHS and period comparisons.
- Dual-series bars (current vs prior year in two colors on one card) are a compact private-vs-NHS comparison pattern.
- Share-as-unique-link plus Presentation mode is a cheap way for a doctor to hand cashflow evidence to an accountant or practice manager.

Worth avoiding:

- No status or pipeline view anywhere: money is summarized (debtors days) but you cannot see where an individual invoice sits; our invoice timeline must fill exactly this gap.
- Two teal-on-teal series without an on-card legend (Cash card) forces guessing which bar is which year; always label both series.
- Freeform card settings (any hex color, any card type, uploaded images) suit accountants building client decks but add decision overhead for a doctor who wants one canonical dashboard; ship strong defaults instead of a builder.
- An 'AI' button under every single chart is repetitive chrome that competes with the data; one contextual entry point is enough.
- '> 999%' shown as a trend value is noise from unbounded percent math; cap or reword extreme deltas ('new this year').

### C20 — Stripe Dashboard

Payments operations console for online businesses: balances, payment lifecycle, invoicing, and configurable revenue analytics in one web app.

Navigation model: Horizontal top tab bar (Home, Payments, Balances, Customers, Products, Reports, Connect, More) + contextual left sub-nav per module + global omnisearch. Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C20-S1 | Payments list with status tabs and Succeeded chips | video frame |
| C20-S2 | Home page: Today section, balance, payouts, overview charts | real UI |
| C20-S3 | Global search with inline status chips and payout date | video frame |
| C20-S4 | Create invoice form with live email preview | video frame |
| C20-S5 | Overview date-range picker with preset periods | real UI |
| C20-S6 | Reports overview edit mode: reorder and toggle charts | video frame |

Observations (evidence):

- Home landing stacks a 'Today' section (Gross volume with intraday line chart, USD balance, 'Estimated future payouts', Payouts) above a 'Your overview' chart row.
- Payment status is a colored pill with label plus icon: green 'Succeeded' with checkmark, blue 'Open'; the payments list also filters by status tabs All / Succeeded / Refunded / Uncaptured / Failed.
- Payments table columns are Amount+currency, status chip, Description (invoice number or payment id), Customer email, Date, overflow menu; one row per payment, checkbox per row.
- Global search returns mixed entities (payments, customers, quotes) with amount, id, status chip, and date inline in the dropdown, plus a 'Show all results' action.
- Payouts panel on Home states the expected settlement date ('£317.69, Expected Feb 21') and 'available instantly' amount next to the balance.
- Overview charts show current period as a solid line and previous period as a lighter ghost line, with a delta badge (e.g. '+2.4%', '-2.8%') beside each KPI number.
- Charts are user-configurable: an Edit mode allows drag-to-reorder, hide/show, and a 'Select charts' checklist grouped by category (Payments, Billing: MRR, Churned revenue, LTV...).
- Date-range picker offers presets (Today, Last 7 days, Last 4 weeks, ... All time) plus dual-month calendar, and a Compare control with Previous period/week/month/year/Custom.
- Test mode is a global toggle with a persistent orange 'TEST DATA' banner across every page; a yellow banner on invoice creation explains the customer will not be charged.
- Invoice creation shows a live preview pane with Email / Invoice PDF / Payment page tabs and a 'Review invoice' button as the final gate before sending; invoice list has Draft / Outstanding / Past due / Paid tabs.

Scores: navigation 5 · hierarchy 4 · metric surfacing 5 · pipeline visibility 4 · dataviz 4 · task speed 5 · error prevention 4 · states 3 · mobile n/a

Worth copying:

- Status chip formula: color + icon + label ('Succeeded' + check, green) and status-named list tabs (Draft/Outstanding/Past due/Paid) — map directly to our invoice lifecycle stages (Submitted to Semble / At Healthcode / With insurer / Paid).
- Answer 'when do I get paid?' on the landing page: Stripe pairs balance with 'Estimated future payouts' and an explicit expected date ('Expected Feb 21') — our cashflow hero metric should state a date, not just an amount.
- Previous-period ghost line + delta badge on every KPI chart is a cheap, legible comparison pattern — reuse it for private-vs-NHS and month-over-month cashflow.
- Global search that returns invoices with amount, status chip, and date inline — a doctor can check one patient's invoice without opening any module.
- Pre-send review gate with live preview of exactly what the recipient sees — mirrors our pre-submission validation step before an invoice leaves for Healthcode.

Worth avoiding:

- Eight top-level modules plus 'More' is overkill for a single-doctor practice; our nav should stay at 4-5 destinations.
- Description column showing raw ids (pi_3KT27vFX...) when no invoice number exists — never surface opaque ids to non-technical clinicians.
- Chart edit mode with 15+ toggleable metrics adds configuration burden; doctors need one opinionated cashflow view, not a BI builder.
- Empty invoice list renders a bare table under onboarding cards with no guidance in the table itself — our empty states should show the pipeline skeleton and next action.

### C21 — Semble

UK private-practice management system (ex-Heydoc) with patient records, invoicing, and a Healthcode integration for insurer billing; what our doctor uses today.

Navigation model: Flat top module bar (Appointments, Patients, Tasks, Labs, Letters, Invoices, Products, Contacts, Analytics, Settings) plus a left sub-nav inside the patient record (Invoices, Account statements, Letters, Communications, Documents, Logs). Evidence quality: good.

| Screen | Caption | Kind |
|---|---|---|
| C21-S1 | Invoice list with Total and Paid pill chips | marketing render |
| C21-S2 | Healthcode billing submission modal with insurer dropdowns | real UI |
| C21-S3 | Invoice detail with OUTSTANDING and VALIDATED status chips | real UI |
| C21-S4 | Invoice creation form with Billing to insurer dropdown | real UI |
| C21-S5 | Patient Logs tab showing raw SOAP submission XML | real UI |

Observations (evidence):

- Top nav is a single flat bar of ~11 modules; invoicing lives both in the global Invoices module and in a per-patient Invoices tab.
- Invoice list rows show invoice number, created date, author, and location, with paired pill chips: amber Total (e.g. Total £340) and colour-coded Paid (blue Paid £300, red Paid £0).
- Invoice detail header shows two status chips side by side: payment status (OUTSTANDING, red) and Healthcode status (VALIDATED, blue), next to Pay, share, edit, and print actions.
- Healthcode submission is a modal with five dropdowns (Service setting, Diagnosis type-to-search, Payee provider, Controlling specialist, Provider) and a Submit to Healthcode button; each field has plain-language helper text.
- Help docs state the Healthcode status appears only after the user refreshes the page; the status vocabulary is Unprocessed, Validated, Awaiting collection, Collected.
- No status exists beyond Collected: docs state that once the insurer pays, reconciliation in Semble must be done manually via the Pay dialog.
- Shortfall handling is manual: the user adjusts the insurer-paid amount, the remainder stays outstanding, and the invoice is re-shared with the patient with an explanatory note.
- Verification that a submission went through is done in the patient Logs tab, which renders the raw SOAP XML request and response.
- Healthcode failures surface as toast messages in the top-right corner; the help centre keeps a long catalogue of API error strings such as Problem with Diagnosis: Code not Mapped and Problem with ProviderNo: Invalid Code.
- Invoice creation form fields: Header, date (with inline note Invoices before 31/05/22 are locked), optional Practitioner, Billing section with patient and a Billing to dropdown for selecting the insurer, and an Add invoice item button for line items.

Scores: navigation 4 · hierarchy 3 · metric surfacing 2 · pipeline visibility 2 · dataviz n/a · task speed 1 · error prevention 2 · states n/a · mobile n/a

Worth copying:

- Paired amount chips on every invoice row (amber Total + colour-coded Paid) give per-invoice payment state at a glance; reuse this pattern in our invoice list.
- Dual status chips on the invoice header separating payment state from submission state; our timeline should keep that distinction while extending it past Collected to paid-out.
- Plain-language helper text under each insurer field (Payee provider, Controlling specialist) explains Healthcode jargon at the point of entry; do this in our pre-submission validation UI.
- Event-triggered billing automations (When booking is approved, invoice patient; automated and overdue payment reminders with Active/Pending states) reduce manual chasing.

Worth avoiding:

- Status that only updates on manual page refresh and dead-ends at Collected: the doctor never sees a payment date, so the core question when do I get paid has no answer in the product.
- Raw SOAP XML in a Logs tab as the only submission audit trail; replace with a human-readable event timeline (submitted, validated, collected, paid).
- Validation that happens only after submission, via insurer API error toasts backed by a help-centre catalogue of ~20 error strings; our pre-submission checks should catch these before the invoice leaves.
- Manual reconciliation and shortfall workflows with no aggregate rollup: outstanding insurer money is scattered across patient records, which is why cashflow must be our hero metric.

### C22 — Healthcode (ePractice)

The UK private-healthcare clearing service; ePractice is its billing/practice portal for specialists and medical secretaries submitting insurer invoices.

Navigation model: Horizontal top tabs (Status / Patients / Billing / Records & Reporting / Settings) with sub-tabs inside each module and a right-hand Quick Links button column. Evidence quality: partial.

| Screen | Caption | Kind |
|---|---|---|
| C22-S1 | Status landing page: task counts, ageing bar chart, quick links | real UI |
| C22-S2 | Post-submission validation errors: field, error, solution in red panels | real UI |
| C22-S3 | Payment Tracking: outstanding bills table, manual payment entry form | real UI |
| C22-S4 | Bill entry screen: episode, invoice, diagnosis codes, charge lines | real UI |
| C22-S5 | Secretary multi-specialist status page with per-provider failure counts | real UI |

Observations (evidence):

- Landing Status page shows four task counters (Failed Electronic Bills to Update, Membership Enquiry Responses to Review, Completed Paper Bills to Send, Draft Bills) plus an Awaiting column and a Service Announcements panel.
- Outstanding Payments is a bar chart of bill counts by age band (0-30, 31-60, 61-90, 91+ days) split Partially Paid vs With No Payments; counts of bills, not pound amounts.
- Invoice status in the current ePractice is three colour-coded boxes per invoice in the Account tab: 1 green = validated and ready, 2 green = waiting to be collected by insurer, 3 green = successfully submitted with collection date/time, 1 red = failed validation, 3 red = cancelled; tooltips on hover.
- Status tracking ends at insurer collection; there is no in-portal state for insurer processing, approval, shortfall, or payment date, and payments are entered manually in Payment Tracking (date, paid by, method, amount, comments).
- Validation errors are surfaced after Save & Send in red panels listing Field / Error / Solution (e.g. Field: Diagnosis Code, Error: Must be specified, Solution: Enter a diagnosis code), paged with << Error 1 of 2 >> controls.
- Bill entry is a dense multi-tab form (Episode & Invoice, Patient & Bill To, GP Details) with separate Charges sub-tab; NET TOTAL shown in a dark footer bar.
- Payment Tracking table columns: Patient Name, Invoice No, Invoice Date, Amount, Balance Due; footer totals for Invoice Net, Payment Total, Write Off / Credit Total, Balance Outstanding; filter by name, invoice number, payment type.
- Auto-population pulls patient demographics, insurance details, episode dates and diagnosis/procedure codes from validated hospital bills (VEDA), so the user only confirms charges and fee.
- Secretaries billing for multiple specialists get an aggregate table of Failed Electronic Bills / Unsubmitted Paper Bills / Draft Bills / Unread ME Responses per specialist.
- Legacy biller UI is desktop-only (documented for Internet Explorer with pop-up windows); no mobile layout is documented.

Scores: navigation 3 · hierarchy 2 · metric surfacing 2 · pipeline visibility 2 · dataviz 2 · task speed 2 · error prevention 3 · states 2 · mobile n/a

Worth copying:

- Error messages as Field / Error / Solution triplets: every validation failure names the field, the rule broken, and the fix - keep this pattern in our pre-submission validation.
- Ageing buckets (0-30/31-60/61-90/91+ days) as the default framing for outstanding money; doctors already think in these bands.
- Landing page as an action queue: counts of failed bills and drafts with direct links, so the first click is always the highest-value fix.
- Auto-population from upstream hospital/clearing data to cut re-keying - our Semble integration should prefill the same fields.

Worth avoiding:

- Status that dies at 'collected by insurer': the three-box tracker never says approved, shortfall, or paid, which is exactly the visibility gap we fill with an end-to-end timeline through remittance.
- Unlabeled colour-box status requiring hover tooltips to decode; use explicit chips with icon + label + date instead.
- Manual payment entry as the only reconciliation path - remittance should update invoice state automatically.
- Counting bills instead of pounds on the landing chart; cashflow value at risk is the number a doctor needs.
- Validation surfaced only after Save & Send; validate inline while the field is being completed.

## Appendix: screenshot index

All captures taken 2026-07-04. Files live in `design/references/<app>/`.

| ID | File | App folder | Kind | Source |
|---|---|---|---|---|
| C01-S1 | `epic/C01-S1.jpg` | epic | video frame | https://www.youtube.com/watch?v=iC1SjqAutUI |
| C01-S2 | `epic/C01-S2.jpg` | epic | video frame | https://www.youtube.com/watch?v=iC1SjqAutUI |
| C01-S3 | `epic/C01-S3.jpg` | epic | video frame | https://www.youtube.com/watch?v=AwMo3Je4S2Q |
| C01-S4 | `epic/C01-S4.jpg` | epic | video frame | https://www.youtube.com/watch?v=iC1SjqAutUI |
| C01-S5 | `epic/C01-S5.jpg` | epic | video frame | https://www.youtube.com/watch?v=iC1SjqAutUI |
| C02-S1 | `oracle-health-cerner/C02-S1.jpg` | oracle-health-cerner | video frame | https://m.youtube.com/watch?v=JRNlAlBkhPM |
| C02-S2 | `oracle-health-cerner/C02-S2.jpg` | oracle-health-cerner | video frame | https://www.youtube.com/watch?v=4J7pWfH-bn8 |
| C02-S3 | `oracle-health-cerner/C02-S3.jpg` | oracle-health-cerner | video frame | https://www.youtube.com/playlist?list=PLf4LusHX7ezfhFZIeGYffFJQsWTFTsEdj |
| C02-S4 | `oracle-health-cerner/C02-S4.jpg` | oracle-health-cerner | video frame | https://www.youtube.com/playlist?list=PLf4LusHX7ezfhFZIeGYffFJQsWTFTsEdj |
| C02-S5 | `oracle-health-cerner/C02-S5.webp` | oracle-health-cerner | marketing render | https://www.oracle.com/health/clinical-suite/electronic-health-record/ |
| C02-S6 | `oracle-health-cerner/C02-S6.webp` | oracle-health-cerner | marketing render | https://www.oracle.com/health/clinical-suite/electronic-health-record/ |
| C03-S1 | `meditech-expanse/C03-S1.jpg` | meditech-expanse | video frame | https://www.youtube.com/watch?v=mpa_uY9HqSw |
| C03-S2 | `meditech-expanse/C03-S2.jpg` | meditech-expanse | video frame | https://www.youtube.com/watch?v=p_zB8Ec3VBw |
| C03-S3 | `meditech-expanse/C03-S3.jpg` | meditech-expanse | video frame | https://www.youtube.com/watch?v=f4hyGOUZNdE |
| C03-S4 | `meditech-expanse/C03-S4.jpg` | meditech-expanse | video frame | https://www.youtube.com/watch?v=f4hyGOUZNdE |
| C03-S5 | `meditech-expanse/C03-S5.jpg` | meditech-expanse | video frame | https://www.youtube.com/watch?v=4q_2BxwmzDo |
| C03-S6 | `meditech-expanse/C03-S6.jpg` | meditech-expanse | video frame | https://www.youtube.com/watch?v=mpa_uY9HqSw |
| C04-S1 | `athenaone/C04-S1.jpg` | athenaone | video frame | https://www.youtube.com/watch?v=Jq3XKXk6Exg |
| C04-S2 | `athenaone/C04-S2.jpg` | athenaone | video frame | https://www.youtube.com/watch?v=gyf51Xhkn-4 |
| C04-S3 | `athenaone/C04-S3.jpg` | athenaone | video frame | https://www.youtube.com/watch?v=LVkK66UZEH8 |
| C04-S4 | `athenaone/C04-S4.jpg` | athenaone | video frame | https://www.youtube.com/watch?v=GljCWF4Yak0 |
| C04-S5 | `athenaone/C04-S5.jpg` | athenaone | video frame | https://www.youtube.com/watch?v=b6RlugVZD9o |
| C04-S6 | `athenaone/C04-S6.jpg` | athenaone | marketing render | https://www.youtube.com/watch?v=H_oqpkrd3Tw |
| C05-S1 | `eclinicalworks/C05-S1.jpg` | eclinicalworks | video frame | https://www.youtube.com/watch?v=aEjHW4D-K54 |
| C05-S2 | `eclinicalworks/C05-S2.jpg` | eclinicalworks | video frame | https://www.youtube.com/watch?v=IlsRxe2QUPU |
| C05-S3 | `eclinicalworks/C05-S3.jpg` | eclinicalworks | video frame | https://www.youtube.com/watch?v=gkmxmVCfdas |
| C05-S4 | `eclinicalworks/C05-S4.jpg` | eclinicalworks | video frame | https://www.youtube.com/watch?v=8LoSRd87HJg |
| C05-S5 | `eclinicalworks/C05-S5.png` | eclinicalworks | marketing render | https://www.eclinicalworks.com/new/ |
| C05-S6 | `eclinicalworks/C05-S6.png` | eclinicalworks | marketing render | https://www.eclinicalworks.com/new/ |
| C06-S1 | `nextgen-office/C06-S1.png` | nextgen-office | real UI | https://blog.metropm.com/nextgen-office-dashboard |
| C06-S2 | `nextgen-office/C06-S2.png` | nextgen-office | real UI | https://blog.metropm.com/nextgen-office-dashboard |
| C06-S3 | `nextgen-office/C06-S3.png` | nextgen-office | real UI | https://blog.metropm.com/nextgen-office-dashboard |
| C06-S4 | `nextgen-office/C06-S4.png` | nextgen-office | real UI | https://blog.metropm.com/nextgen-office-dashboard |
| C06-S5 | `nextgen-office/C06-S5.webp` | nextgen-office | marketing render | https://www.nextgen.com/solutions/electronic-health-records/small-practices-nextgen-office |
| C06-S6 | `nextgen-office/C06-S6.webp` | nextgen-office | marketing render | https://www.nextgen.com/solutions/electronic-health-records/small-practices-nextgen-office |
| C07-S1 | `advancedmd/C07-S1.jpg` | advancedmd | real UI | https://www.advancedmd.com/emr-ehr-software/donut-dashboard/ |
| C07-S2 | `advancedmd/C07-S2.jpg` | advancedmd | real UI | https://www.advancedmd.com/emr-ehr-software/donut-dashboard/ |
| C07-S3 | `advancedmd/C07-S3.jpg` | advancedmd | real UI | https://www.advancedmd.com/emr-ehr-software/donut-dashboard/ |
| C07-S4 | `advancedmd/C07-S4.jpg` | advancedmd | real UI | https://www.advancedmd.com/emr-ehr-software/donut-dashboard/ |
| C07-S5 | `advancedmd/C07-S5.jpg` | advancedmd | marketing render | https://www.advancedmd.com/company/new-products-features/dashboard/ |
| C08-S1 | `drchrono/C08-S1.jpg` | drchrono | video frame | https://www.youtube.com/watch?v=vZH8naIom1Y |
| C08-S2 | `drchrono/C08-S2.jpg` | drchrono | video frame | https://www.youtube.com/watch?v=lqKQJHrlJ8M |
| C08-S3 | `drchrono/C08-S3.jpg` | drchrono | video frame | https://www.youtube.com/watch?v=lqKQJHrlJ8M |
| C08-S4 | `drchrono/C08-S4.jpg` | drchrono | video frame | https://www.youtube.com/watch?v=lqKQJHrlJ8M |
| C08-S5 | `drchrono/C08-S5.jpg` | drchrono | video frame | https://www.youtube.com/watch?v=K5Xyay1PATs |
| C08-S6 | `drchrono/C08-S6.jpg` | drchrono | video frame | https://www.youtube.com/watch?v=vZH8naIom1Y |
| C09-S1 | `tebra/C09-S1.png` | tebra | real UI | https://helpme.tebra.com/Billing/Billing_Reports/Navigate_AR_Dashboard |
| C09-S2 | `tebra/C09-S2.png` | tebra | real UI | https://helpme.tebra.com/Tebra_PM/03_Dashboard_Overview/01_Navigate_Dashboard |
| C09-S3 | `tebra/C09-S3.png` | tebra | real UI | https://helpme.tebra.com/Billing/Billing_Reports/Navigate_AR_Dashboard |
| C09-S4 | `tebra/C09-S4.png` | tebra | marketing render | https://www.tebra.com/billing |
| C09-S5 | `tebra/C09-S5.png` | tebra | video frame | https://www.kareo.com/kareo-ehr-dashboard |
| C09-S6 | `tebra/C09-S6.png` | tebra | real UI | https://helpme.tebra.com/Billing/Billing_Reports/Billing_Analytics |
| C10-S1 | `elation-health/C10-S1.png` | elation-health | real UI | https://www.elationhealth.com/contact-us/product-tour/ (Navattic tour capture) |
| C10-S2 | `elation-health/C10-S2.png` | elation-health | real UI | https://www.elationhealth.com/contact-us/product-tour/ (Navattic tour capture) |
| C10-S3 | `elation-health/C10-S3.jpg` | elation-health | real UI | https://www.elationhealth.com/contact-us/product-tour/ (Navattic tour capture) |
| C10-S4 | `elation-health/C10-S4.jpg` | elation-health | real UI | https://www.elationhealth.com/contact-us/product-tour/ (Navattic tour capture) |
| C10-S5 | `elation-health/C10-S5.png` | elation-health | marketing render | https://www.elationhealth.com/solutions/ehr/ |
| C10-S6 | `elation-health/C10-S6.png` | elation-health | marketing render | https://www.elationhealth.com/solutions/ehr/ |
| C11-S1 | `practice-fusion/C11-S1.png` | practice-fusion | real UI | https://softwarefinder.com/emr-software/practice-fusion |
| C11-S2 | `practice-fusion/C11-S2.jpg` | practice-fusion | real UI | https://softwarefinder.com/emr-software/practice-fusion |
| C11-S3 | `practice-fusion/C11-S3.jpg` | practice-fusion | real UI | https://softwarefinder.com/emr-software/practice-fusion |
| C11-S4 | `practice-fusion/C11-S4.jpg` | practice-fusion | video frame | https://img.youtube.com/vi/DhUjk5jRj9k/maxresdefault.jpg |
| C11-S5 | `practice-fusion/C11-S5.jpg` | practice-fusion | video frame | https://img.youtube.com/vi/k-3NJKL05ok/maxresdefault.jpg |
| C12-S1 | `carecloud/C12-S1.png` | carecloud | video frame | https://carecloud.com/product-tour/billing_video.html |
| C12-S2 | `carecloud/C12-S2.png` | carecloud | video frame | https://carecloud.com/product-tour/billing_video.html |
| C12-S3 | `carecloud/C12-S3.png` | carecloud | video frame | https://carecloud.com/product-tour/billing_video.html |
| C12-S4 | `carecloud/C12-S4.png` | carecloud | video frame | https://carecloud.com/product-tour/charts_video.html |
| C12-S5 | `carecloud/C12-S5.png` | carecloud | video frame | https://carecloud.com/product-tour/charts_video.html |
| C13-S1 | `simplepractice/C13-S1.jpg` | simplepractice | real UI | https://www.saasui.design/application/simplepractice |
| C13-S2 | `simplepractice/C13-S2.jpg` | simplepractice | real UI | https://www.saasui.design/application/simplepractice |
| C13-S3 | `simplepractice/C13-S3.jpg` | simplepractice | real UI | https://www.saasui.design/application/simplepractice |
| C13-S4 | `simplepractice/C13-S4.jpg` | simplepractice | real UI | https://www.saasui.design/application/simplepractice |
| C13-S5 | `simplepractice/C13-S5.jpg` | simplepractice | real UI | https://www.saasui.design/application/simplepractice |
| C14-S1 | `jane-app/C14-S1.png` | jane-app | marketing render | https://jane.app/features/scheduling |
| C14-S2 | `jane-app/C14-S2.png` | jane-app | marketing render | https://jane.app/features/billing-and-insurance |
| C14-S3 | `jane-app/C14-S3.png` | jane-app | marketing render | https://jane.app/features/billing-and-insurance |
| C14-S4 | `jane-app/C14-S4.png` | jane-app | marketing render | https://jane.app/features/invoicing-and-sales |
| C14-S5 | `jane-app/C14-S5.png` | jane-app | marketing render | https://jane.app/features/reporting-and-analytics |
| C14-S6 | `jane-app/C14-S6.png` | jane-app | marketing render | https://jane.app/features/billing-and-insurance |
| C15-S1 | `healthie/C15-S1.png` | healthie | real UI | https://help.gethealthie.com/article/535-your-provider-dashboard |
| C15-S2 | `healthie/C15-S2.png` | healthie | real UI | https://help.gethealthie.com/article/535-your-provider-dashboard |
| C15-S3 | `healthie/C15-S3.png` | healthie | real UI | https://help.gethealthie.com/article/535-your-provider-dashboard |
| C15-S4 | `healthie/C15-S4.webp` | healthie | real UI | https://www.gethealthie.com/plus/platform-ehr |
| C15-S5 | `healthie/C15-S5.webp` | healthie | marketing render | https://www.gethealthie.com/plus/platform-ehr |
| C16-S1 | `xero-analytics-plus/C16-S1.png` | xero-analytics-plus | real UI | https://www.xero.com/us/accounting-software/analytics/snapshot/ |
| C16-S2 | `xero-analytics-plus/C16-S2.jpg` | xero-analytics-plus | video frame | https://www.youtube.com/watch?v=Yg1W-OgrBsw |
| C16-S3 | `xero-analytics-plus/C16-S3.png` | xero-analytics-plus | real UI | https://blog.accountingprose.com/getting-started-with-xeros-new-analytics-powered-by-syft-analytics |
| C16-S4 | `xero-analytics-plus/C16-S4.png` | xero-analytics-plus | real UI | https://blog.accountingprose.com/getting-started-with-xeros-new-analytics-powered-by-syft-analytics |
| C16-S5 | `xero-analytics-plus/C16-S5.png` | xero-analytics-plus | marketing render | https://www.xero.com/us/accounting-software/analytics/ |
| C16-S6 | `xero-analytics-plus/C16-S6.jpg` | xero-analytics-plus | marketing render | https://www.xero.com/us/accounting-software/analytics/ |
| C17-S1 | `quickbooks-online/C17-S1.png` | quickbooks-online | real UI | https://www.intuit.com/oidam/intuit/ic/en_ca/content/Intuit-education-program-ca-qbo-ch2-getting-around-quickbooks-online.pdf |
| C17-S2 | `quickbooks-online/C17-S2.png` | quickbooks-online | real UI | https://www.intuit.com/oidam/intuit/ic/en_ca/content/Intuit-education-program-ca-qbo-ch2-getting-around-quickbooks-online.pdf |
| C17-S3 | `quickbooks-online/C17-S3.png` | quickbooks-online | real UI | https://www.intuit.com/oidam/intuit/ic/en_ca/content/Intuit-education-program-ca-qbo-ch2-getting-around-quickbooks-online.pdf |
| C17-S4 | `quickbooks-online/C17-S4.png` | quickbooks-online | real UI | https://www.intuit.com/oidam/intuit/ic/en_ca/content/Intuit-education-program-ca-qbo-ch2-getting-around-quickbooks-online.pdf |
| C17-S5 | `quickbooks-online/C17-S5.png` | quickbooks-online | real UI | https://www.intuit.com/oidam/intuit/ic/en_ca/content/Intuit-education-program-ca-qbo-ch2-getting-around-quickbooks-online.pdf |
| C17-S6 | `quickbooks-online/C17-S6.png` | quickbooks-online | real UI | https://www.intuit.com/oidam/intuit/ic/en_ca/content/Intuit-education-program-ca-qbo-ch2-getting-around-quickbooks-online.pdf |
| C18-S1 | `fathom/C18-S1.jpg` | fathom | real UI | https://www.fathomhq.com/features/insights-dashboard |
| C18-S2 | `fathom/C18-S2.jpg` | fathom | real UI | https://www.fathomhq.com/features/insights-dashboard |
| C18-S3 | `fathom/C18-S3.jpg` | fathom | real UI | https://www.fathomhq.com/features/insights-dashboard |
| C18-S4 | `fathom/C18-S4.jpg` | fathom | real UI | https://www.fathomhq.com/features/insights-dashboard |
| C18-S5 | `fathom/C18-S5.png` | fathom | real UI | https://www.fathomhq.com/features/insights-dashboard |
| C18-S6 | `fathom/C18-S6.png` | fathom | marketing render | https://www.fathomhq.com/reports |
| C19-S1 | `syft-analytics/C19-S1.png` | syft-analytics | real UI | https://help.syftanalytics.com/en/articles/9041125-create-a-dashboard |
| C19-S2 | `syft-analytics/C19-S2.png` | syft-analytics | real UI | https://help.syftanalytics.com/en/articles/9041125-create-a-dashboard |
| C19-S3 | `syft-analytics/C19-S3.png` | syft-analytics | real UI | https://help.syftanalytics.com/en/articles/9041125-create-a-dashboard |
| C19-S4 | `syft-analytics/C19-S4.png` | syft-analytics | real UI | https://help.syftanalytics.com/en/articles/9041125-create-a-dashboard |
| C19-S5 | `syft-analytics/C19-S5.png` | syft-analytics | real UI | https://help.syftanalytics.com/en/articles/9070894-visualize |
| C19-S6 | `syft-analytics/C19-S6.png` | syft-analytics | real UI | https://help.syftanalytics.com/en/articles/9070894-visualize |
| C20-S1 | `stripe-dashboard/C20-S1.jpg` | stripe-dashboard | video frame | https://pageflows.com/web/products/stripe/ |
| C20-S2 | `stripe-dashboard/C20-S2.png` | stripe-dashboard | real UI | https://support.stripe.com/questions/dashboard-home-page-charts-for-business-insights |
| C20-S3 | `stripe-dashboard/C20-S3.jpg` | stripe-dashboard | video frame | https://pageflows.com/web/products/stripe/ |
| C20-S4 | `stripe-dashboard/C20-S4.jpg` | stripe-dashboard | video frame | https://pageflows.com/web/products/stripe/ |
| C20-S5 | `stripe-dashboard/C20-S5.png` | stripe-dashboard | real UI | https://support.stripe.com/questions/dashboard-home-page-charts-for-business-insights |
| C20-S6 | `stripe-dashboard/C20-S6.jpg` | stripe-dashboard | video frame | https://pageflows.com/screens/2e9c0c08-14de-4946-bfa9-b1fe8a8cacf7/ |
| C21-S1 | `semble/C21-S1.png` | semble | marketing render | https://www.semble.io/platform/patient-billing |
| C21-S2 | `semble/C21-S2.png` | semble | real UI | https://help.semble.io/submit-a-healthcode-invoice-semble-help-centre |
| C21-S3 | `semble/C21-S3.png` | semble | real UI | https://help.semble.io/submit-a-healthcode-invoice-semble-help-centre |
| C21-S4 | `semble/C21-S4.png` | semble | real UI | https://help.semble.io/submit-a-healthcode-invoice-semble-help-centre |
| C21-S5 | `semble/C21-S5.png` | semble | real UI | https://help.semble.io/submit-a-healthcode-invoice-semble-help-centre |
| C22-S1 | `healthcode/C22-S1.png` | healthcode | real UI | https://www.veda.healthcode.co.uk/_help/docs/ePracticeBiller_UserGuide.pdf |
| C22-S2 | `healthcode/C22-S2.png` | healthcode | real UI | https://www.veda.healthcode.co.uk/_help/docs/ePracticeBiller_UserGuide.pdf |
| C22-S3 | `healthcode/C22-S3.png` | healthcode | real UI | https://www.veda.healthcode.co.uk/_help/docs/ePracticeBiller_UserGuide.pdf |
| C22-S4 | `healthcode/C22-S4.png` | healthcode | real UI | https://www.veda.healthcode.co.uk/_help/docs/ePracticeBiller_UserGuide.pdf |
| C22-S5 | `healthcode/C22-S5.png` | healthcode | real UI | https://www.veda.healthcode.co.uk/_help/docs/ePracticeBiller_UserGuide.pdf |
