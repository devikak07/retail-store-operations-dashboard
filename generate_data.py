"""
Synthetic retail store operations dataset generator.
Produces a star schema suitable for Power BI:
  dim_date, dim_store, dim_product, dim_employee
  fact_sales, fact_labour, fact_footfall
All data is fabricated. No real company or personal data is used.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(42)

START = date(2024, 1, 1)
END = date(2025, 12, 31)

OUT = "/home/claude/data"
import os
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- dim_date
dates = pd.date_range(START, END, freq="D")
dim_date = pd.DataFrame({"DateKey": dates})
dim_date["Year"] = dim_date.DateKey.dt.year
dim_date["Quarter"] = "Q" + dim_date.DateKey.dt.quarter.astype(str)
dim_date["MonthNumber"] = dim_date.DateKey.dt.month
dim_date["MonthName"] = dim_date.DateKey.dt.strftime("%b")
dim_date["YearMonth"] = dim_date.DateKey.dt.strftime("%Y-%m")
dim_date["WeekOfYear"] = dim_date.DateKey.dt.isocalendar().week.astype(int)
dim_date["DayName"] = dim_date.DateKey.dt.strftime("%a")
dim_date["DayOfWeek"] = dim_date.DateKey.dt.dayofweek + 1
dim_date["IsWeekend"] = dim_date.DayOfWeek.isin([6, 7])
dim_date["DateKey"] = dim_date.DateKey.dt.date

# ---------------------------------------------------------------- dim_store
stores = [
    ("ST01", "Friern Barnet", "London North", 4200, "Retail Park", date(2016, 3, 14)),
    ("ST02", "Croydon",       "London South", 6100, "Retail Park", date(2013, 9, 2)),
    ("ST03", "Watford",       "Home Counties", 3400, "High Street", date(2019, 6, 24)),
    ("ST04", "Reading",       "Home Counties", 5200, "Retail Park", date(2011, 11, 7)),
    ("ST05", "Ilford",        "London East",  2900, "High Street", date(2021, 2, 15)),
]
dim_store = pd.DataFrame(stores, columns=[
    "StoreKey", "StoreName", "Region", "FloorAreaSqFt", "StoreFormat", "OpenedDate"])
# baseline daily transaction volume, scaled by size
dim_store["_base_txns"] = [95, 140, 70, 120, 60]
dim_store["_conversion"] = [0.34, 0.31, 0.38, 0.33, 0.36]

# ---------------------------------------------------------------- dim_product
categories = {
    "Dog":           (["Dry Food", "Wet Food", "Treats", "Toys", "Beds", "Leads & Collars"], 0.34),
    "Cat":           (["Dry Food", "Wet Food", "Treats", "Litter", "Toys", "Scratchers"],    0.26),
    "Small Animal":  (["Bedding", "Hay & Forage", "Dry Food", "Hutches", "Toys"],            0.12),
    "Aquatics":      (["Fish Food", "Tanks", "Filters", "Decor", "Water Treatment"],         0.14),
    "Reptile":       (["Live Food", "Heating", "Substrate", "Vivariums"],                    0.05),
    "Wild Bird":     (["Seed & Feed", "Feeders", "Suet"],                                    0.09),
}
brands = ["Wainwright's", "AVA", "Harringtons", "Purely", "Step Up", "Own Label", "Nutriment"]

prod_rows = []
pid = 1
for cat, (subs, _) in categories.items():
    for sub in subs:
        n = int(rng.integers(4, 9))
        for _ in range(n):
            brand = rng.choice(brands)
            # most SKUs are low-value consumables; hardlines are the long tail
            if sub in ("Hutches", "Tanks", "Vivariums", "Beds", "Filters", "Heating"):
                cost = float(np.round(rng.uniform(14.0, 85.0), 2))
            else:
                cost = float(np.round(min(38.0, rng.lognormal(1.15, 0.62)), 2))
            margin = rng.uniform(0.28, 0.55)
            price = float(np.round(cost / (1 - margin), 2))
            # consumables sell constantly; hardlines are occasional purchases
            if sub in ("Hutches", "Tanks", "Vivariums", "Beds", "Filters",
                       "Heating", "Scratchers"):
                weight = rng.uniform(0.02, 0.08)
            elif sub in ("Toys", "Decor", "Leads & Collars", "Feeders"):
                weight = rng.uniform(0.3, 0.7)
            else:
                weight = rng.uniform(1.0, 2.2)
            prod_rows.append((
                f"P{pid:04d}",
                f"{brand} {sub} {int(rng.integers(1,900))}",
                cat, sub, brand, cost, price,
                bool(rng.random() < 0.18),          # own brand flag
                round(weight, 3),
            ))
            pid += 1
dim_product = pd.DataFrame(prod_rows, columns=[
    "ProductKey", "ProductName", "Category", "Subcategory", "Brand",
    "UnitCost", "UnitPrice", "IsOwnBrand", "_weight"])

# ---------------------------------------------------------------- dim_employee
first = ["Amelia","Josh","Priya","Marcus","Leah","Tom","Sofia","Daniel","Grace","Omar",
         "Chloe","Ben","Nadia","Ryan","Ella","Kofi","Maya","Liam","Zara","Callum",
         "Isla","Hassan","Freya","Noah","Ruby","Ethan","Lucy","Adam","Nina","Jack"]
last = ["Baker","Nolan","Shah","Reid","Frost","Doyle","Marsh","Quinn","Hale","Byrne",
        "Ward","Ellis","Khan","Payne","Vance","Mensah","Rowe","Gale","Ahmed","Blake"]
roles = [("Store Manager",1,18.40),("Duty Manager",2,14.10),("Team Leader",2,12.80),
         ("Retail Assistant",9,11.60),("Groomer",2,13.50)]

emp_rows = []
eid = 1
for _, s in dim_store.iterrows():
    for role, count, rate in roles:
        for _ in range(count):
            emp_rows.append((
                f"E{eid:04d}",
                f"{rng.choice(first)} {rng.choice(last)}",
                s.StoreKey, role,
                float(np.round(rate * rng.uniform(0.96, 1.08), 2)),
                START - timedelta(days=int(rng.integers(60, 2200))),
                bool(rng.random() < 0.55),           # part time
            ))
            eid += 1
dim_employee = pd.DataFrame(emp_rows, columns=[
    "EmployeeKey", "EmployeeName", "StoreKey", "Role", "HourlyRate",
    "HireDate", "IsPartTime"])

# ---------------------------------------------------------------- seasonality
def season_factor(d):
    doy = d.timetuple().tm_yday
    # Christmas peak, summer dip, spring uplift
    f = 1.0 + 0.16 * np.sin(2 * np.pi * (doy - 80) / 365)
    if d.month == 12 and d.day <= 24:
        f *= 1.0 + 0.9 * (d.day / 24)
    if d.month == 1:
        f *= 0.88
    if (d.month, d.day) in [(12,25),(12,26),(1,1)]:
        f = 0.0
    return f

dow_factor = {0:0.86, 1:0.84, 2:0.88, 3:0.95, 4:1.12, 5:1.45, 6:1.22}

# ---------------------------------------------------------------- fact tables
cat_names = list(categories.keys())
cat_weights = np.array([v[1] for v in categories.values()])
cat_weights = cat_weights / cat_weights.sum()
prod_by_cat = {c: dim_product[dim_product.Category == c].reset_index(drop=True)
               for c in cat_names}
prod_probs = {c: (df._weight / df._weight.sum()).to_numpy()
              for c, df in prod_by_cat.items()}

sales_rows, footfall_rows, labour_rows = [], [], []
txn_id = 1

emp_by_store = {k: g for k, g in dim_employee.groupby("StoreKey")}

for _, s in dim_store.iterrows():
    growth = rng.uniform(0.00008, 0.00035)     # slow underlying trend
    for i, d in enumerate(dim_date.DateKey):
        sf = season_factor(d)
        if sf == 0.0:
            continue
        f = sf * dow_factor[d.weekday()] * (1 + growth * i)
        txns = max(1, int(rng.poisson(s._base_txns * f)))
        conv = min(0.85, max(0.05, rng.normal(s._conversion, 0.03)))
        footfall = int(txns / conv)

        footfall_rows.append((d, s.StoreKey, footfall, txns))

        # ---- labour: scheduled vs actual, deliberately imperfect
        emps = emp_by_store[s.StoreKey]
        # rota scales with the day's trade, not a flat headcount
        crew = int(np.clip(round(2 + 2.2 * f), 2, min(7, len(emps))))
        working = emps.sample(n=crew,
                              random_state=int(rng.integers(0, 1e6)))
        for _, e in working.iterrows():
            sched = float(rng.choice([4, 4.5, 5, 6, 7.5, 8]))
            actual = max(0.0, sched + float(rng.normal(0.25, 0.6)))
            labour_rows.append((d, s.StoreKey, e.EmployeeKey,
                                round(sched, 2), round(actual, 2),
                                round(actual * e.HourlyRate, 2)))

        # ---- sales: each transaction is a basket of 1-5 lines
        for _ in range(txns):
            tid = f"T{txn_id:08d}"
            txn_id += 1
            n_lines = int(rng.choice([1, 2, 3, 4, 5], p=[.45, .27, .15, .08, .05]))
            line_no = 1
            for c in rng.choice(cat_names, size=n_lines, p=cat_weights):
                pool = prod_by_cat[c]
                p = pool.iloc[int(rng.choice(len(pool), p=prod_probs[c]))]
                qty = int(rng.choice([1,1,1,2,2,3,4], p=[.42,.2,.1,.13,.07,.05,.03]))
                promo = rng.random() < 0.14
                disc = float(np.round(rng.choice([0.10, 0.15, 0.20, 0.25]), 2)) if promo else 0.0
                net = round(p.UnitPrice * qty * (1 - disc), 2)
                sales_rows.append((
                    f"{tid}-{line_no}", tid, d, s.StoreKey, p.ProductKey,
                    qty, net, round(p.UnitCost * qty, 2), disc, promo))
                line_no += 1

fact_sales = pd.DataFrame(sales_rows, columns=[
    "SalesLineID","TransactionID","DateKey","StoreKey","ProductKey","Quantity",
    "NetSales","CostOfGoods","DiscountPct","IsPromotion"])
fact_footfall = pd.DataFrame(footfall_rows, columns=[
    "DateKey","StoreKey","Footfall","Transactions"])
fact_labour = pd.DataFrame(labour_rows, columns=[
    "DateKey","StoreKey","EmployeeKey","ScheduledHours","ActualHours","LabourCost"])

# ---------------------------------------------------------------- write
dim_store = dim_store.drop(columns=["_base_txns", "_conversion"])
dim_product = dim_product.drop(columns=["_weight"])

for name, df in [("dim_date", dim_date), ("dim_store", dim_store),
                 ("dim_product", dim_product), ("dim_employee", dim_employee),
                 ("fact_sales", fact_sales), ("fact_footfall", fact_footfall),
                 ("fact_labour", fact_labour)]:
    df.to_csv(f"{OUT}/{name}.csv", index=False)
    print(f"{name:16s} {len(df):>8,} rows")

print("\nSales total: £{:,.0f}".format(fact_sales.NetSales.sum()))
print("Labour total: £{:,.0f}".format(fact_labour.LabourCost.sum()))
