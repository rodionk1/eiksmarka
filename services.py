import json
from datetime import date
from pathlib import Path

from db import BASE_DIR, execute, fetch_all, fetch_one, get_connection

PREPS_DIR = BASE_DIR / "preps"
PRODUCTS_DIR = BASE_DIR / "products"


def _today():
    return date.today().isoformat()


def parse_recipe_file(path: Path):
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
    if not lines:
        raise ValueError(f"Recipe file {path} is empty")

    header = [p.strip() for p in lines[0].split(";")]
    if len(header) != 3:
        raise ValueError(f"Invalid header in {path}. Expected 'name;default_qty;unit'")

    name, default_qty, unit = header
    ingredients = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(";")]
        if len(parts) != 4:
            raise ValueError(f"Invalid ingredient line in {path}: {line}")
        source_type, ingredient_name, qty, ing_unit = parts
        if source_type not in {"raw", "prep"}:
            raise ValueError(f"Invalid ingredient source '{source_type}' in {path}")
        ingredients.append({
            "source_type": source_type,
            "ingredient_name": ingredient_name,
            "qty": float(qty),
            "unit": ing_unit,
        })

    return {
        "name": name,
        "default_qty": float(default_qty),
        "unit": unit,
        "ingredients": ingredients,
    }


def load_raw_products_from_file(path: Path):
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
    with get_connection() as conn:
        for line in lines:
            parts = [p.strip() for p in line.split(";")]
            if len(parts) < 5:
                raise ValueError(f"Invalid raw line: {line}")
            name = parts[0]
            quantity = float(parts[1])
            unit = parts[2]
            min_q = float(parts[3])
            price = float(parts[4])

            row = conn.execute("SELECT Raw_id FROM Raw_products WHERE Raw_name_nor = ?", (name,)).fetchone()
            if row:
                raw_id = row["Raw_id"]
            else:
                raw_id = conn.execute(
                    "INSERT INTO Raw_products (Raw_name_nor, Raw_name_rus, Raw_name_pl) VALUES (?, ?, ?)",
                    (name, "", ""),
                ).lastrowid

            exists = conn.execute("SELECT Raw_id FROM Storage_raw WHERE Raw_id = ?", (raw_id,)).fetchone()
            if exists:
                conn.execute(
                    "UPDATE Storage_raw SET Quantity = ?, Unit = ?, Min_quantity = ?, Price_pr_unit = ? WHERE Raw_id = ?",
                    (quantity, unit, min_q, price, raw_id),
                )
            else:
                conn.execute(
                    "INSERT INTO Storage_raw (Raw_id, Unit, Quantity, Min_quantity, Price_pr_unit) VALUES (?, ?, ?, ?, ?)",
                    (raw_id, unit, quantity, min_q, price),
                )
        conn.commit()


def _build_ingredient_json(ingredients):
    prep_map = {}
    raw_map = {}
    with get_connection() as conn:
        for item in ingredients:
            qty = item["qty"]
            if item["source_type"] == "prep":
                row = conn.execute("SELECT Prep_id FROM Preps WHERE Prep_name = ?", (item["ingredient_name"],)).fetchone()
                if not row:
                    raise ValueError(f"Unknown prep ingredient: {item['ingredient_name']}")
                prep_map[str(row["Prep_id"])] = qty
            else:
                row = conn.execute("SELECT Raw_id FROM Raw_products WHERE Raw_name_nor = ?", (item["ingredient_name"],)).fetchone()
                if not row:
                    raise ValueError(f"Unknown raw ingredient: {item['ingredient_name']}")
                raw_map[str(row["Raw_id"])] = qty
    return prep_map, raw_map


def load_preps_from_folder(folder: Path = PREPS_DIR):
    for path in sorted(folder.glob("*.txt")):
        recipe = parse_recipe_file(path)
        prep_json, raw_json = _build_ingredient_json(recipe["ingredients"])
        row = fetch_one("SELECT Prep_id FROM Preps WHERE Prep_name = ?", (recipe["name"],))
        if row:
            execute(
                "UPDATE Preps SET Ingredients_prep = ?, Ingredients_raw = ?, Unit = ?, Default_qty = ? WHERE Prep_id = ?",
                (json.dumps(prep_json), json.dumps(raw_json), recipe["unit"], recipe["default_qty"], row["Prep_id"]),
            )
        else:
            execute(
                "INSERT INTO Preps (Prep_name, Ingredients_prep, Ingredients_raw, Unit, Default_qty) VALUES (?, ?, ?, ?, ?)",
                (recipe["name"], json.dumps(prep_json), json.dumps(raw_json), recipe["unit"], recipe["default_qty"]),
            )


