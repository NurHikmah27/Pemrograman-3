from database import SessionLocal, engine
from models import Base, Customer, Product, Order

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if db.query(Customer).count() == 0:

    c1 = Customer(
        nama="Andi",
        email="andi@gmail.com"
    )

    c2 = Customer(
        nama="Budi",
        email="budi@gmail.com"
    )

    db.add_all([c1, c2])
    db.commit()

if db.query(Product).count() == 0:

    p1 = Product(
        nama_produk="Laptop",
        kategori="Elektronik",
        harga=7000000
    )

    p2 = Product(
        nama_produk="Mouse",
        kategori="Elektronik",
        harga=150000
    )

    p3 = Product(
        nama_produk="Meja",
        kategori="Furniture",
        harga=800000
    )

    db.add_all([p1, p2, p3])
    db.commit()

if db.query(Order).count() == 0:

    o1 = Order(
        customer_id=1,
        product_id=1,
        jumlah=1
    )

    o2 = Order(
        customer_id=1,
        product_id=2,
        jumlah=2
    )

    o3 = Order(
        customer_id=2,
        product_id=3,
        jumlah=3
    )

    db.add_all([o1, o2, o3])
    db.commit()

db.close()

print("Database berhasil diisi.")