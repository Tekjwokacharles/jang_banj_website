from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from pathlib import Path
from functools import wraps
from datetime import datetime


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Local development:
#     instance/jang_banj.db
#
# Render production:
#     Set DB_PATH=/var/data/jang_banj.db
#
# This allows SQLite to remain the database while giving Render
# a persistent location when a persistent disk is attached.
default_db_path = BASE_DIR / "instance" / "jang_banj.db"

DB_PATH = Path(
    os.environ.get("DB_PATH", str(default_db_path))
)

app = Flask(__name__)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "temporary-development-key"
)


# ============================================================
# ADMIN CONFIGURATION
# ============================================================

APP_ENV = os.environ.get(
    "APP_ENV",
    "development"
).lower()

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD"
)

# For local development only, allow the old password if no
# environment variable has been configured yet.
#
# IMPORTANT:
# Before production deployment, ADMIN_PASSWORD MUST be set
# in Render Environment Variables.
if not ADMIN_PASSWORD:
    if APP_ENV == "production":
        raise RuntimeError(
            "ADMIN_PASSWORD environment variable is required "
            "when APP_ENV=production."
        )

    ADMIN_PASSWORD = "admin123"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    """
    Open a SQLite database connection.

    Locally:
        instance/jang_banj.db

    Render:
        /var/data/jang_banj.db
        when DB_PATH is configured to use the persistent disk.
    """

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    # Enable foreign key support.
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = get_db()

    try:

        # ====================================================
        # CREATE CATEGORIES TABLE
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                display_order INTEGER DEFAULT 0
            )
        """)

        # ====================================================
        # CREATE PRICE ITEMS TABLE
        # ====================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                price REAL,
                price_ssp REAL DEFAULT 0,
                price_usd REAL DEFAULT 0,
                unit TEXT DEFAULT '',
                display_order INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (category_id)
                    REFERENCES categories(id)
                    ON DELETE CASCADE
            )
        """)

        # ====================================================
        # DATABASE MIGRATION
        # ====================================================

        columns = conn.execute(
            "PRAGMA table_info(price_items)"
        ).fetchall()

        column_names = [
            column["name"]
            for column in columns
        ]

        # Add price_ssp if missing.
        if "price_ssp" not in column_names:

            conn.execute("""
                ALTER TABLE price_items
                ADD COLUMN price_ssp REAL DEFAULT 0
            """)

        # Add price_usd if missing.
        if "price_usd" not in column_names:

            conn.execute("""
                ALTER TABLE price_items
                ADD COLUMN price_usd REAL DEFAULT 0
            """)

        # Copy old price values into SSP.
        if "price" in column_names:

            conn.execute("""
                UPDATE price_items
                SET price_ssp = price
                WHERE price_ssp IS NULL
                   OR price_ssp = 0
            """)

        # ====================================================
        # INSERT DEFAULT CATEGORIES
        # ====================================================

        count = conn.execute(
            "SELECT COUNT(*) FROM categories"
        ).fetchone()[0]

        if count == 0:

            categories = [
                ("Site Works", 1),
                ("Foundations", 2),
                ("Columns", 3),
                ("Slabs", 4),
                ("Masonry", 5),
                ("Plastering & Painting", 6),
            ]

            conn.executemany(
                """
                INSERT INTO categories
                (
                    name,
                    display_order
                )
                VALUES (?, ?)
                """,
                categories
            )

            # =================================================
            # DEFAULT PRICE DATA
            # =================================================

            sample = [

                (
                    1,
                    "Site preparation / site works",
                    900000,
                    0,
                    "job",
                    1
                ),

                (
                    1,
                    "Total station / site surveying",
                    1800000,
                    0,
                    "job",
                    2
                ),

                (
                    2,
                    "Excavation per cubic meter",
                    70000,
                    0,
                    "m³",
                    1
                ),

                (
                    2,
                    "White sand per cubic meter",
                    50000,
                    0,
                    "m³",
                    2
                ),

                (
                    2,
                    "Reinforced foundation package",
                    1600000,
                    0,
                    "job",
                    3
                ),

                (
                    3,
                    "Short column",
                    550000,
                    0,
                    "column",
                    1
                ),

                (
                    3,
                    "Ground-floor column",
                    600000,
                    0,
                    "column",
                    2
                ),

                (
                    3,
                    "Rebar per meter",
                    90000,
                    0,
                    "m",
                    3
                ),

                (
                    4,
                    "Ground-floor slab per meter",
                    87000,
                    0,
                    "m²",
                    1
                ),

                (
                    4,
                    "Ground-floor slab with reinforcement",
                    95000,
                    0,
                    "m²",
                    2
                ),

                (
                    5,
                    "One brick wall per square meter",
                    30000,
                    0,
                    "m²",
                    1
                ),

                (
                    5,
                    "Half-brick wall per square meter",
                    40000,
                    0,
                    "m²",
                    2
                ),

                (
                    5,
                    "Two-brick wall per linear meter",
                    35000,
                    0,
                    "m",
                    3
                ),

                (
                    6,
                    "Interior plaster",
                    12000,
                    0,
                    "m²",
                    1
                ),

                (
                    6,
                    "Exterior plaster",
                    18000,
                    0,
                    "m²",
                    2
                ),

                (
                    6,
                    "Interior painting",
                    10000,
                    0,
                    "m²",
                    3
                ),

                (
                    6,
                    "Exterior painting",
                    15000,
                    0,
                    "m²",
                    4
                ),
            ]

            conn.executemany(
                """
                INSERT INTO price_items
                (
                    category_id,
                    description,
                    price,
                    price_ssp,
                    price_usd,
                    unit,
                    display_order,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        category_id,
                        description,
                        ssp,
                        ssp,
                        usd,
                        unit,
                        display_order,
                        datetime.now().strftime(
                            "%Y-%m-%d"
                        )
                    )
                    for (
                        category_id,
                        description,
                        ssp,
                        usd,
                        unit,
                        display_order
                    ) in sample
                ]
            )

        conn.commit()

    finally:
        conn.close()


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

def admin_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if not session.get("admin"):

            return redirect(
                url_for("admin_login")
            )

        return f(*args, **kwargs)

    return wrapper


# ============================================================
# GLOBAL TEMPLATE VARIABLES
# ============================================================

@app.context_processor
def inject_globals():

    return {
        "current_year": datetime.now().year
    }


# ============================================================
# HELPER FUNCTION - GET PROJECT IMAGES
# ============================================================

def get_project_images():

    image_folder = (
        Path(app.static_folder) / "images"
    )

    # Create the folder automatically if necessary.
    image_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif"
    }

    images = sorted(
        [
            image.name
            for image in image_folder.iterdir()
            if (
                image.is_file()
                and image.suffix.lower()
                in supported_extensions
            )
        ]
    )

    return images


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    conn = get_db()

    try:

        categories = conn.execute(
            """
            SELECT *
            FROM categories
            ORDER BY display_order, id
            """
        ).fetchall()

        grouped = []

        for cat in categories:

            items = conn.execute(
                """
                SELECT *
                FROM price_items
                WHERE category_id = ?
                ORDER BY display_order, id
                """,
                (cat["id"],)
            ).fetchall()

            grouped.append(
                (cat, items)
            )

    finally:
        conn.close()

    # Get all project images.
    all_images = get_project_images()

    # Show the first 12 on the home page.
    home_images = all_images[:12]

    return render_template(
        "home.html",
        grouped=grouped,
        images=home_images,
        total_images=len(all_images)
    )


# ============================================================
# PROJECT GALLERY
# ============================================================

@app.route("/gallery")
def gallery():

    images = get_project_images()

    return render_template(
        "gallery.html",
        images=images
    )


# ============================================================
# PRICES PAGE
# ============================================================

@app.route("/prices")
def prices():

    conn = get_db()

    try:

        categories = conn.execute(
            """
            SELECT *
            FROM categories
            ORDER BY display_order, id
            """
        ).fetchall()

        grouped = []

        for cat in categories:

            items = conn.execute(
                """
                SELECT *
                FROM price_items
                WHERE category_id = ?
                ORDER BY display_order, id
                """,
                (cat["id"],)
            ).fetchall()

            grouped.append(
                (cat, items)
            )

    finally:
        conn.close()

    return render_template(
        "prices.html",
        grouped=grouped,
        updated=datetime.now().strftime(
            "%d-%m-%Y"
        )
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect(
                url_for("admin_dashboard")
            )

        flash(
            "Invalid username or password.",
            "error"
        )

    return render_template(
        "admin_login.html"
    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    conn = get_db()

    try:

        categories = conn.execute(
            """
            SELECT *
            FROM categories
            ORDER BY display_order, id
            """
        ).fetchall()

        grouped = []

        for cat in categories:

            items = conn.execute(
                """
                SELECT *
                FROM price_items
                WHERE category_id = ?
                ORDER BY display_order, id
                """,
                (cat["id"],)
            ).fetchall()

            grouped.append(
                (cat, items)
            )

    finally:
        conn.close()

    return render_template(
        "admin_dashboard.html",
        grouped=grouped
    )


# ============================================================
# ADD PRICE
# ============================================================

@app.route(
    "/admin/price/add",
    methods=["POST"]
)
@admin_required
def add_price():

    try:

        category_id = request.form[
            "category_id"
        ]

        description = request.form[
            "description"
        ].strip()

        price_ssp = float(
            request.form.get(
                "price_ssp",
                0
            ) or 0
        )

        price_usd = float(
            request.form.get(
                "price_usd",
                0
            ) or 0
        )

        unit = request.form.get(
            "unit",
            ""
        ).strip()

    except (KeyError, ValueError):

        flash(
            "Please enter valid price information.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    conn = get_db()

    try:

        conn.execute(
            """
            INSERT INTO price_items
            (
                category_id,
                description,
                price,
                price_ssp,
                price_usd,
                unit,
                display_order,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                category_id,
                description,
                price_ssp,
                price_ssp,
                price_usd,
                unit,
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
            )
        )

        conn.commit()

    finally:
        conn.close()

    flash(
        "Price item added.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# EDIT PRICE
# ============================================================

@app.route(
    "/admin/price/<int:item_id>/edit",
    methods=["POST"]
)
@admin_required
def edit_price(item_id):

    try:

        description = request.form[
            "description"
        ].strip()

        price_ssp = float(
            request.form.get(
                "price_ssp",
                0
            ) or 0
        )

        price_usd = float(
            request.form.get(
                "price_usd",
                0
            ) or 0
        )

        unit = request.form.get(
            "unit",
            ""
        ).strip()

    except (KeyError, ValueError):

        flash(
            "Please enter valid price information.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    conn = get_db()

    try:

        conn.execute(
            """
            UPDATE price_items
            SET
                description = ?,
                price = ?,
                price_ssp = ?,
                price_usd = ?,
                unit = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                description,
                price_ssp,
                price_ssp,
                price_usd,
                unit,
                datetime.now().strftime(
                    "%Y-%m-%d"
                ),
                item_id
            )
        )

        conn.commit()

    finally:
        conn.close()

    flash(
        "Price updated.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# DELETE PRICE
# ============================================================

@app.route(
    "/admin/price/<int:item_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_price(item_id):

    conn = get_db()

    try:

        conn.execute(
            """
            DELETE FROM price_items
            WHERE id = ?
            """,
            (item_id,)
        )

        conn.commit()

    finally:
        conn.close()

    flash(
        "Price item deleted.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# ADD CATEGORY
# ============================================================

@app.route(
    "/admin/category/add",
    methods=["POST"]
)
@admin_required
def add_category():

    name = request.form.get(
        "name",
        ""
    ).strip()

    if not name:

        flash(
            "Category name is required.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    conn = get_db()

    try:

        conn.execute(
            """
            INSERT INTO categories
            (
                name,
                display_order
            )
            VALUES (?, 0)
            """,
            (name,)
        )

        conn.commit()

    finally:
        conn.close()

    flash(
        "Category added.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# INITIALIZE DATABASE
# ============================================================
#
# This runs when Flask starts directly and also when the
# application is imported by Gunicorn on Render.
#
# ============================================================

init_db()


# ============================================================
# START DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )