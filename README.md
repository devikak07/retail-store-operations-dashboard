# Retail Store Operations Dashboard

A Power BI report analysing two years of trading across a five-store retail estate —
sales performance, labour efficiency, and the relationship between the two.

Built on synthetic data. No real company or personal data is used.

---

## Findings

### 1. Labour cost is fixed; sales are not

Labour cost is almost identical across all five stores — £255k to £263k over two
years, a spread of 3%. Sales over the same period range from £887k to £2.17m, a
spread of 2.4×.

| Store | Total Sales | Labour Cost | Labour % of Sales | Sales per Labour Hour |
|---|---|---|---|---|
| Croydon | £2,170,067 | £258,399 | 12% | £108.00 |
| Reading | £1,874,846 | £254,514 | 14% | £94.53 |
| Friern Barnet | £1,511,288 | £260,649 | 17% | £75.11 |
| Watford | £1,130,541 | £263,498 | 23% | £55.53 |
| Ilford | £887,392 | £255,143 | 29% | £45.64 |
| **Estate** | **£7,574,134** | **£1,292,203** | **17%** | **£75.86** |

This is consistent with **minimum staffing floors** rather than overstaffing. A store
cannot trade with fewer than two people on the floor regardless of how quiet it is,
so smaller stores carry a fixed labour burden that larger stores spread across far
more sales.

The implication is that labour efficiency is not primarily a management-performance
question at the small stores. Closing Ilford's gap to the 17% estate average would
represent around £104k over the period, but that figure is a ceiling rather than a
target — the floor is real. The more useful question is whether Ilford's trading
hours match its footfall, not whether it is overstaffed during them.

### 2. Overrun is small, but systematic

Actual hours worked exceed scheduled hours on **every day of the week, without
exception**. Total overrun is 4,119 hours — roughly 4.3% of scheduled hours —
costing £53,310 across the two years, or about £5,300 per store per year.

A 4% overrun is not unusual in retail and is not by itself evidence of poor
discipline. Shifts run long because customers are still in the shop at close,
because deliveries land late, or because a colleague stays to finish a task.

The finding is not that overrun exists. It is that overrun is **consistent and
predictable**, appearing on every weekday across all five stores over two years.
A predictable cost belongs in the plan: any rota or budget built on scheduled hours
will understate true labour cost by approximately 4% every period.

### 3. Seasonality is stable and steep

Sales peak in December and fall sharply in January in both years, with the two
December peaks almost identical. The pattern is stable enough to plan against.

---

## The data model

Star schema — three fact tables joined to four dimensions, all many-to-one with a
single filter direction.

**Facts**
- `fact_sales` — 819,000 rows, one per sales line, with transaction ID, quantity, net sales, cost, discount
- `fact_labour` — one row per employee shift, scheduled and actual hours, labour cost
- `fact_footfall` — daily footfall and transaction counts by store

**Dimensions**
- `dim_date` — marked as the report's date table, enabling time intelligence
- `dim_store` — five stores, region, floor area, format
- `dim_product` — 158 SKUs across six categories
- `dim_employee` — 80 employees, role, hourly rate

Power BI's auto-detected relationships were removed and rebuilt. In particular, an
auto-created `dim_employee → dim_store` link created an ambiguous filter path between
labour and store, which deactivated the `fact_labour → dim_employee` relationship.
Removing the dimension-to-dimension join restored a clean star.

## Measures

Around eighteen DAX measures, layered so that lower-level measures compose into
higher-level ones. Examples:

```dax
Total Sales = SUM(fact_sales[NetSales])
Gross Margin % = DIVIDE([Gross Profit], [Total Sales])
Conversion Rate = DIVIDE([Transactions], [Total Footfall])
Sales per Labour Hour = DIVIDE([Total Sales], [Actual Hours])
Overrun Cost = DIVIDE([Labour Cost], [Actual Hours]) * [Hours Overrun]
```

`DIVIDE` is used throughout rather than `/` so that a zero denominator returns blank
rather than breaking the visual.

## Verification

Every headline figure was calculated independently from the source files in pandas
before being trusted in the report:

| Metric | Source files | Power BI |
|---|---|---|
| Total sales | £7,574,134 | £7,574,134 |
| Gross margin | 41.0% | 41.0% |
| Transactions | 406,772 | 406,772 |
| Average transaction value | £18.62 | £18.62 |

## Report pages

1. **Executive overview** — headline KPIs, monthly sales trend, category mix
2. **Store comparison** — sales ranking and the labour efficiency table above
3. **Labour** — scheduled versus actual hours by weekday, overrun hours and cost

## Repository contents

```
generate_data.py     Generates the synthetic dataset
retail-store-ops.pbix  The Power BI report
screenshots/         Report pages
README.md            This file
```

The CSVs are not committed — `generate_data.py` reproduces them exactly
(fixed random seed).

## Running it

```bash
python generate_data.py
```

Then open `retail-store-ops.pbix` in Power BI Desktop and update the data source
paths to point at your generated files.
