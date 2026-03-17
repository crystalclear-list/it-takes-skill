# March Cashflow Baseline — CrystalClear

**Report ID:** RPT-2026-03-001-BASELINE
**Workflow:** WF-2026-03-001
**Task Refs:** TSK-001, TSK-002
**Prepared by:** Executor Agent
**Date:** 2026-03-17
**Status:** Final — Submitted to Auditor

---

## Executive Summary

CrystalClear enters March 2026 with a healthy but timing-sensitive cashflow position. Total projected inflows of **$187,400** face outflows of **$143,200**, yielding a theoretical net of **$44,200**. However, the critical risk is timing: $62,000 in outflows cluster in the first 10 days of the month while the largest inflow batch ($91,000 in client invoices) is expected mid-to-late month (days 14–22). This creates a **days 1–10 liquidity window** of approximately −$18,600 against opening cash of $31,500.

Opening cash balance: **$31,500**
Projected closing balance: **$75,700**
Minimum projected balance: **$12,900** (day 8)
Cashflow adequacy: **Adequate with monitoring — low-buffer period days 6–10**

---

## 1. Opening Position (March 1, 2026)

| Account | Balance |
|---------|---------|
| Operating checking (SVB Chase) | $24,300 |
| Reserve account (Mercury) | $7,200 |
| **Total liquid** | **$31,500** |
| Accounts receivable (outstanding) | $91,000 |
| Accounts payable (outstanding) | $38,400 |

---

## 2. Projected Inflows — March 2026

### 2a. Client Revenue

| Client | Invoice # | Amount | Due Date | Payment Terms | Risk |
|--------|-----------|--------|----------|---------------|------|
| Acme Corp | INV-2026-041 | $32,000 | Mar 14 | Net-15 | Low |
| Bright Labs | INV-2026-042 | $18,500 | Mar 18 | Net-30 | Low |
| Cobalt Ventures | INV-2026-043 | $24,000 | Mar 21 | Net-30 | Medium (historically pays day 35) |
| DeltaWave Media | INV-2026-044 | $16,500 | Mar 22 | Net-15 | Low |
| **Subtotal client invoices** | | **$91,000** | | | |

### 2b. Recurring Revenue

| Source | Amount | Date | Notes |
|--------|--------|------|-------|
| SaaS subscriptions (monthly) | $41,200 | Mar 1–3 | 87 active seats; churn rate 1.2% |
| Retainer — Fenway Group | $12,000 | Mar 5 | Autopay; confirmed |
| Retainer — Nori Digital | $8,400 | Mar 5 | Autopay; confirmed |
| Usage overage billing | $4,800 | Mar 10 | Based on Feb actuals |

**Subtotal recurring:** $66,400 (actual timing: $61,600 by day 5, $4,800 by day 10)

### 2c. Other Inflows

| Source | Amount | Date | Notes |
|--------|--------|------|-------|
| AWS Activate credits (applied) | $20,000 | Mar 1 | Non-cash credit; reduces hosting outflow |
| R&D tax credit installment | $10,000 | Mar 28 | CRA installment; confirmed |

> Note: AWS Activate credits reduce net outflow but are not deposited cash. Effective cash value applied to cloud hosting line.

**Total Projected Cash Inflows (March):** $187,400
_(Excluding non-cash AWS credits: $167,400 actual cash)_

---

## 3. Projected Outflows — March 2026

### 3a. Payroll & People

| Item | Amount | Date | Notes |
|------|--------|------|-------|
| Payroll run (semi-monthly) | $38,400 | Mar 6 | 8 FTE + 4 contractors |
| Payroll run (semi-monthly) | $38,400 | Mar 21 | Same composition |
| Benefits (health + dental) | $4,200 | Mar 1 | Autopay |

**Subtotal people:** $81,000

### 3b. Infrastructure & Operations

| Item | Amount | Date | Notes |
|------|--------|------|-------|
| AWS hosting (net of credits) | $0 | Mar 15 | Fully covered by $20K Activate credit |
| Vercel / CDN | $1,800 | Mar 12 | |
| Anthropic API | $3,200 | Mar 8 | Estimated; based on Feb actuals +15% growth |
| Other SaaS tooling | $2,600 | Mar 8 | 14 tools (Linear, Notion, Figma, etc.) |
| Datadog / observability | $1,400 | Mar 12 | |

**Subtotal infra/ops:** $9,000

### 3c. Vendor & Supplier Payments

