
from flask import Flask, request, jsonify, send_from_directory, session
import sqlite3
import os
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# APP CONFIG
# ==========================================

app = Flask(__name__)

app.secret_key = "OGONG-HARDWARE-SECRET-2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE = os.path.join(DATABASE_DIR, "ogong.db")


# Make sure database folder exists
os.makedirs(DATABASE_DIR, exist_ok=True)


# ==========================================
# DATABASE
# ==========================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Ensure database tables and initial records exist."""
    conn = get_db()
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cur.fetchone():
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'cashier' CHECK(role IN ('admin', 'cashier')),
                    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact_person TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    price REAL NOT NULL DEFAULT 0.00,
                    cost_price REAL NOT NULL DEFAULT 0.00,
                    stock INTEGER NOT NULL DEFAULT 0,
                    minimum_stock INTEGER NOT NULL DEFAULT 10,
                    supplier_id INTEGER NULL REFERENCES suppliers(id) ON DELETE SET NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_no TEXT NOT NULL UNIQUE,
                    customer_id INTEGER NULL REFERENCES customers(id) ON DELETE SET NULL,
                    cashier_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
                    subtotal REAL NOT NULL DEFAULT 0.00,
                    discount REAL NOT NULL DEFAULT 0.00,
                    total REAL NOT NULL DEFAULT 0.00,
                    cash_received REAL NOT NULL DEFAULT 0.00,
                    change_amount REAL NOT NULL DEFAULT 0.00,
                    payment_method TEXT NOT NULL DEFAULT 'Cash',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    subtotal REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    reference TEXT,
                    user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_products_supplier ON products (supplier_id);
                CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
                CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales (customer_id);
                CREATE INDEX IF NOT EXISTS idx_sales_cashier ON sales (cashier_id);
                CREATE INDEX IF NOT EXISTS idx_sales_date ON sales (created_at);
                CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items (sale_id);
                CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items (product_id);
                CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements (product_id);
                CREATE INDEX IF NOT EXISTS idx_stock_movements_user ON stock_movements (user_id);
                CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements (created_at);
            """)
            conn.commit()

            seed_file = os.path.join(DATABASE_DIR, "ogong_seed.sql")
            if os.path.exists(seed_file):
                with open(seed_file, "r", encoding="utf-8") as f:
                    seed_content = f.read()
                clean_lines = [
                    l for l in seed_content.splitlines()
                    if not l.strip().startswith("USE ") and not l.strip().startswith("--")
                ]
                conn.executescript("\n".join(clean_lines))
                conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        conn.close()

init_db()


def migrate_product_delete_constraints():
    """Allow deleting products without leaving orphaned sales or stock records."""
    conn = get_db()

    try:
        for table_name, create_sql in {
            "sale_items": """
                CREATE TABLE sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    subtotal REAL NOT NULL
                )
            """,
            "stock_movements": """
                CREATE TABLE stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    reference TEXT,
                    user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
        }.items():
            schema = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table_name,)
            ).fetchone()

            if schema and "ON DELETE CASCADE" in schema["sql"]:
                continue

            conn.execute("PRAGMA foreign_keys = OFF")
            old_table = f"{table_name}_old"
            conn.execute(f"ALTER TABLE {table_name} RENAME TO {old_table}")
            conn.execute(create_sql)

            if table_name == "sale_items":
                conn.execute("""
                    INSERT INTO sale_items (id, sale_id, product_id, quantity, price, subtotal)
                    SELECT id, sale_id, product_id, quantity, price, subtotal
                    FROM sale_items_old
                """)
            else:
                conn.execute("""
                    INSERT INTO stock_movements (id, product_id, type, quantity, reference, user_id, created_at)
                    SELECT id, product_id, type, quantity, reference, user_id, created_at
                    FROM stock_movements_old
                """)

            conn.execute(f"DROP TABLE {old_table}")
            conn.execute("PRAGMA foreign_keys = ON")

            if table_name == "sale_items":
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items (sale_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items (product_id)")
            else:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements (product_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_user ON stock_movements (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements (created_at)")

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Product delete migration error: {e}")
    finally:
        conn.close()


migrate_product_delete_constraints()


def query(sql, params=(), one=False):
    conn = get_db()

    try:
        cursor = conn.execute(sql, params)

        if one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()

        conn.commit()
        return result

    finally:
        conn.close()


# ==========================================
# HELPERS
# ==========================================

def get_json():
    return request.get_json(silent=True) or {}


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "Login required"
            }), 401

        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "Login required"
            }), 401

        if session.get("role") != "admin":
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403

        return func(*args, **kwargs)

    return wrapper