def load_products_from_folder(folder: Path = PRODUCTS_DIR):
    for path in sorted(folder.glob("*.txt")):
        if path.name == "raw_products.txt":
            continue
        recipe = parse_recipe_file(path)
        prep_json, raw_json = _build_ingredient_json(recipe["ingredients"])
        row = fetch_one("SELECT Prod_id FROM Products WHERE Prod_name = ?", (recipe["name"],))
        if row:
            execute(
                "UPDATE Products SET Ingredients_prep = ?, Ingredients_raw = ?, Unit = ?, Default_quantity = ? WHERE Prod_id = ?",
                (json.dumps(prep_json), json.dumps(raw_json), recipe["unit"], recipe["default_qty"], row["Prod_id"]),
            )
        else:
            execute(
                "INSERT INTO Products (Prod_name, Unit, Default_quantity, Ingredients_prep, Ingredients_raw, Sales_price_pr_unit) VALUES (?, ?, ?, ?, ?, 0)",
                (recipe["name"], recipe["unit"], recipe["default_qty"], json.dumps(prep_json), json.dumps(raw_json)),
            )


def load_all_recipe_data():
    raw_file = PRODUCTS_DIR / "raw_products.txt"
    if raw_file.exists():
        load_raw_products_from_file(raw_file)
    load_preps_from_folder()
    load_products_from_folder()


def get_stock_snapshot():
    raw_rows = fetch_all(
        "SELECT rp.Raw_name_nor as name, sr.Quantity as quantity, sr.Unit as unit, sr.Min_quantity as min_quantity "
        "FROM Storage_raw sr JOIN Raw_products rp ON rp.Raw_id = sr.Raw_id ORDER BY name"
    )
    prep_rows = fetch_all(
        "SELECT p.Prep_name as name, COALESCE(SUM(sp.Quantity), 0) as quantity, p.Unit as unit "
        "FROM Preps p LEFT JOIN Storage_prep sp ON sp.Prep_id = p.Prep_id GROUP BY p.Prep_id ORDER BY name"
    )
    prod_rows = fetch_all(
        "SELECT p.Prod_name as name, COALESCE(SUM(sp.Quantity), 0) as quantity, p.Unit as unit "
        "FROM Products p LEFT JOIN Storage_prod sp ON sp.Prod_id = p.Prod_id GROUP BY p.Prod_id ORDER BY name"
    )
    return raw_rows, prep_rows, prod_rows


def _aggregate_prep_stock():
    rows = fetch_all("SELECT Prep_id, COALESCE(SUM(Quantity), 0) as qty FROM Storage_prep GROUP BY Prep_id")
    return {str(r["Prep_id"]): float(r["qty"]) for r in rows}


def _aggregate_raw_stock():
    rows = fetch_all("SELECT Raw_id, Quantity FROM Storage_raw")
    return {str(r["Raw_id"]): float(r["Quantity"]) for r in rows}


def _required_ingredients_for_product(prod_id, quantity):
    row = fetch_one("SELECT Default_quantity, Ingredients_prep, Ingredients_raw FROM Products WHERE Prod_id = ?", (prod_id,))
    if not row:
        raise ValueError("Product not found")
    factor = float(quantity) / float(row["Default_quantity"])
    prep_req = {k: v * factor for k, v in json.loads(row["Ingredients_prep"] or "{}").items()}
    raw_req = {k: v * factor for k, v in json.loads(row["Ingredients_raw"] or "{}").items()}
    return prep_req, raw_req


def _required_ingredients_for_prep(prep_id, quantity):
    row = fetch_one("SELECT Default_qty, Ingredients_prep, Ingredients_raw FROM Preps WHERE Prep_id = ?", (prep_id,))
    if not row:
        raise ValueError("Prep not found")
    factor = float(quantity) / float(row["Default_qty"])
    prep_req = {k: v * factor for k, v in json.loads(row["Ingredients_prep"] or "{}").items()}
    raw_req = {k: v * factor for k, v in json.loads(row["Ingredients_raw"] or "{}").items()}
    return prep_req, raw_req


