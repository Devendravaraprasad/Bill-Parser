import sqlite3
import os

# Path to SQLite database
DB_PATH = os.path.join("data", "receipts.db")

# --- Helper functions ---

def safe_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0

def normalize_str(value):
    return value.strip() if isinstance(value, str) and value.strip() else "NA"

# --- Initialize SQLite database ---

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            invoice_date TEXT,
            vendor_name TEXT,
            subtotal_amount REAL,
            tax_amount REAL,
            total_amount REAL,
            payment_method TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- Insert a single receipt dict ---

def insert_receipt(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO receipts (
            invoice_number, invoice_date, vendor_name,
            subtotal_amount, tax_amount, total_amount, payment_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        normalize_str(data.get("invoice_number")),
        normalize_str(data.get("invoice_date")),
        normalize_str(data.get("vendor_name")),
        safe_float(data.get("subtotal_amount")),
        safe_float(data.get("tax_amount")),
        safe_float(data.get("total_amount")),
        normalize_str(data.get("payment_method")),
    ))
    conn.commit()
    conn.close()

# --- Fetch all records ---

def fetch_all_receipts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM receipts")
    rows = c.fetchall()
    conn.close()
    return rows