# ==========================================
# FRONTEND
# ==========================================

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "login.html")


@app.route("/<path:filename>")
def files(filename):
    return send_from_directory(BASE_DIR, filename)


# ==========================================
# LOGIN
# ==========================================

@app.post("/api/login")
def login():

    data = get_json()

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    user = query("""
        SELECT
            id,
            username,
            password,
            full_name,
            role,
            status
        FROM users
        WHERE username = ?
    """, (username,), one=True)

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid username or password"
        }), 401

    if user["status"] != "active":
        return jsonify({
            "success": False,
            "message": "Account is inactive"
        }), 403

    stored_password = user["password"]

    # Supports both hashed passwords and old plain-text passwords
    password_valid = False

    if stored_password == password:
        password_valid = True
    else:
        try:
            password_valid = check_password_hash(
                stored_password,
                password
            )
        except Exception:
            password_valid = False

    if not password_valid:
        return jsonify({
            "success": False,
            "message": "Invalid username or password"
        }), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "status": user["status"]
        }
    })


@app.post("/api/logout")
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out"
    })


@app.get("/api/current-user")
def current_user():

    if "user_id" not in session:
        return jsonify({
            "logged_in": False
        })

    return jsonify({
        "logged_in": True,
        "id": session["user_id"],
        "username": session["username"],
        "role": session["role"]
    })


# ==========================================
# PRODUCTS
# ==========================================

@app.get("/api/products")
@login_required
def get_products():

    products = query("""
        SELECT
            p.*,
            s.name AS supplier_name
        FROM products p
        LEFT JOIN suppliers s
            ON p.supplier_id = s.id
        ORDER BY p.id DESC
    """)

    return jsonify([
        dict(product)
        for product in products
    ])


