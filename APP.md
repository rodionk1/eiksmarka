# Web App for Kitchen + 2 Cafeterias

## App Tabs / Roles

The single web page has 3 sections:

1. Admin:
- Initialize database and load text files from `products/` and `preps/`
- Register orders for cafeteria 1 or cafeteria 2
- View order warnings

2. Kitchen:
- Add prep stock batches
- View planned production activities
- Complete an activity (this subtracts used preps/raw and adds finished stock)

3. Cafeteria:
- Send finished products to kafe_1 (main storage) or kafe_2
- View auto-created purchase planning entries for missing raw products

## Interaction Between Tables

1. Order registration (`Orders`):
- User creates order with product and quantity.
- Engine reads recipe from `Products` and calculates ingredient demand.

2. Availability check:
- Prep availability is checked against `Storage_prep`.
- Raw availability is checked against `Storage_raw`.
- Missing items are added as warning text in `Orders.Warning`.

3. Missing raw products:
- If raw products are missing, app creates `Purchase` entry automatically:
  - `Contents` = JSON with raw IDs and missing quantities
  - `Made_by` = NULL (system-created)
  - `Control` and `Accomplished` = 0

4. Production planning (`Activity`):
- For every ordered product, a production activity is created (`Product_type='prod'`).
- If required prep is missing, prep production activities are added automatically (`Product_type='prep'`).
- Nested prep dependencies are expanded, so preps needed by other preps are also included.

5. Production completion:
- When activity is completed:
  - Used preps are deducted from `Storage_prep`
  - Used raw materials are deducted from `Storage_raw`
  - Produced quantity is added to `Storage_prod`
  - `Activity.Accomplished` is set to 1
- Sequence enforcement: a `prod` activity cannot be completed while any `prep` activity for the same order is still not accomplished.

## Recipe/Text File Format

### Raw products file
`products/raw_products.txt`

One line per raw item:
`name;quantity;unit;min_quantity;price_pr_unit`

### Prep/Product recipe file
First line:
`name;default_qty;unit`

Other lines:
`source_type;ingredient_name;qty;unit`

- `source_type` is `raw` or `prep`
- prep files go in `preps/`
- product files go in `products/`

## Local Start

1. Install dependencies:

`pip install -r requirements.txt`

2. Run app:

`python app.py`

3. Open:

`http://localhost:8000`

4. Click **Initialize DB + Load Files** on first run.

## Free Hosting

For free hosting, this Flask app can be deployed to Render free tier or PythonAnywhere free tier.
Use `gunicorn app:app` as the start command and persist SQLite DB on mounted storage if available.
