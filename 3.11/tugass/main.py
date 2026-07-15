from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, select, case
from models import Customer, Order

from database import engine, get_db
from models import Base, Product
from schemas import ProductCreate, ProductResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@app.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product tidak ditemukan")

    return product


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int,
                   data: ProductCreate,
                   db: Session = Depends(get_db)):

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product tidak ditemukan")

    product.nama_produk = data.nama_produk
    product.kategori = data.kategori
    product.harga = data.harga

    db.commit()
    db.refresh(product)

    return product


@app.delete("/products/{product_id}")
def delete_product(product_id: int,
                   db: Session = Depends(get_db)):

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product tidak ditemukan")

    db.delete(product)
    db.commit()

    return {"message": "Product berhasil dihapus"}

@app.get("/reports/customer-total")
def customer_total(db: Session = Depends(get_db)):
    result = (
        db.query(
            Customer.nama,
            func.sum(Order.jumlah * Product.harga).label("total_belanja")
        )
        .join(Order, Customer.id == Order.customer_id)
        .join(Product, Product.id == Order.product_id)
        .group_by(Customer.id, Customer.nama)
        .order_by(func.sum(Order.jumlah * Product.harga).desc())
        .all()
    )

    return [
        {
            "nama": row.nama,
            "total_belanja": row.total_belanja
        }
        for row in result
    ]

@app.get("/reports/top-product-by-category")
def top_product_by_category(db: Session = Depends(get_db)):

    penjualan = (
        select(
            Product.kategori.label("kategori"),
            Product.nama_produk.label("nama_produk"),
            func.sum(Order.jumlah).label("total_terjual")
        )
        .join(Order, Product.id == Order.product_id)
        .group_by(Product.kategori, Product.nama_produk)
        .cte("penjualan")
    )

    max_penjualan = (
        select(
            penjualan.c.kategori,
            func.max(penjualan.c.total_terjual).label("maks")
        )
        .group_by(penjualan.c.kategori)
        .cte("max_penjualan")
    )

    result = db.execute(
        select(
            penjualan.c.kategori,
            penjualan.c.nama_produk,
            penjualan.c.total_terjual
        )
        .join(
            max_penjualan,
            (penjualan.c.kategori == max_penjualan.c.kategori) &
            (penjualan.c.total_terjual == max_penjualan.c.maks)
        )
    ).all()

    return [
        {
            "kategori": row.kategori,
            "nama_produk": row.nama_produk,
            "total_terjual": row.total_terjual
        }
        for row in result
    ]

@app.get("/reports/customer-level")
def customer_level(db: Session = Depends(get_db)):

    total_belanja = (
        select(
            Customer.nama.label("nama"),
            func.sum(Order.jumlah * Product.harga).label("total_belanja")
        )
        .join(Order, Customer.id == Order.customer_id)
        .join(Product, Product.id == Order.product_id)
        .group_by(Customer.id, Customer.nama)
        .cte("total_belanja")
    )

    result = db.execute(
        select(
            total_belanja.c.nama,
            total_belanja.c.total_belanja,
            case(
                (total_belanja.c.total_belanja > 5000000, "VIP"),
                (
                    (total_belanja.c.total_belanja >= 1000000) &
                    (total_belanja.c.total_belanja <= 5000000),
                    "Regular"
                ),
                else_="Basic"
            ).label("level_customer")
        )
    ).all()

    return [
        {
            "nama": row.nama,
            "total_belanja": row.total_belanja,
            "level_customer": row.level_customer
        }
        for row in result
    ]