@app.post("/api/products")
@admin_required
def add_product():

    data = get_json()

    required = [
        "sku",
        "name",
        "category",
        "unit",
        "price"
    ]

    for field in required:
        if field not in data:
            return jsonify({
                "success": False,
                "message": f"{field} is required"
            }), 400

    try:

        price = float(data["price"])
        cost_price = float(data.get("cost_price", 0))
        stock = int(data.get("stock", 0))
        minimum_stock = int(data.get("minimum_stock", 10))

        if price < 0 or cost_price < 0:
            raise ValueError()

        if stock < 0 or minimum_stock < 0:
            raise ValueError()

        conn = get_db()

        try:

            cursor = conn.execute("""
                INSERT INTO products
                (
                    sku,
                    name,
                    category,
                    unit,
                    price,
                    cost_price,
                    stock,
                    minimum_stock,
                    supplier_id
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["sku"],
                data["name"],
                data["category"],
                data["unit"],
                price,
                cost_price,
                stock,
                minimum_stock,
                data.get("supplier_id")
            ))

            conn.commit()

            return jsonify({
                "success": True,
                "message": "Product added",
                "id": cursor.lastrowid
            })

        except sqlite3.IntegrityError:
            conn.rollback()

            return jsonify({
                "success": False,
                "message": "SKU already exists"
            }), 400

        finally:
            conn.close()

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid product values"
        }), 400


@app.put("/api/products/<int:product_id>")
@admin_required
def update_product(product_id):

    data = get_json()

    required = [
        "sku",
        "name",
        "category",
        "unit",
        "price"
    ]

    for field in required:
        if field not in data:
            return jsonify({
                "success": False,
                "message": f"{field} is required"
            }), 400

    try:

        price = float(data["price"])
        cost_price = float(data.get("cost_price", 0))
        minimum_stock = int(data.get("minimum_stock", 10))

        if price < 0:
            raise ValueError()

        if cost_price < 0:
            raise ValueError()

        if minimum_stock < 0:
            raise ValueError()

        conn = get_db()

        try:

            cursor = conn.execute("""
                UPDATE products
                SET
                    sku = ?,
                    name = ?,
                    category = ?,
                    unit = ?,
                    price = ?,
                    cost_price = ?,
                    minimum_stock = ?,
                    supplier_id = ?
                WHERE id = ?
            """, (
                data["sku"],
                data["name"],
                data["category"],
                data["unit"],
                price,
                cost_price,
                minimum_stock,
                data.get("supplier_id"),
                product_id
            ))

            conn.commit()

            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "message": "Product not found"
                }), 404

            return jsonify({
                "success": True,
                "message": "Product updated"
            })

        except sqlite3.IntegrityError:
            conn.rollback()

            return jsonify({
                "success": False,
                "message": "SKU already exists"
            }), 400

        finally:
            conn.close()

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid product values"
        }), 400


@app.delete("/api/products/<int:product_id>")
@admin_required
def delete_product(product_id):

    conn = get_db()

    try:

        cursor = conn.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Product not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Product deleted"
        })

    except sqlite3.IntegrityError:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": "Cannot delete this product because it is already used"
        }), 400

    finally:
        conn.close()


# ==========================================
# INVENTORY / STOCK
# ==========================================

@app.post("/api/inventory/stock-in")
@login_required
def stock_in():

    data = get_json()

    try:
        product_id = int(data["product_id"])
        quantity = int(data["quantity"])

    except (KeyError, ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid product or quantity"
        }), 400

    if quantity <= 0:
        return jsonify({
            "success": False,
            "message": "Quantity must be greater than zero"
        }), 400

    conn = get_db()

    try:

        product = conn.execute("""
            SELECT id, name
            FROM products
            WHERE id = ?
        """, (product_id,)).fetchone()

        if not product:
            return jsonify({
                "success": False,
                "message": "Product not found"
            }), 404

        conn.execute("""
            UPDATE products
            SET stock = stock + ?
            WHERE id = ?
        """, (
            quantity,
            product_id
        ))

        conn.execute("""
            INSERT INTO stock_movements
            (
                product_id,
                type,
                quantity,
                reference,
                user_id
            )

            VALUES (?, 'STOCK-IN', ?, ?, ?)
        """, (
            product_id,
            quantity,
            data.get("reference", "Manual Stock In"),
            session.get("user_id")
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Stock added"
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    finally:
        conn.close()


@app.post("/api/inventory/stock-out")
@login_required
def stock_out():

    data = get_json()

    try:
        product_id = int(data["product_id"])
        quantity = int(data["quantity"])

    except (KeyError, ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid product or quantity"
        }), 400

    if quantity <= 0:
        return jsonify({
            "success": False,
            "message": "Quantity must be greater than zero"
        }), 400

    conn = get_db()

    try:

        product = conn.execute("""
            SELECT
                id,
                name,
                stock
            FROM products
            WHERE id = ?
        """, (product_id,)).fetchone()

        if not product:
            return jsonify({
                "success": False,
                "message": "Product not found"
            }), 404

        if product["stock"] < quantity:
            return jsonify({
                "success": False,
                "message": "Insufficient stock"
            }), 400

        conn.execute("""
            UPDATE products
            SET stock = stock - ?
            WHERE id = ?
        """, (
            quantity,
            product_id
        ))

        conn.execute("""
            INSERT INTO stock_movements
            (
                product_id,
                type,
                quantity,
                reference,
                user_id
            )

            VALUES (?, 'STOCK-OUT', ?, ?, ?)
        """, (
            product_id,
            quantity,
            data.get("reference", "Manual Stock Out"),
            session.get("user_id")
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Stock removed"
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    finally:
        conn.close()


@app.get("/api/inventory/movements")
@login_required
def stock_movements():

    rows = query("""
        SELECT
            sm.*,
            p.name AS product_name,
            p.sku
        FROM stock_movements sm
        JOIN products p
            ON sm.product_id = p.id
        ORDER BY sm.id DESC
    """)

    return jsonify([
        dict(row)
        for row in rows
    ])


# ==========================================
# SUPPLIERS
# ==========================================

@app.get("/api/suppliers")
@login_required
def get_suppliers():

    rows = query("""
        SELECT *
        FROM suppliers
        ORDER BY id DESC
    """)

    return jsonify([
        dict(row)
        for row in rows
    ])


@app.post("/api/suppliers")
@admin_required
def add_supplier():

    data = get_json()

    if not data.get("name"):
        return jsonify({
            "success": False,
            "message": "Supplier name is required"
        }), 400

    try:

        query("""
            INSERT INTO suppliers
            (
                name,
                contact_person,
                phone,
                email,
                address
            )

            VALUES (?, ?, ?, ?, ?)
        """, (
            data["name"],
            data.get("contact_person"),
            data.get("phone"),
            data.get("email"),
            data.get("address")
        ))

        return jsonify({
            "success": True,
            "message": "Supplier added"
        })

    except sqlite3.IntegrityError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400


@app.delete("/api/suppliers/<int:supplier_id>")
@admin_required
def delete_supplier(supplier_id):

    try:

        query(
            "DELETE FROM suppliers WHERE id = ?",
            (supplier_id,)
        )

        return jsonify({
            "success": True,
            "message": "Supplier deleted"
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Cannot delete supplier because it is being used"
        }), 400


# ==========================================
# CUSTOMERS
# ==========================================

@app.get("/api/customers")
@login_required
def get_customers():

    rows = query("""
        SELECT *
        FROM customers
        ORDER BY id DESC
    """)

    return jsonify([
        dict(row)
        for row in rows
    ])


@app.post("/api/customers")
@login_required
def add_customer():

    data = get_json()

    if not data.get("name"):
        return jsonify({
            "success": False,
            "message": "Customer name is required"
        }), 400

    try:

        query("""
            INSERT INTO customers
            (
                name,
                phone,
                email,
                address
            )

            VALUES (?, ?, ?, ?)
        """, (
            data["name"],
            data.get("phone"),
            data.get("email"),
            data.get("address")
        ))

        return jsonify({
            "success": True,
            "message": "Customer added"
        })

    except sqlite3.IntegrityError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400


# ==========================================
# USERS
# ==========================================

@app.get("/api/users")
@admin_required
def get_users():

    rows = query("""
        SELECT
            id,
            username,
            full_name,
            role,
            status,
            created_at
        FROM users
        ORDER BY id DESC
    """)

    return jsonify([
        dict(row)
        for row in rows
    ])


@app.post("/api/users")
@admin_required
def add_user():

    data = get_json()

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    full_name = str(data.get("full_name", "")).strip()
    role = data.get("role", "cashier")

    if not username or not password or not full_name:
        return jsonify({
            "success": False,
            "message": "Username, password and full name are required"
        }), 400

    if role not in ["admin", "cashier"]:
        return jsonify({
            "success": False,
            "message": "Invalid role"
        }), 400

    password_hash = generate_password_hash(password)

    try:

        query("""
            INSERT INTO users
            (
                username,
                password,
                full_name,
                role,
                status
            )

            VALUES (?, ?, ?, ?, 'active')
        """, (
            username,
            password_hash,
            full_name,
            role
        ))

        return jsonify({
            "success": True,
            "message": "User added"
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Username already exists"
        }), 400


# ==========================================
# CASHIER / SALES
# ==========================================

@app.post("/api/sales")
@login_required
def create_sale():

    data = get_json()

    items = data.get("items", [])

    if not isinstance(items, list) or len(items) == 0:
        return jsonify({
            "success": False,
            "message": "Sale must contain at least one item"
        }), 400

    try:

        discount = float(data.get("discount", 0))
        cash = float(data.get("cash_received", 0))

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid discount or cash amount"
        }), 400

    if discount < 0:
        return jsonify({
            "success": False,
            "message": "Invalid discount"
        }), 400

    conn = get_db()

    try:

        subtotal = 0
        checked_items = []

        # ----------------------------------
        # CHECK STOCK
        # ----------------------------------

        for item in items:

            try:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])

            except (KeyError, ValueError, TypeError):

                raise Exception(
                    "Invalid product or quantity"
                )

            if quantity <= 0:
                raise Exception(
                    "Quantity must be greater than zero"
                )

            product = conn.execute("""
                SELECT *
                FROM products
                WHERE id = ?
            """, (
                product_id,
            )).fetchone()

            if not product:
                raise Exception(
                    "Product not found"
                )

            if product["stock"] < quantity:
                raise Exception(
                    f"Insufficient stock for {product['name']}"
                )

            item_subtotal = (
                float(product["price"]) *
                quantity
            )

            subtotal += item_subtotal

            checked_items.append({
                "product": product,
                "product_id": product_id,
                "quantity": quantity,
                "subtotal": item_subtotal
            })

        # ----------------------------------
        # TOTAL
        # ----------------------------------

        if discount > subtotal:
            raise Exception(
                "Discount cannot be greater than subtotal"
            )

        total = subtotal - discount

        if cash < total:
            raise Exception(
                "Insufficient cash received"
            )

        change = cash - total

        # ----------------------------------
        # RECEIPT NUMBER
        # ----------------------------------

        receipt_no = (
            "OG-" +
            datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            )
        )

        # ----------------------------------
        # SALE
        # ----------------------------------

        cursor = conn.execute("""
            INSERT INTO sales
            (
                receipt_no,
                customer_id,
                cashier_id,
                subtotal,
                discount,
                total,
                cash_received,
                change_amount,
                payment_method
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            receipt_no,
            data.get("customer_id"),
            session.get("user_id"),
            subtotal,
            discount,
            total,
            cash,
            change,
            data.get("payment_method", "Cash")
        ))

        sale_id = cursor.lastrowid

        # ----------------------------------
        # SALE ITEMS + STOCK
        # ----------------------------------

        for item in checked_items:

            product = item["product"]
            product_id = item["product_id"]
            quantity = item["quantity"]
            item_subtotal = item["subtotal"]

            conn.execute("""
                INSERT INTO sale_items
                (
                    sale_id,
                    product_id,
                    quantity,
                    price,
                    subtotal
                )

                VALUES (?, ?, ?, ?, ?)
            """, (
                sale_id,
                product_id,
                quantity,
                product["price"],
                item_subtotal
            ))

            conn.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """, (
                quantity,
                product_id
            ))

            conn.execute("""
                INSERT INTO stock_movements
                (
                    product_id,
                    type,
                    quantity,
                    reference,
                    user_id
                )

                VALUES (?, 'SALE', ?, ?, ?)
            """, (
                product_id,
                quantity,
                receipt_no,
                session.get("user_id")
            ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Sale completed",
            "sale_id": sale_id,
            "receipt_no": receipt_no,
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "cash": cash,
            "change": change
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    finally:
        conn.close()


# ==========================================
# SALES HISTORY
# ==========================================

@app.get("/api/sales")
@login_required
def get_sales():

    rows = query("""
        SELECT
            s.*,
            u.full_name AS cashier,
            c.name AS customer
        FROM sales s
        LEFT JOIN users u
            ON s.cashier_id = u.id
        LEFT JOIN customers c
            ON s.customer_id = c.id
        ORDER BY s.id DESC
    """)

    return jsonify([
        dict(row)
        for row in rows
    ])


# ==========================================
# DASHBOARD
# ==========================================

@app.get("/api/dashboard")
@login_required
def dashboard():

    products = query("""
        SELECT COUNT(*) AS total
        FROM products
    """, one=True)

    stock = query("""
        SELECT COALESCE(
            SUM(stock),
            0
        ) AS total
        FROM products
    """, one=True)

    value = query("""
        SELECT COALESCE(
            SUM(stock * price),
            0
        ) AS total
        FROM products
    """, one=True)

    low_stock = query("""
        SELECT COUNT(*) AS total
        FROM products
        WHERE stock <= minimum_stock
    """, one=True)

    sales = query("""
        SELECT COALESCE(
            SUM(total),
            0
        ) AS total
        FROM sales
        WHERE DATE(created_at) = DATE('now', 'localtime')
    """, one=True)

    return jsonify({

        "total_products":
            products["total"],

        "total_stock":
            stock["total"],

        "inventory_value":
            value["total"],

        "low_stock":
            low_stock["total"],

        "today_sales":
            sales["total"]

    })


# ==========================================
# SALES REPORT
# ==========================================

@app.get("/api/reports/sales")
@login_required
def sales_report():

    rows = query("""
        SELECT
            DATE(created_at) AS date,
            COUNT(*) AS transactions,
            COALESCE(SUM(total), 0) AS sales
        FROM sales
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """)

    return jsonify([
        dict(row)
        for row in rows
    ])


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(error):

    if request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "message": "API endpoint not found"
        }), 404

    return "Page not found", 404


@app.errorhandler(500)
def server_error(error):

    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    print("------------------------------------------")
    print("OGONG HARDWARE SYSTEM")
    print("------------------------------------------")
    print(f"Database: {DATABASE}")
    print("Server: http://127.0.0.1:5000")
    print("------------------------------------------")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
