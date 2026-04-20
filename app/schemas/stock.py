from pydantic import BaseModel, Field

class IngresoStockCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)
    motivo: str | None = None