def _plan_missing_preps(total_prep_req, total_raw_req, prep_stock):
    pending_prep_req = dict(total_prep_req)
    planned_prep_qty = {}
    expanded_raw_req = dict(total_raw_req)

    # Expand prep requirements recursively so nested preps are also planned.
    while pending_prep_req:
        current_req = pending_prep_req
        pending_prep_req = {}

        for prep_id, req in current_req.items():
            available = prep_stock.get(prep_id, 0)
            if available >= req:
                prep_stock[prep_id] = available - req
                continue

            missing_qty = req - available
            prep_stock[prep_id] = 0
            planned_prep_qty[prep_id] = planned_prep_qty.get(prep_id, 0) + missing_qty

            nested_prep_req, nested_raw_req = _required_ingredients_for_prep(int(prep_id), missing_qty)
            for nested_prep_id, nested_qty in nested_prep_req.items():
                pending_prep_req[nested_prep_id] = pending_prep_req.get(nested_prep_id, 0) + nested_qty
            for raw_id, raw_qty in nested_raw_req.items():
                expanded_raw_req[raw_id] = expanded_raw_req.get(raw_id, 0) + raw_qty

    return planned_prep_qty, expanded_raw_req


def _upsert_purchase_for_missing_raw(missing_raw):
    if not missing_raw:
        return None
    return execute(
        "INSERT INTO Purchase (Date, Contents, Made_by, Control, Accomplished, Purchase_type) VALUES (?, ?, NULL, 0, 0, 'raw')",
        (_today(), json.dumps(missing_raw)),
    )


def _names_for_missing(prep_missing, raw_missing):
    warnings = []
    for prep_id, qty in prep_missing.items():
        row = fetch_one("SELECT Prep_name FROM Preps WHERE Prep_id = ?", (int(prep_id),))
        if row:
            warnings.append(f"Missing prep: {row['Prep_name']} ({qty:.2f})")
    for raw_id, qty in raw_missing.items():
        row = fetch_one("SELECT Raw_name_nor FROM Raw_products WHERE Raw_id = ?", (int(raw_id),))
        if row:
            warnings.append(f"Missing raw: {row['Raw_name_nor']} ({qty:.2f})")
    return warnings


def place_order(customer_id, cafeteria, items):
    prep_stock = _aggregate_prep_stock()
    raw_stock = _aggregate_raw_stock()

    total_prep_req = {}
    total_raw_req = {}

    for item in items:
        prep_req, raw_req = _required_ingredients_for_product(item["prod_id"], item["quantity"])
        for key, value in prep_req.items():
            total_prep_req[key] = total_prep_req.get(key, 0) + value
        for key, value in raw_req.items():
            total_raw_req[key] = total_raw_req.get(key, 0) + value

    planned_prep_qty, total_raw_req = _plan_missing_preps(total_prep_req, total_raw_req, dict(prep_stock))

    missing_prep = {}
    missing_raw = {}
    for key, req in planned_prep_qty.items():
        if req > 0:
            missing_prep[key] = req
    for key, req in total_raw_req.items():
        available = raw_stock.get(key, 0)
        if available < req:
            missing_raw[key] = req - available

    purchase_id = _upsert_purchase_for_missing_raw(missing_raw)
    warnings = _names_for_missing(missing_prep, missing_raw)
    if purchase_id:
        warnings.append(f"Purchase order #{purchase_id} created for missing raw products")

    order_id = execute(
        "INSERT INTO Orders (Customer_id, Cafeteria, Date, Content, Warning) VALUES (?, ?, ?, ?, ?)",
        (customer_id, cafeteria, _today(), json.dumps(items), " | ".join(warnings)),
    )

    for prep_id, qty in planned_prep_qty.items():
        prep = fetch_one("SELECT Unit FROM Preps WHERE Prep_id = ?", (int(prep_id),))
        execute(
            "INSERT INTO Activity (Order_id, Product_type, Product_id, Quantity, Unit, Date, Control, Accomplished) VALUES (?, 'prep', ?, ?, ?, ?, 0, 0)",
            (order_id, int(prep_id), qty, prep["Unit"], _today()),
        )

    for item in items:
        prod = fetch_one("SELECT Unit FROM Products WHERE Prod_id = ?", (item["prod_id"],))
        execute(
            "INSERT INTO Activity (Order_id, Product_type, Product_id, Quantity, Unit, Date, Control, Accomplished) VALUES (?, 'prod', ?, ?, ?, ?, 0, 0)",
            (order_id, item["prod_id"], item["quantity"], prod["Unit"], _today()),
        )

    return {
        "order_id": order_id,
        "warnings": warnings,
    }


