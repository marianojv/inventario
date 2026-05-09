from pydantic import BaseModel, Field

class ConfiguracionResponse(BaseModel):
    max_precio_producto: float
    max_stock_producto: int

    class Config:
        from_attributes = True


class ConfiguracionUpdate(BaseModel):
    max_precio_producto: float = Field(gt=0)
    max_stock_producto: int = Field(gt=0)