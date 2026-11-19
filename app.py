from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import requests

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.secret_key = "foodsave_secret_key_2026"

def update_database():
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("""
            ALTER TABLE food_items
            ADD COLUMN minimum_stock REAL DEFAULT 1
        """)
    except sqlite3.OperationalError:
        pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS consumption_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT,
            consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

@app.context_processor
def inject_user():
    if "user_id" in session:
        return {
            "current_user": {
                "name": session.get("user_name", "User")
            }
        }

    return {
        "current_user": None
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect("/dashboard")

        flash("Invalid email or password", "error")

    return render_template("login.html")




@app.route("/add-food", methods=["GET", "POST"])
def add_food():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        quantity = request.form.get("quantity", 0)
        unit = request.form.get("unit", "")
        purchase_date = request.form.get("purchase_date", "")
        expiry_date = request.form.get("expiry_date", "")
        price = request.form.get("price", 0)
        minimum_stock = request.form.get("minimum_stock", 1)
        storage = request.form.get("storage", "")

        user_id = session["user_id"]

        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO food_items
            (
                user_id,
                name,
                category,
                quantity,
                unit,
                purchase_date,
                expiry_date,
                price,
                minimum_stock,
                storage
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            name,
            category,
            quantity,
            unit,
            purchase_date,
            expiry_date,
            price,
            minimum_stock,
            storage
        ))

        conn.commit()
        conn.close()

        return redirect("/inventory")

    return render_template("add_food.html")

