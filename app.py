from flask import Flask, redirect, render_template, request, url_for, jsonify

from db import init_db
from services import (
    complete_activity,
    create_customer,
    list_dashboard_data,
    load_all_recipe_data,
    mark_order_delivered,
    place_order,
    seed_defaults,
    get_stock_snapshot,
    add_prep_stock,
    add_prod_stock,
    create_purchase_order,
    get_purchase_by_id,
    update_purchase_order,
)

app = Flask(__name__)


@app.route("/")
def index():
    data = list_dashboard_data()
    raw_stock, prep_stock, prod_stock = get_stock_snapshot()
    return render_template(
        "index.html",
        data=data,
        raw_stock=raw_stock,
        prep_stock=prep_stock,
        prod_stock=prod_stock,
        message=request.args.get("message", ""),
        error=request.args.get("error", ""),
    )


@app.post("/setup")
def setup_data():
    try:
        init_db()
        seed_defaults()
        load_all_recipe_data()
        message = "Database initialized and recipe files loaded"
        return redirect(url_for("index", message=message))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


@app.post("/orders")
def create_order():
    try:
        customer_id = int(request.form["customer_id"])
        place = request.form["place"]
        prod_id = int(request.form["prod_id"])
        quantity = float(request.form["quantity"])
        delivery_date = request.form.get("delivery_date")
        delivery_window = request.form.get("delivery_window", "morning")
        result = place_order(
            customer_id,
            place,
            [{"prod_id": prod_id, "quantity": quantity}],
            delivery_date=delivery_date,
            delivery_window=delivery_window,
        )
        message = f"Order #{result['order_id']} created"
        if result["warnings"]:
            message += " | " + " | ".join(result["warnings"])
        return redirect(url_for("index", message=message))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


@app.post("/customers")
def add_customer():
    try:
        customer_id = create_customer(
            request.form.get("name", ""),
            phone=request.form.get("phone", ""),
            email=request.form.get("email", ""),
        )
        return redirect(url_for("index", message=f"Customer #{customer_id} added"))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


@app.post("/activity/<int:activity_id>/complete")
def finish_activity(activity_id):
    try:
        complete_activity(activity_id, made_by=1)
        return redirect(url_for("index", message=f"Activity #{activity_id} completed"))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


@app.post("/stock/prep")
def stock_prep():
    try:
        prep_id = int(request.form["prep_id"])
        quantity = float(request.form["quantity"])
        add_prep_stock(prep_id, quantity, made_by=1)
        return redirect(url_for("index", message="Prep stock updated"))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


@app.post("/stock/product")
def stock_product():
    try:
        prod_id = int(request.form["prod_id"])
        quantity = float(request.form["quantity"])
        cafeteria = request.form.get("cafeteria", "kafe_1")
        add_prod_stock(prod_id, quantity, made_by=1, to_cafeteria=cafeteria)
        return redirect(url_for("index", message="Product stock updated"))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


@app.post("/purchase")
def create_purchase():
    try:
        purchase_type = request.form.get("purchase_type", "raw")
        if purchase_type not in ("raw", "product"):
            purchase_type = "raw"
        items = request.form.getlist("raw_id")
        quantities = request.form.getlist("quantity")
        contents = {}
        for raw_id, qty in zip(items, quantities):
            if raw_id and qty:
                contents[raw_id] = float(qty)
        purchase_id = create_purchase_order(contents, purchase_type=purchase_type, worker_id=1)
        return redirect(url_for("index", message=f"Purchase order #{purchase_id} created"))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


@app.post("/purchase/<int:purchase_id>/update")
def update_purchase(purchase_id):
    try:
        items = request.form.getlist("raw_id")
        quantities = request.form.getlist("quantity")
        contents = {}
        for raw_id, qty in zip(items, quantities):
            if raw_id and qty:
                contents[raw_id] = float(qty)
        update_purchase_order(purchase_id, contents)
        return redirect(url_for("index", message=f"Purchase order #{purchase_id} updated"))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


@app.post("/orders/<int:order_id>/delivered")
def set_order_delivered(order_id):
    try:
        mark_order_delivered(order_id)
        return redirect(url_for("index", message=f"Order #{order_id} marked delivered"))
    except Exception as exc:
        return redirect(url_for("index", error=str(exc)))


if __name__ == "__main__":
    init_db()
    seed_defaults()
    app.run(host="0.0.0.0", port=8000, debug=True)

