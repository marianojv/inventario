from pydantic import BaseModel, Field
from typing import Optional
from .categoria import CategoriaMini

class ProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    precio_venta: float = Field(..., gt=0)
    stock: int = Field(0, ge=0)
    categoria_id: Optional[int]

class ProductoResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    precio_venta: float
    stock: int
    activo: bool
    categoria: CategoriaMini | None

    class Config:
        from_attributes = True
        
class ProductoMini(BaseModel):
    id: int
    nombre: str
    categoria: Optional[CategoriaMini] = None

    class Config:
        from_attributes = True
        