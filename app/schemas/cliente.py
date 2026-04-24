from pydantic import BaseModel, Field
from typing import Optional, Literal

TipoCliente = Literal["EMPRESA", "PERSONA"]

class ClienteCreate(BaseModel):
    # Tipo
    tipo_cliente: TipoCliente

    # Común
    nombre_razon_social: str = Field(..., min_length=1)
    telefono: Optional[str] = None

    # Dirección
    calle: Optional[str] = None
    numero: Optional[str] = None
    localidad: Optional[str] = None
    codigo_postal: Optional[str] = None

    # Empresa
    codigo_fiscal: Optional[str] = None

    # Persona física
    dni: Optional[str] = None


class ClienteResponse(BaseModel):
    id: int                   # técnico
    codigo_cliente: str        # negocio
    tipo_cliente: str
    nombre_razon_social: str
    telefono: Optional[str]

    calle: Optional[str]
    numero: Optional[str]
    localidad: Optional[str]
    codigo_postal: Optional[str]

    codigo_fiscal: Optional[str]
    dni: Optional[str]

    activo: bool

    class Config:
        from_attributes = True