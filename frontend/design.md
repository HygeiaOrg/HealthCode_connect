---
# design.md tokens (google-labs-code/design.md format)
# Read this file before generating or editing any UI code in frontend/.
colors:
  light:
    surface: "#fcfcfb"
    page: "#f9f9f7"
    ink-primary: "#0b0b0b"
    ink-secondary: "#52514e"
    ink-muted: "#898781"
    gridline: "#e1e0d9"
    baseline: "#c3c2b7"
    border: "rgba(11,11,11,0.10)"
    brand: "#2a78d6"
    series-nhs: "#2a78d6"
    series-private: "#1baf7a"
    series-3: "#eda100"
    series-4: "#4a3aa7"
    stage-draft: "#86b6ef"
    stage-medserv: "#2a78d6"
    stage-insurer: "#1c5cab"
    status-query: "#ec835a"
    status-paid: "#0ca30c"
    status-overdue: "#fab219"
    status-stuck: "#ec835a"
    status-rejected: "#d03b3b"
    delta-good-text: "#006300"
  dark:
    surface: "#1a1a19"
    page: "#0d0d0d"
    ink-primary: "#ffffff"
    ink-secondary: "#c3c2b7"
    ink-muted: "#898781"
    gridline: "#2c2c2a"
    baseline: "#383835"
    border: "rgba(255,255,255,0.10)"
    brand: "#3987e5"
    series-nhs: "#3987e5"
    series-private: "#199e70"
    series-3: "#c98500"
    series-4: "#9085e9"
    stage-draft: "#86b6ef"
    stage-medserv: "#3987e5"
    stage-insurer: "#1c5cab"
    status-query: "#ec835a"
    status-paid: "#0ca30c"
    status-overdue: "#fab219"
    status-stuck: "#ec835a"
    status-rejected: "#d03b3b"
    delta-good-text: "#0ca30c"
typography:
  family: 'system-ui, -apple-system, "Segoe UI", sans-serif'
  hero: { size: 40, weight: 650, tracking: "-0.01em" }
  h1: { size: 24, weight: 650 }
  h2: { size: 18, weight: 600 }
  body: { size: 14, weight: 400, line-height: 1.5 }
  small: { size: 12.5, weight: 400 }
  chip: { size: 12, weight: 600 }
  money-columns: "font-variant-numeric: tabular-nums"
spacing:
  base: 4
  card-padding: 20
  section-gap: 24
  page-max-width: 1240
radius:
  card: 10
  control: 8
  chip: 999
  chart-data-end: 4
elevation:
  card: "0 1px 2px rgba(11,11,11,0.05), inset 0 0 0 1px var(--border)"
  modal: "0 8px 30px rgba(11,11,11,0.18)"
---

# HealthCode Connect design system

## Overview

HealthCode Connect answers one question on sight: when do I get paid? The interface is a cashflow console for a doctor who checks finances weekly, between patients, and it is judged by how fast it converts a glance into that answer. Every choice below traces to evidence in `../design/DESIGN.md`; citations like (C17) point to the teardown cards there.

Personality: calm, precise, bank-grade. The product earns trust by showing dated facts, never by decoration. Density sits between Stripe (C20) and SimplePractice (C13): fewer, larger numbers than an EHR, more information per screen than a marketing dashboard.

## Colors

The palette is the validated data-viz reference set; both modes passed the six-check validator on 2026-07-04 (worst adjacent CVD ΔE 47.2 light, 41.3 dark).

Roles, not raw hex, everywhere. The two income streams have fixed identities: NHS is always `series-nhs` (blue), private clinic is always `series-private` (aqua). A filter that hides one series never repaints the other.

Pipeline stages are an ordinal blue ramp that darkens as money moves toward the doctor: `stage-draft` → `stage-medserv` → `stage-insurer`. Terminal states leave the ramp: `status-paid` (green), `status-rejected` (red). The insurer-query state wears `status-query` (orange): actively blocked, not merely slow. Exceptions ride on top: `status-overdue` (amber) and `status-stuck` (orange) flag age, not position. Status colors never appear as chart series and never appear without an icon and a label (C01, C22).

Relief rule from the validator: `series-private` and `series-3` sit below 3:1 on the light surface, so any chart using them ships visible direct labels or a table toggle. We ship direct labels by default.

## Typography

One family, the system sans, at every size including the hero figure. Money columns and axis ticks use tabular figures so amounts align; everything else uses proportional figures. Text always wears ink tokens; a colored dot or chip beside the text carries series identity, the text itself never does.

## Layout & Spacing