def add_prep_stock(prep_id, quantity, made_by=None):
    execute(
        "INSERT INTO Storage_prep (Prep_id, Quantity, Unit, Made_date, Made_by) "
        "SELECT Prep_id, ?, Unit, ?, ? FROM Preps WHERE Prep_id = ?",
        (quantity, _today(), made_by, prep_id),
    )


def add_prod_stock(prod_id, quantity, made_by=None, to_cafeteria=None):
    if to_cafeteria == "kafe_2":
        execute(
            "INSERT INTO Kafe_2 (Prod_id, Quantity, Made_date, Made_by) VALUES (?, ?, ?, ?)",
            (prod_id, quantity, _today(), made_by),
        )
    else:
        execute(
            "INSERT INTO Storage_prod (Prod_id, Quantity, Made_date, Made_by) VALUES (?, ?, ?, ?)",
            (prod_id, quantity, _today(), made_by),
        )


def _consume_raw(raw_requirements):
    with get_connection() as conn:
        for raw_id, qty in raw_requirements.items():
            row = conn.execute("SELECT Quantity FROM Storage_raw WHERE Raw_id = ?", (int(raw_id),)).fetchone()
            if not row or row["Quantity"] < qty:
                raise ValueError(f"Insufficient raw material {raw_id}")
            conn.execute("UPDATE Storage_raw SET Quantity = Quantity - ? WHERE Raw_id = ?", (qty, int(raw_id)))
        conn.commit()


def _consume_prep(prep_requirements):
    with get_connection() as conn:
        for prep_id, needed in prep_requirements.items():
            available = conn.execute(
                "SELECT COALESCE(SUM(Quantity), 0) as qty FROM Storage_prep WHERE Prep_id = ?",
                (int(prep_id),),
            ).fetchone()["qty"]
            if available < needed:
                raise ValueError(f"Insufficient prep {prep_id}")

            rows = conn.execute(
                "SELECT ID, Quantity FROM Storage_prep WHERE Prep_id = ? ORDER BY ID",
                (int(prep_id),),
            ).fetchall()
            remaining = needed
            for row in rows:
                if remaining <= 0:
                    break
                used = min(remaining, row["Quantity"])
                conn.execute("UPDATE Storage_prep SET Quantity = Quantity - ? WHERE ID = ?", (used, row["ID"]))
                remaining -= used
            conn.execute("DELETE FROM Storage_prep WHERE Quantity <= 0")
        conn.commit()


def complete_activity(activity_id, made_by=None):
    activity = fetch_one("SELECT * FROM Activity WHERE ID = ?", (activity_id,))
    if not activity:
        raise ValueError("Activity not found")
    if activity["Accomplished"]:
        return

    if activity["Product_type"] == "prod" and activity["Order_id"] is not None:
        pending = fetch_one(
            "SELECT COUNT(1) as count FROM Activity WHERE Order_id = ? AND Product_type = 'prep' AND Accomplished = 0",
            (activity["Order_id"],),
        )
        if pending and pending["count"] > 0:
            raise ValueError("Cannot complete product activity before prep activities are finished for this order")

    quantity = float(activity["Quantity"])

    if activity["Product_type"] == "prod":
        prep_req, raw_req = _required_ingredients_for_product(activity["Product_id"], quantity)
        _consume_prep(prep_req)
        _consume_raw(raw_req)
        add_prod_stock(activity["Product_id"], quantity, made_by)
    else:
        prep = fetch_one("SELECT * FROM Preps WHERE Prep_id = ?", (activity["Product_id"],))
        factor = quantity / float(prep["Default_qty"])
        prep_req = {k: v * factor for k, v in json.loads(prep["Ingredients_prep"] or "{}").items()}
        raw_req = {k: v * factor for k, v in json.loads(prep["Ingredients_raw"] or "{}").items()}
        _consume_prep(prep_req)
        _consume_raw(raw_req)
        add_prep_stock(activity["Product_id"], quantity, made_by)

    execute("UPDATE Activity SET Accomplished = 1, Control = 1 WHERE ID = ?", (activity_id,))


