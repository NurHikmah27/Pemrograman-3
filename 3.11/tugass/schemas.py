from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    nama_produk: str
    kategori: str
    harga: float = Field(gt=0)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True