- One chrome layer: a fixed 216px left sidebar (OpenClaw Control-UI structure): brand strip, grouped nav with uppercase section labels (Work: Overview, Invoices, Fix queue; Insight: Compare; System: Settings), a live stuck-count badge on Fix queue, and connection status in the footer. Still five destinations; every product with a 12-plus-item rail scored poorly on findability (C02, C05, C17).
- Content column capped at 1240px, 24px gaps between sections, cards on the `page` plane with `surface` fill.
- The Overview grid: hero cashflow card full-width, then a three-card KPI row, then the pipeline bar, then the action queue. The hero is never below the fold.
- Responsive: below 900px the sidebar collapses to a horizontal strip and content goes single column. No separate mobile app for the MVP.

## Elevation & Depth

Flat by default. Cards get a hairline ring plus a 1px shadow; only modals and the invoice timeline flyout cast real shadow. Depth signals interactivity, never importance: importance is expressed by size and position (hero first).

## Shapes

Cards at 10px radius, controls at 8px, chips fully rounded. Chart marks are thin with 4px rounded data-ends anchored to the baseline, 2px line weight, 2px surface gaps between stacked segments. No decorative illustration except in empty states.

## Components

- Hero cashflow card. Headline figure is expected cash with a date, in the Stripe pattern: "£4,320 expected by 18 Jul" (C20). Below it a cashflow line chart with a previous-period ghost line and a delta chip (C19, C20). One chart, no configuration (C19, C20 avoid-notes).
- KPI card. Number, delta arrow with plain-language comparison, one-sentence explainer, in the Tebra/Xero grammar (C09, C16). MVP set: outstanding total, median days to payment per payer ("Payment velocity", C09), fees paid to middlemen this year.
- Pipeline money bar. One segmented horizontal bar, each lifecycle stage labeled with £ amount and count, in the QuickBooks two-stage money bar pattern (C17). Clicking a segment filters the invoice table (donut-as-filter behavior, C07, in bar form). Repeated identically on Overview and Invoices so the mental model carries (C17).
- Status chip. Color plus icon plus label, always all three (C20). Stage chips add days-in-stage when older than 7 days: "With insurer · 12d", following "Overdue 47 days" (C17). Never a bare dot (C01, C06, C22).
- Invoice row. Number, patient ref, payer chip (NHS or insurer name), amount, stage chip, expected date, inline action (Fix, Chase, or View). The row expands in place to the dated timeline (C01): Draft → At Medserv → With insurer → Paid, each stage with a timestamp, the current stage pulsing; rejection and insurer-query nodes branch where they happened. Nothing dead-ends at "collected" (C21, C22).
- Validation panel. Pre-submission checks as named rows with pass/fail chips and one-line explanations (C10). Failures use the Field / Error / Solution triplet (C22). A live counter gates submission: the Submit button stays disabled until "0 issues remaining" (C02).
- Fix queue. The orchestration centre: every stuck invoice matches exactly one deterministic rule (rejected, insurer query, shortfall, past insurer SLA, stalled at Medserv, never submitted; checked in that order) and each rule prescribes one action. Groups carry a severity accent and £ total; rows sort by money at stake; the rulebook and per-insurer SLA table are printed on Settings. Grouping errors by fix type is the CareCloud inbox pattern (C12); the gate-until-zero idea is Cerner's (C02).
- Action queue. "Needs attention" list with counts per reason (Rejected 2, Missing data 1, Stale 14d+ 3), each row carrying its inline fix action (C10, C15, C22).
- Compare view. Private versus NHS as paired series in the two fixed hues: dual-series bars for monthly income (C19), side-by-side aging buckets (C14), rejection rate and payment velocity per payer (C09). Comparison date ranges spelled out in plain text under the title (C19).
- Empty states. Every panel teaches: a SAMPLE-badged preview of the populated state plus one call to action (C16, C17). Positive empty state for a clean queue: "No invoices need attention" (C15). Never a silent blank (C02, C05).
- Tables. Hover tooltip per mark, aging buckets as first-class columns (C14), pounds and percent shown together (C09). Every chart has a table-view toggle.

## Do's & Don'ts

Do:

- Answer "when do I get paid?" on landing with an amount and a date, zero clicks.
- Show £ values everywhere a count appears; counts alone are banned (C07, C22).
- Validate at data entry and before submission, never only after (C05, C21, C22).
- Keep data live or visibly fresh; if data is cached, show "updated 2 min ago".
- Use sentence-style microcopy with actions attached: "You have 2 rejected invoices to fix" (C09).

Don't:

- Don't add nav items beyond the four destinations; fold rarities into Settings.
- Don't use color without icon and label, anywhere (C01, C05, C22).
- Don't ship chart configuration, metric pickers, or dashboard builders (C19, C20).
- Don't show raw ids, XML, or API error strings to the doctor (C20, C21); translate to Field / Error / Solution.
- Don't render pie charts for status mixes; use the pipeline money bar or a status-count row (C15).
- Don't put a second y-axis on any chart; two measures means two charts.