def list_dashboard_data():
    products = fetch_all("SELECT * FROM Products ORDER BY Prod_name")
    preps = fetch_all("SELECT * FROM Preps ORDER BY Prep_name")
    orders = fetch_all("SELECT * FROM Orders ORDER BY ID DESC LIMIT 20")
    activities = fetch_all("""
        SELECT a.*, 
               COALESCE(pr.Prod_name, p.Prep_name) as item_name
        FROM Activity a
        LEFT JOIN Products pr ON a.Product_type = 'prod' AND a.Product_id = pr.Prod_id
        LEFT JOIN Preps p ON a.Product_type = 'prep' AND a.Product_id = p.Prep_id
        ORDER BY a.Accomplished ASC, a.ID DESC LIMIT 50
    """)
    
    # Separate purchase orders by type
    raw_purchases = fetch_all("""
        SELECT p.*, COALESCE(w.Name, 'System') as made_by_name
        FROM Purchase p
        LEFT JOIN Workers w ON p.Made_by = w.ID
        WHERE p.Purchase_type = 'raw'
        ORDER BY p.Accomplished ASC, p.ID DESC LIMIT 20
    """)
    product_purchases = fetch_all("""
        SELECT p.*, COALESCE(w.Name, 'System') as made_by_name
        FROM Purchase p
        LEFT JOIN Workers w ON p.Made_by = w.ID
        WHERE p.Purchase_type = 'product'
        ORDER BY p.Accomplished ASC, p.ID DESC LIMIT 20
    """)
    
    customers = fetch_all("SELECT * FROM Customers ORDER BY Name")
    workers = fetch_all("SELECT * FROM Workers ORDER BY Name")
    
    # Extract raw products for purchase modal
    raw_products = fetch_all("SELECT Raw_id, Raw_name_nor FROM Raw_products ORDER BY Raw_name_nor")
    
    return {
        "products": products,
        "preps": preps,
        "orders": orders,
        "activities": activities,
        "raw_purchases": raw_purchases,
        "product_purchases": product_purchases,
        "customers": customers,
        "workers": workers,
        "raw_products": raw_products,
    }


def seed_defaults():
    if not fetch_one("SELECT ID FROM Workers LIMIT 1"):
        execute("INSERT INTO Workers (Name) VALUES ('System')")
        execute("INSERT INTO Workers (Name) VALUES ('Kitchen Team')")
    if not fetch_one("SELECT ID FROM Customers LIMIT 1"):
        execute("INSERT INTO Customers (Phone, Name, Email) VALUES ('00000000', 'Walk-in', 'local@shop.no')")


def create_purchase_order(order_contents, purchase_type="raw", worker_id=None):
    """Create a manual purchase order. order_contents is dict of {raw_id: quantity} or {product_id: quantity}.
    purchase_type must be 'raw' or 'product'."""
    if not order_contents:
        raise ValueError("Purchase order must contain at least one item")
    if purchase_type not in ("raw", "product"):
        raise ValueError("Purchase type must be 'raw' or 'product'")
    return execute(
        "INSERT INTO Purchase (Date, Contents, Made_by, Control, Accomplished, Purchase_type) VALUES (?, ?, ?, 0, 0, ?)",
        (_today(), json.dumps(order_contents), worker_id, purchase_type),
    )


def get_purchase_by_id(purchase_id):
    """Fetch a single purchase order with details."""
    return fetch_one("SELECT * FROM Purchase WHERE ID = ?", (purchase_id,))


def update_purchase_order(purchase_id, new_contents):
    """Update purchase order contents (as dict of raw_id: qty). Only if not accomplished."""
    purchase = get_purchase_by_id(purchase_id)
    if not purchase:
        raise ValueError("Purchase not found")
    if purchase["Accomplished"]:
        raise ValueError("Cannot modify accomplished purchase orders")
    execute(
        "UPDATE Purchase SET Contents = ? WHERE ID = ?",
        (json.dumps(new_contents), purchase_id),
    )

