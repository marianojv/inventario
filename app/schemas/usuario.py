from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str


class UsuarioResponse(BaseModel):
    id: int
    username: str
    nombre: str
    rol: str
    activo: bool

    class Config:
        from_attributes = True
        
class UsuarioCreate(BaseModel):
    username: str
    password: str
    rol: str        
    nombre: str