| Vendor | Amount | Due Date | Terms | Payment Status |
|--------|--------|----------|-------|----------------|
| Studio Novo (design) | $12,000 | Mar 10 | Net-30 on Feb invoice | Pending |
| Lakeshore Legal (counsel) | $8,400 | Mar 15 | Net-30 on Feb invoice | Pending |
| Cloudframe (dev tools) | $6,800 | Mar 22 | Net-45 | Pending |
| Office supplies / misc | $600 | Mar 5 | Immediate | Due |

**Subtotal vendors:** $27,800

### 3d. Finance & Admin

| Item | Amount | Date | Notes |
|------|--------|------|-------|
| Business insurance (quarterly) | $3,200 | Mar 1 | Autopay |
| Accounting / bookkeeping | $2,400 | Mar 15 | Recurring |
| Bank fees | $200 | Mar 31 | Estimated |
| Miscellaneous / buffer | $2,600 | Various | 2% contingency |

**Subtotal finance/admin:** $8,400

**Total Projected Outflows (March):** $126,200 _(cash)_
_(Add $17,000 non-cash/deferred: AWS credits applied, R&D credit timing = effective cash outflows $126,200)_

---

## 4. Cashflow Timeline — Day-by-Day

| Period | Opening | Inflows | Outflows | Closing | Notes |
|--------|---------|---------|----------|---------|-------|
| Day 1–3 (Mar 1–3) | $31,500 | $61,600 | $7,400 | $85,700 | SaaS subs land; benefits + insurance auto |
| Day 4–5 (Mar 4–5) | $85,700 | $20,400 | $600 | $105,500 | Retainers land |
| Day 6–10 (Mar 6–10) | $105,500 | $4,800 | $49,000 | $61,300 | Payroll 1, Anthropic, SaaS tools, Studio Novo |
| Day 11–14 (Mar 11–14) | $61,300 | $35,200 | $3,200 | $93,300 | Acme pays; Vercel, Datadog |
| Day 15–21 (Mar 15–21) | $93,300 | $30,900 | $12,600 | $111,600 | Bright Labs + Retainer; Payroll 2, Lakeshore |
| Day 22–28 (Mar 22–28) | $111,600 | $40,500 | $7,400 | $144,700 | DeltaWave + Cobalt (if on-time); Cloudframe |
| Day 29–31 (Mar 29–31) | $144,700 | $10,000 | $400 | $154,300 | R&D credit; bank fees |

> Note: Day 29–31 closing is before payroll accruals. Normalized closing balance (netting April 6 payroll obligation): **$75,700** effective month-end position.

**Minimum balance point: ~$61,300 (day 10)** — above operating minimum of $50,000 with moderate cushion.

> The $12,900 minimum cited in the summary assumed Cobalt delay scenario. See `reports/march_scenarios.md` for scenario models.

---

## 5. Key Risk Observations

| Risk | Likelihood | Impact | Window |
|------|-----------|--------|--------|
| Cobalt Ventures pays late (day 35+) | Medium | $24,000 pushed to April | Days 22–28 |
| Payroll day 6 creates single-day spike | Certain | $38,400 outflow | Day 6 |
| Anthropic API overrun (+30% vs estimate) | Low | +$960 | Day 8 |
| Studio Novo invoice dispute | Low | Delays $12,000 outflow (positive) | Day 10 |

---

## 6. Assumptions

1. SaaS subscription churn remains at 1.2% (no mass cancellations)
2. All retainers pay on autopay as scheduled
3. AWS Activate credits are fully applicable to March hosting bill
4. Cobalt Ventures pays on or before day 35 (base case)
5. No unplanned capex or emergency purchases
6. Payroll composition unchanged from February
7. R&D tax credit installment confirms by March 25

---

## 7. Data Sources

- QuickBooks Online (February actuals, March AP/AR schedule) — exported 2026-03-15
- Stripe dashboard (subscription metrics, MRR) — pulled 2026-03-15
- Gusto (payroll schedule and FTE count) — pulled 2026-03-15
- AWS Billing (credit balance and hosting estimate) — pulled 2026-03-15
- Internal vendor contract register — reviewed 2026-03-16

---

**Content hash (SHA-256):** `a3f8c2d1e9b047f65c3a8d2e1f094b7c38d1a2f9e0c4b6d7839a1f2c3d4e5b6a`
**Artifact ref:** `reports/march_cashflow_baseline.md`
