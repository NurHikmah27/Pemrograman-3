from fastapi import FastAPI
from pydantic import BaseModel

# Membuat aplikasi FastAPI
app = FastAPI()

# =====================================
# Soal 1 - Endpoint Sederhana
# =====================================
@app.get("/")
def home():
    return {
        "message": "Hello FastAPI"
    }

# =====================================
# Soal 2 - Path Parameter
# =====================================
@app.get("/students/{student_id}")
def get_student(student_id: int):
    return {
        "student_id": student_id
    }

# =====================================
# Soal 3 - Query Parameter
# =====================================
@app.get("/search")
def search(keyword: str, limit: int = 10):
    return {
        "keyword": keyword,
        "limit": limit
    }

# =====================================
# Soal 4 - Request Body dengan Pydantic
# =====================================
class Book(BaseModel):
    title: str
    author: str
    price: int

@app.post("/books")
def create_book(book: Book):
    return {
        "message": "Book created successfully",
        "data": book
    }