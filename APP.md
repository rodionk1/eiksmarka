# Web App for Kitchen + 2 Cafeterias

## App Structure

The web app uses a **full-window tabbed interface** with three role-based sections:

1. **Admin Tab**
   - Register customer orders for cafeteria 1 or cafeteria 2
   - View recent orders and warnings  
   - Production and purchase orders auto-created based on availability checks

2. **Kitchen Tab**
   - Add prep stock batches
   - View production activities with product/prep names (not IDs)
   - Complete production activities (sequenced: preps before products)

3. **Cafeteria Tab**
   - Send finished products to kafe_1 (main storage) or kafe_2 (remote)
   - **Purchase order management:**
     - Open a modal to create new purchase orders
     - Add multiple raw materials with adjustable quantities
     - Edit existing purchase orders (if not yet accomplished)
   - View stock levels (raw materials, preps, ready products)

Tab state is stored in browser localStorage, so the last-used tab is remembered on reload.

## Purchase Order Modal

When raw materials are missing from an order:
- A Purchase record is auto-created with missing items
- The **Cafeteria** tab shows all purchase orders in a table
- Click **+ New Purchase Order** to open the modal and manually create orders
- Inside modal:
  - Add multiple items by selecting raw material + quantity
  - Use **+ Add Item** to add more rows
  - Use **Remove** to delete rows
  - Submit to create the order
- Click an existing order's **Edit** button to modify quantities (if not accomplished)

## Interaction Between Tables

1. Order registration (`Orders`):
- User creates order via Admin tab with product and quantity.
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
- All activities for an order share the same Order_id for sequencing.

5. Production completion:
- When activity is completed:
  - Used preps are deducted from `Storage_prep`
  - Used raw materials are deducted from `Storage_raw`
  - Produced quantity is added to `Storage_prod`
  - `Activity.Accomplished` is set to 1
- Sequence enforcement: a `prod` activity cannot be completed while any `prep` activity for the same order is still not accomplished.

6. Manual purchase orders:
- Use the purchase modal in the Cafeteria tab to create/edit purchase orders manually.
- Adjustable quantities allow flexibility in ordering.
- Multiple raw items can be added in a single purchase order.

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

```bash
pip install -r requirements.txt
```

2. Run app:

```bash
python app.py
```

3. Open in browser:

```
http://localhost:8000
```

4. On first run, click **Initialize DB + Load Files** button at the top to set up database and import recipes from `products/` and `preps/` folders.

5. Use the **Admin**, **Kitchen**, and **Cafeteria** tabs to navigate between roles. Tab state is saved in browser localStorage.

## Free Hosting

For free hosting, this Flask app can be deployed to Render free tier or PythonAnywhere free tier.
Use `gunicorn app:app` as the start command and persist SQLite DB on mounted storage if available.
