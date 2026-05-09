from sqlalchemy import Column, Integer, String, Float, Boolean
from .database import Base
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import String
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    precio_venta = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    categoria = relationship("Categoria", back_populates="productos")
    eliminado = Column(Boolean, default=False)
    
class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    total = Column(Float, nullable=False)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    cliente = relationship("Cliente")

    detalles = relationship("DetalleVenta", back_populates="venta")    


class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"

    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    producto = relationship("Producto")

    venta = relationship("Venta", back_populates="detalles")


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    activa = Column(Boolean, default=True)
    eliminado = Column(Boolean, default=False) 
    productos = relationship("Producto", back_populates="categoria")


class MovimientoStock(Base):
    __tablename__ = "movimientos_stock"

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    tipo = Column(String, nullable=False)  # INGRESO / EGRESO
    cantidad = Column(Integer, nullable=False)
    motivo = Column(String, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)

    producto = relationship("Producto")



class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)

    # Código de negocio: 200xxx / 300xxx
    codigo_cliente = Column(String, unique=True, index=True, nullable=False)

    # EMPRESA | PERSONA
    tipo_cliente = Column(String, nullable=False)

    # Común
    nombre_razon_social = Column(String, nullable=False)
    telefono = Column(String, nullable=True)

    # Dirección
    calle = Column(String, nullable=True)
    numero = Column(String, nullable=True)
    localidad = Column(String, nullable=True)
    codigo_postal = Column(String, nullable=True)

    # Empresa
    codigo_fiscal = Column(String, nullable=True)

    # Persona Física
    dni = Column(String, nullable=True)

    activo = Column(Boolean, default=True) 
    eliminado = Column(Boolean, default=False)
    
    
class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True, index=True)

    max_precio_producto = Column(Float, nullable=False)
    max_stock_producto = Column(Integer, nullable=False)
    
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    
    nombre = Column(String)

    rol = Column(String, default="USER")  # "ADMIN" o "USER"
    activo = Column(Boolean, default=True)    