@app.route("/edit-food/<int:food_id>", methods=["GET", "POST"])
def edit_food(food_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    food = conn.execute(
        "SELECT * FROM food_items WHERE id = ? AND user_id = ?",
        (food_id, session["user_id"])
    ).fetchone()

    if not food:
        conn.close()
        return redirect("/inventory")

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        quantity = request.form.get("quantity", 0)
        unit = request.form.get("unit", "")
        purchase_date = request.form.get("purchase_date", "")
        expiry_date = request.form.get("expiry_date", "")
        price = request.form.get("price", 0)
        minimum_stock = request.form.get("minimum_stock", 1)
        storage = request.form.get("storage", "")

        conn.execute("""
            UPDATE food_items
            SET name = ?,
                category = ?,
                quantity = ?,
                unit = ?,
                purchase_date = ?,
                expiry_date = ?,
                price = ?,
                minimum_stock = ?,
                storage = ?
            WHERE id = ? AND user_id = ?
        """, (
            name,
            category,
            quantity,
            unit,
            purchase_date,
            expiry_date,
            price,
            minimum_stock,
            storage,
            food_id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/inventory")

    conn.close()

    return render_template("edit_food.html", food=food)

@app.route("/delete-food/<int:food_id>", methods=["POST"])
def delete_food(food_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "DELETE FROM food_items WHERE id = ? AND user_id = ?",
        (food_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/inventory")

@app.route("/consumption", methods=["GET", "POST"])
def consumption():
    if "user_id" not in session:
        return redirect(url_for("login"))

    from datetime import date

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if request.method == "POST":
        try:
            food_id = int(request.form.get("food_id"))
            quantity = float(request.form.get("quantity_consumed"))
            consumption_date = request.form.get("consumption_date")

            food = conn.execute(
                """SELECT * FROM food_items
                   WHERE id = ? AND user_id = ?""",
                (food_id, session["user_id"])
            ).fetchone()

            if not food:
                flash("Food item not found.", "error")

            elif quantity <= 0 or quantity > float(food["quantity"] or 0):
                flash("Enter a valid quantity within available stock.", "error")

            elif not consumption_date:
                flash("Please select a date.", "error")

            else:
                conn.execute(
                    """UPDATE food_items
                       SET quantity = quantity - ?
                       WHERE id = ? AND user_id = ?""",
                    (quantity, food_id, session["user_id"])
                )

                conn.execute(
                    """INSERT INTO consumption_history
                       (user_id, food_id, food_name, quantity, unit, consumed_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        session["user_id"],
                        food_id,
                        food["name"],
                        quantity,
                        food["unit"],
                        consumption_date
                    )
                )

                conn.commit()
                conn.close()

                flash("Consumption recorded successfully.", "success")
                return redirect(url_for("consumption"))

        except (ValueError, TypeError):
            flash("Please enter valid details.", "error")

    foods = conn.execute(
        """SELECT * FROM food_items
           WHERE user_id = ?
           ORDER BY name""",
        (session["user_id"],)
    ).fetchall()

    history = conn.execute(
        """SELECT food_name AS name,
                  quantity AS quantity_consumed,
                  unit,
                  consumed_at AS consumption_date
           FROM consumption_history
           WHERE user_id = ?
           ORDER BY consumed_at DESC""",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "consumption.html",
        foods=foods,
        history=history,
        today=date.today().isoformat()
    )

@app.route("/inventory")
def inventory():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    foods = conn.execute(
        "SELECT * FROM food_items WHERE user_id = ? ORDER BY expiry_date ASC",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    from datetime import date

    today = date.today()

    food_list = []

    for food in foods:

        food = dict(food)

        if food["expiry_date"]:

            expiry = date.fromisoformat(food["expiry_date"])

            days_remaining = (expiry - today).days

            if days_remaining < 0:
                status = "Expired"

            elif days_remaining <= 3:
                status = "Expiring Soon"

            else:
                status = "Fresh"

        else:
            days_remaining = 0
            status = "Unknown"

        food["days_remaining"] = days_remaining
        food["status"] = status

        food_list.append(food)

    return render_template(
        "inventory.html",
        foods=food_list
    )

@app.route("/expiry")
def expiry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    from datetime import date, timedelta

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    foods = conn.execute(
        """SELECT * FROM food_items
           WHERE user_id = ?
           ORDER BY expiry_date ASC""",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    today_date = date.today()
    tomorrow_date = today_date + timedelta(days=1)

    today = []
    tomorrow = []
    soon = []
    expired = []

    for food in foods:
        item = dict(food)
        expiry_value = item.get("expiry_date")

        if not expiry_value:
            continue

        try:
            expiry_date = date.fromisoformat(expiry_value)
        except (ValueError, TypeError):
            continue

        days_left = (expiry_date - today_date).days

        if days_left < 0:
            expired.append(item)
        elif days_left == 0:
            today.append(item)
        elif days_left == 1:
            tomorrow.append(item)
        elif days_left <= 3:
            soon.append(item)

    return render_template(
        "expiry.html",
        today=today,
        tomorrow=tomorrow,
        soon=soon,
        expired=expired
    )

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    from datetime import date

    user_id = session["user_id"]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    foods = conn.execute(
        "SELECT * FROM food_items WHERE user_id = ? ORDER BY expiry_date ASC",
        (user_id,)
    ).fetchall()
    consumption_history = conn.execute(
    """
    SELECT food_name, quantity, unit, consumed_at
    FROM consumption_history
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT 5
    """,
    (session["user_id"],)
).fetchall()

    conn.close()

    today = date.today()

    fresh = 0
    soon = 0
    expired = 0
    low = 0
    total_qty = 0
    wasted = 0
    loss = 0

    attention_items = []
    suggestions = []

    for food in foods:

        quantity = float(food["quantity"] or 0)
        total_qty += quantity

        # -------------------------
        # EXPIRY STATUS
        # -------------------------

        expiry_date = food["expiry_date"]

        if expiry_date:

            try:
                expiry = date.fromisoformat(expiry_date)
                days_left = (expiry - today).days
            except:
                days_left = 999

            if days_left < 0:
                expired += 1
                status = "Expired"

            elif days_left <= 3:
                soon += 1
                status = "Expiring Soon"

            else:
                fresh += 1
                status = "Fresh"

        else:
            days_left = 999
            status = "Fresh"

        # -------------------------
        # LOW STOCK
        # -------------------------

        minimum_stock = float(food["minimum_stock"] or 1)

        is_low = quantity <= minimum_stock

        if is_low:
            low += 1

        # -------------------------
        # ATTENTION ITEMS
        # -------------------------

        if is_low or status == "Expiring Soon" or status == "Expired":

            attention_items.append({
                "name": food["name"],
                "quantity": quantity,
                "unit": food["unit"],
                "minimum_stock": minimum_stock,
                "expiry_date": food["expiry_date"],
                "status": status,
                "days_remaining": days_left
            })

    # -------------------------
    # RECIPE / USAGE SUGGESTIONS
    # -------------------------

    ingredients = [
        food["name"].lower().strip()
        for food in foods
        if food["quantity"] and float(food["quantity"]) > 0
    ]

    if "bread" in ingredients:
        suggestions.append("Use bread soon to avoid wastage.")

    if "banana" in ingredients:
        suggestions.append("Banana milkshake can be prepared using available bananas.")

    if "milk" in ingredients:
        suggestions.append("Use milk before its expiry date.")

    if "rice" in ingredients:
        suggestions.append("Rice can be used to prepare a quick meal.")

    if "vegetables" in ingredients or "vegetable" in ingredients:
        suggestions.append("Use available vegetables in a mixed vegetable dish.")

    if soon > 0:
        suggestions.append(
            "Some food items are expiring soon. Consider using them first."
        )

    if not suggestions and foods:
        suggestions.append(
            "Your food inventory is currently in good condition."
        )

    # -------------------------
    # RECENTLY ADDED
    # -------------------------

    recent_foods = sorted(
        foods,
        key=lambda x: x["id"],
        reverse=True
    )[:5]

    current_user = {
        "name": session.get("user_name", "User")
    }

    return render_template(
        "dashboard.html",
        current_user=current_user,
        foods=foods,
        fresh=fresh,
        soon=soon,
        expired=expired,
        low=low,
        total_qty=total_qty,
        wasted=wasted,
        loss=loss,
        attention_items=attention_items,
        suggestions=suggestions,
        recent_foods=recent_foods
    )
    
@app.route("/recipes")
def recipes():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    inventory = conn.execute(
        """
        SELECT * FROM food_items 
        WHERE user_id = ? AND quantity > 0 
        ORDER BY expiry_date ASC
        """,
        (session["user_id"],)
    ).fetchall()
    conn.close()

    # Get all available lower-case ingredient names
    available = {food["name"].strip().lower() for food in inventory}
    recipes = []
    seen_items = set()

    # 1. DYNAMICALLY ENRICHED SINGLE ITEMS: Automatically uses other available inventory items!
    for food in inventory:
        name = food["name"].strip()
        lower_name = name.lower()
        
        if lower_name not in seen_items:
            seen_items.add(lower_name)
            
            # Automatically find other veggies/items currently in stock to combine with this item
            extras = [item for item in available if item != lower_name and item in ["onion", "tomato", "carrot", "capsicum", "garlic", "potato"]]
            
            if extras:
                extra_str = ", ".join(extras)
                title = f"Desi Style {name.capitalize()} with {extra_str.capitalize()}"
                instructions = f"1. Prep your {lower_name}.\n2. Heat oil in a pan, and sauté your available {extra_str} with Indian spices (turmeric, salt, chili powder) until soft and fragrant.\n3. Toss in your {lower_name}, mix thoroughly, cook for 3-5 minutes, and serve hot!"
            else:
                if any(k in lower_name for k in ["maggie", "maggi", "noodle"]):
                    instructions = "1. Boil 1.5 cups of water in a pan.\n2. Add the noodles and the included tastemaker packet.\n3. Cook for 2 minutes until water is absorbed. Serve hot!"
                else:
                    instructions = f"1. Take {name} from your inventory.\n2. Prepare or cook it according to your preference using basic Indian spices, oil, or heat."
                title = f"Quick {name.capitalize()} Dish"

            recipes.append({
                "title": title,
                "ingredients": [lower_name] + extras,
                "instructions": instructions,
                "score": 1 + len(extras)
            })

    # 2. INDIAN & COMBINATION RECIPE BLUEPRINTS
    RECIPE_BLUEPRINTS = [
        {
            "title": "Classic South Indian Sambar",
            "required": ["dal", "onion"],
            "instructions": "1. Pressure cook dal with a pinch of turmeric and salt until soft.\n2. In a pan, sauté chopped onions and available vegetables with sambar powder and tamarind extract.\n3. Mix the cooked dal into the vegetable gravy, boil for 5 minutes, and temper with mustard seeds and curry leaves."
        },
        {
            "title": "Home-Style Dal Fry",
            "required": ["dal"],
            "instructions": "1. Boil lentils until completely tender.\n2. In a small pan, heat ghee or oil, add cumin seeds, chopped onions, and garlic until golden.\n3. Pour the tempering over the boiled dal, simmer for 2 minutes, and serve hot with rice or roti."
        },
        {
            "title": "Masala Egg Omelette",
            "required": ["egg", "onion"],
            "instructions": "1. Whisk eggs in a bowl with finely chopped onions, green chilies, and salt.\n2. Heat oil or butter in a frying pan over medium heat.\n3. Pour the mixture, cook until golden brown on both sides, and serve hot."
        },
        {
            "title": "Home-Style Egg Curry",
            "required": ["egg", "onion", "tomato"],
            "instructions": "1. Boil and peel eggs, then lightly fry them in a pan with turmeric.\n2. Sauté chopped onions and tomatoes with Indian spices (coriander, cumin, chili powder) until oil separates.\n3. Add water for gravy, drop in the eggs, simmer for 5 minutes, and serve with rice or roti."
        },
        {
            "title": "Classic Aloo Paratha (Potato Flatbread)",
            "required": ["potato", "wheat flour"],
            "instructions": "1. Boil and mash potatoes, mixing in chopped onions, green chilies, salt, and cumin powder.\n2. Stuff the potato mixture into wheat dough balls, roll them out flat.\n3. Cook on a hot tawa with ghee or oil on both sides until golden brown and crispy."
        },
        {
            "title": "Batata Poha (Flattened Rice Breakfast)",
            "required": ["poha", "onion"],
            "instructions": "1. Rinse poha in a colander until soft, then drain completely.\n2. Heat oil in a pan, add mustard seeds, curry leaves, chopped onions, and diced potatoes, cooking until tender.\n3. Add the softened poha, a pinch of turmeric, and salt, toss gently for 3 minutes, and serve hot with lemon."
        },
        {
            "title": "Simple Rava Upma",
            "required": ["sooji", "onion"],
            "instructions": "1. Dry roast sooji (semolina) in a pan until fragrant, then set aside.\n2. In the same pan, heat oil, add mustard seeds, green chilies, and chopped onions, sautéing until translucent.\n3. Pour in water with salt, bring to a boil, slowly stir in the roasted sooji to avoid lumps, cover, and cook for 3 minutes."
        }
    ]

    # Automatically match blueprints against user inventory
    for blueprint in RECIPE_BLUEPRINTS:
        if all(req in available for req in blueprint["required"]):
            recipes.append({
                "title": blueprint["title"],
                "ingredients": blueprint["required"],
                "instructions": blueprint["instructions"],
                "score": len(blueprint["required"])
            })

    return render_template("recipes.html", recipes=recipes, inventory=inventory)
    
@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    foods = conn.execute(
    "SELECT * FROM food_items WHERE user_id = ? ORDER BY expiry_date ASC",
    (session["user_id"],)
    ).fetchall()
    foods = [dict(food) for food in foods]

    conn.close()

    from datetime import date

    today = date.today()

    purchased = 0
    consumption = 0
    wasted = 0
    expenditure = 0
    loss = 0

    fresh = 0
    soon = 0
    expired = 0
    low = 0

    for food in foods:

        quantity = float(food["quantity"] or 0)
        price = float(food["price"] or 0)

        purchased += quantity
        expenditure += price

        # Low stock
        try:
            minimum_stock = float(food["minimum_stock"] or 1)

            if quantity <= minimum_stock:
                low += 1

        except (KeyError, TypeError, ValueError):
            if quantity <= 1:
                low += 1

        # Expiry status
        expiry_value = food["expiry_date"]

        if expiry_value:

            try:
                expiry_date = date.fromisoformat(expiry_value)
                days_left = (expiry_date - today).days

                if days_left < 0:
                    expired += 1

                elif days_left <= 3:
                    soon += 1

                else:
                    fresh += 1

            except ValueError:
                pass

    waste_percentage = 0

    if purchased > 0:
        waste_percentage = (wasted / purchased) * 100

    savings = loss

    return render_template(
        "analytics.html",

        foods=foods,

        purchased=purchased,
        consumption=consumption,
        wasted=wasted,

        expenditure=expenditure,
        loss=loss,
        savings=savings,

        waste_percentage=waste_percentage,

        fresh=fresh,
        soon=soon,
        expired=expired,
        low=low
    )
    
@app.route("/scan")
def scan():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("scan.html")   

@app.route("/search-barcode", methods=["POST"])
def search_barcode():
    if "user_id" not in session:
        return redirect("/login")

    barcode = request.form.get("barcode", "").strip()

    if not barcode.isdigit() or not 8 <= len(barcode) <= 14:
        flash("Please enter a valid barcode number.", "error")
        return redirect(url_for("scan"))

    try:
        response = requests.get(
            f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json",
            params={"fields": "product_name,brands,categories"},
            headers={"User-Agent": "FoodSave/1.0"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 1:
            flash("Product not found. Please enter details manually.", "error")
            return redirect(url_for("scan"))

        item = data.get("product", {})
        name = item.get("product_name", "").strip()

        if not name:
            flash("Product name unavailable. Enter it manually.", "error")
            return redirect(url_for("scan"))

        product = {
            "barcode": barcode,
            "name": name,
            "brand": item.get("brands", ""),
            "category": item.get("categories", "")
        }

        return render_template("scan.html", product=product)

    except requests.RequestException:
        flash("Could not connect to the product database. Try again.", "error")
        return redirect(url_for("scan"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect(DB_PATH)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE,
                password TEXT
            )
        """)

        hashed_password = generate_password_hash(password)

        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/notifications")
def notifications():
    if "user_id" not in session:
        return redirect("/login")

    from datetime import date

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    foods = conn.execute(
        """
        SELECT *
        FROM food_items
        WHERE user_id = ?
        ORDER BY expiry_date ASC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    today = date.today()
    alerts = []

    for food in foods:
        if not food["expiry_date"]:
            continue

        expiry = date.fromisoformat(food["expiry_date"])
        days_left = (expiry - today).days

        if days_left < 0:
            alert_type = "Expired"
            message = f"{abs(days_left)} days overdue"

        elif days_left <= 3:
            alert_type = "Expiring Soon"
            message = f"{days_left} days left"

        else:
            continue

        alerts.append({
            "name": food["name"],
            "expiry_date": food["expiry_date"],
            "days_left": days_left,
            "type": alert_type,
            "message": message
        })

    return render_template(
        "notifications.html",
        alerts=alerts
    ) 



if __name__ == "__main__":
    update_database()
    app.run(debug=True)