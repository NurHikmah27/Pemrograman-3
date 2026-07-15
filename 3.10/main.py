from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Online Store API")

DATABASE = "store.db"

# =========================
# Koneksi Database
# =========================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# Membuat Tabel
# =========================
def create_tables():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_produk TEXT,
        kategori TEXT,
        harga INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        product_id INTEGER,
        jumlah INTEGER,
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    conn.commit()

    # Data contoh Customer
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO customers(nama,email)
        VALUES(?,?)
        """,[
            ("Andi","andi@gmail.com"),
            ("Budi","budi@gmail.com"),
            ("Citra","citra@gmail.com")
        ])

    # Data contoh Product
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO products(nama_produk,kategori,harga)
        VALUES(?,?,?)
        """,[
            ("Laptop","Elektronik",8000000),
            ("Mouse","Elektronik",250000),
            ("Meja","Furniture",1500000),
            ("Kursi","Furniture",900000)
        ])

    # Data contoh Order
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO orders(customer_id,product_id,jumlah)
        VALUES(?,?,?)
        """,[
            (1,1,1),
            (1,2,2),
            (2,3,2),
            (2,4,1),
            (3,2,5)
        ])

    conn.commit()
    conn.close()

create_tables()

# =========================
# Pydantic
# =========================
class Product(BaseModel):
    nama_produk:str
    kategori:str
    harga:int

class ProductResponse(Product):
    id:int

# =========================
# CRUD PRODUCTS
# =========================

@app.post("/products",response_model=ProductResponse)
def create_product(product:Product):

    conn=get_db()
    cur=conn.cursor()

    cur.execute("""
    INSERT INTO products(nama_produk,kategori,harga)
    VALUES(?,?,?)
    """,
    (product.nama_produk,
     product.kategori,
     product.harga))

    conn.commit()

    new_id=cur.lastrowid

    conn.close()

    return {"id":new_id,**product.dict()}


@app.get("/products",response_model=list[ProductResponse])
def get_products():

    conn=get_db()

    data=conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    conn.close()

    return [dict(i) for i in data]


@app.get("/products/{product_id}",response_model=ProductResponse)
def get_product(product_id:int):

    conn=get_db()

    data=conn.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    conn.close()

    if data is None:
        raise HTTPException(status_code=404,
        detail="Product tidak ditemukan")

    return dict(data)


@app.put("/products/{product_id}",
response_model=ProductResponse)
def update_product(product_id:int,
product:Product):

    conn=get_db()
    cur=conn.cursor()

    cur.execute("""
    UPDATE products
    SET nama_produk=?,
        kategori=?,
        harga=?
    WHERE id=?
    """,
    (
    product.nama_produk,
    product.kategori,
    product.harga,
    product_id
    ))

    conn.commit()

    if cur.rowcount==0:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Product tidak ditemukan"
        )

    conn.close()

    return {"id":product_id,**product.dict()}


@app.delete("/products/{product_id}")
def delete_product(product_id:int):

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
        "DELETE FROM products WHERE id=?",
        (product_id,)
    )

    conn.commit()

    if cur.rowcount==0:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Product tidak ditemukan"
        )

    conn.close()

    return {"message":"Product berhasil dihapus"}

# =========================
# REPORT 1
# JOIN + SUM
# =========================

@app.get("/reports/customer-total")
def customer_total():

    conn=get_db()

    query="""
    SELECT
    c.nama,
    SUM(p.harga*o.jumlah) total_belanja

    FROM customers c

    JOIN orders o
    ON c.id=o.customer_id

    JOIN products p
    ON p.id=o.product_id

    GROUP BY c.id

    ORDER BY total_belanja DESC
    """

    data=conn.execute(query).fetchall()

    conn.close()

    return [dict(i) for i in data]

# =========================
# REPORT 2
# SUBQUERY
# =========================

@app.get("/reports/customer-above-average")
def above_average():

    conn=get_db()

    query="""
    SELECT *
    FROM(
        SELECT
        c.nama,
        SUM(p.harga*o.jumlah)
        total_belanja

        FROM customers c

        JOIN orders o
        ON c.id=o.customer_id

        JOIN products p
        ON p.id=o.product_id

        GROUP BY c.id
    )

    WHERE total_belanja>

    (
        SELECT AVG(total_belanja)
        FROM(
            SELECT
            SUM(p.harga*o.jumlah)
            total_belanja

            FROM customers c

            JOIN orders o
            ON c.id=o.customer_id

            JOIN products p
            ON p.id=o.product_id

            GROUP BY c.id
        )
    )
    """

    data=conn.execute(query).fetchall()

    conn.close()

    return [dict(i) for i in data]

# =========================
# REPORT 3
# CTE
# =========================

@app.get("/reports/top-product-by-category")
def top_product():

    conn=get_db()

    query="""
    WITH sales AS(

        SELECT

        p.kategori,
        p.nama_produk,
        SUM(o.jumlah)
        total_terjual

        FROM products p

        JOIN orders o
        ON p.id=o.product_id

        GROUP BY p.id

    )

    SELECT *

    FROM sales s

    WHERE total_terjual=

    (
        SELECT
        MAX(total_terjual)

        FROM sales

        WHERE kategori=s.kategori
    )
    """

    data=conn.execute(query).fetchall()

    conn.close()

    return [dict(i) for i in data]

# =========================
# REPORT 4
# CASE + CTE
# =========================

@app.get("/reports/customer-level")
def customer_level():

    conn=get_db()

    query="""
    WITH total AS(

        SELECT

        c.nama,

        SUM(p.harga*o.jumlah)
        total_belanja

        FROM customers c

        JOIN orders o
        ON c.id=o.customer_id

        JOIN products p
        ON p.id=o.product_id

        GROUP BY c.id

    )

    SELECT

    nama,
    total_belanja,

    CASE

        WHEN total_belanja>5000000
        THEN 'VIP'

        WHEN total_belanja>=1000000
        THEN 'Regular'

        ELSE 'Basic'

    END level_customer

    FROM total
    """

    data=conn.execute(query).fetchall()

    conn.close()

    return [dict(i) for i in data]