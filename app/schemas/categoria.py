from pydantic import BaseModel, Field


class CategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=1)


class CategoriaResponse(BaseModel):
    id: int
    nombre: str
    activa: bool

    class Config:
        from_attributes = True

class CategoriaMini(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True
        