from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from .models import Producto
from .schemas.producto import ProductoCreate, ProductoResponse

from .models import Venta, DetalleVenta
from .schemas.venta import VentaCreate
from .schemas.venta import VentaResponse

from .models import Categoria
from .schemas.categoria import CategoriaCreate, CategoriaResponse

from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from .models import MovimientoStock
from .schemas.stock import IngresoStockCreate

from sqlalchemy import or_

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import Depends

from sqlalchemy import func, or_
from fastapi import HTTPException

from .models import Cliente
from .schemas.cliente import ClienteCreate, ClienteResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import Venta

from .models import Configuracion
from .schemas.configuracion import (
    ConfiguracionResponse,
    ConfiguracionUpdate )

from .schemas.producto import (
    ProductoCreate,
    ProductoUpdate,
    ProductoResponse
)

from sqlalchemy.orm import Session
from fastapi import Depends

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas.categoria import CategoriaUpdate

from .schemas.cliente import ClienteUpdate

from .models import Usuario
from .schemas.usuario import LoginRequest, UsuarioResponse

from fastapi import Header

from .schemas.usuario import UsuarioCreate

from fastapi import Depends

import bcrypt

import os
from fastapi.staticfiles import StaticFiles


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def get_current_user(
    user_id: int = Header(None, alias="x-user-id"),
    rol: str = Header(None, alias="x-user-rol")
):
    if not user_id or not rol:
        raise HTTPException(status_code=401, detail="No autenticado")

    return {
        "id": user_id,
        "rol": rol
    }


def require_admin(user = Depends(get_current_user)):
    if user["rol"] != "ADMIN":
        raise HTTPException(status_code=403, detail="No autorizado")

    return user

#app = FastAPI()   # ✅ primero se crea
app = FastAPI(title="Sistema de Stock y Ventas")

# ✅ luego se usa
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

#app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

PERMISOS = {
    "SELECT": ["ADMIN", "USER", "VIEWER"],
    "CREATE": ["ADMIN", "USER"],
    "DELETE": ["ADMIN", "USER"],
    "EDIT": ["ADMIN", "USER"],
    "CONFIGURATION": ["ADMIN"]
}

def require_permission(permiso):
    def wrapper(user=Depends(get_current_user)):
        if user["rol"] not in PERMISOS[permiso]:
            raise HTTPException(status_code=403, detail="No autorizado")
        return user
    return wrapper


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#@app.get("/")
#def root():
#    return {"mensaje": "Sistema de Stock funcionando 🚀"}


#"@app.post("/productos", response_model=ProductoResponse)
#def crear_producto(
#   producto: ProductoCreate,
#   db: Session = Depends(get_db),
#):
#   nuevo_producto = Producto(
#       nombre=producto.nombre,
#       precio_venta=producto.precio_venta,
#       stock=producto.stock,
#   )
#   db.add(nuevo_producto)
#   db.commit()
#   db.refresh(nuevo_producto)
#   return nuevo_producto



from sqlalchemy import func
from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/login-web", response_class=HTMLResponse)
def login_web():
#   with open("app/static/login.html", encoding="utf-8") as f:
    with open(os.path.join(BASE_DIR, "static", "login.html"), encoding="utf-8") as f:
        return f.read()


@app.post("/productos", response_model=ProductoResponse)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db), user = Depends(require_permission("CREATE"))):
    """
    Genera código de producto con formato:
    100001 .. 100999
    """

    # 1️⃣ Obtener el último código generado
    ultimo_codigo = (
        db.query(func.max(Producto.codigo))
        .filter(Producto.codigo.like("100%"))
        .scalar()
    )

    # 2️⃣ Calcular siguiente secuencia
    if ultimo_codigo:
        secuencia = int(ultimo_codigo[-3:]) + 1
    else:
        secuencia = 1

    # 3️⃣ Validación simple de límite (MVP)
    if secuencia > 999:
        raise ValueError("Límite máximo de productos alcanzado (999)")

    # 4️⃣ Construir código
    codigo = f"100{secuencia:03d}"

    config = get_configuracion(db)

    if producto.precio_venta > config.max_precio_producto:
        raise HTTPException(
            status_code=400,
            detail=f"El precio supera el máximo permitido ({config.max_precio_producto})"
        )

    if producto.stock > config.max_stock_producto:
        raise HTTPException(
            status_code=400,
            detail=f"El stock supera el máximo permitido ({config.max_stock_producto})"
        )    

    # 5️⃣ Crear producto (activo por defecto)
    nuevo = Producto(
        codigo=codigo,
        nombre=producto.nombre,
        precio_venta=producto.precio_venta,
        stock=producto.stock,
        categoria_id=producto.categoria_id,
        activo=True,
        eliminado=False
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo


@app.get("/productos", response_model=list[ProductoResponse])
def listar_productos(user = Depends(require_permission("SELECT")),
                     db: Session = Depends(get_db)):
    return (
        db.query(Producto)
        .options(joinedload(Producto.categoria))
        .filter(Producto.activo == True)
        .all()
    )

@app.get("/productos-web", response_class=HTMLResponse)
def web():
    with open("app/static/productos.html", encoding="utf-8") as f:
        return f.read()
    
@app.post("/ventas")
def crear_venta(venta: VentaCreate, db: Session = Depends(get_db), user = Depends(require_permission("CREATE"))):
    # 1️⃣ Validar cliente
    cliente = db.query(Cliente).filter(
        Cliente.id == venta.cliente_id,
        Cliente.activo == True
    ).first()

    if not cliente:
        raise HTTPException(status_code=400, detail="Cliente inválido o inactivo")

    total = 0
    detalles_db = []

    # 2️⃣ Validar productos y stock
    for item in venta.detalles:
        producto = db.query(Producto).filter(
            Producto.id == item.producto_id,
            Producto.activo == True
        ).first()

        if not producto:
            raise HTTPException(
                status_code=400,
                detail=f"Producto {item.producto_id} inválido o inactivo"
            )

        if item.cantidad > producto.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}"
            )

        subtotal = producto.precio_venta * item.cantidad
        total += subtotal

        detalles_db.append(
            DetalleVenta(
                producto_id=producto.id,
                cantidad=item.cantidad,
                precio_unitario=producto.precio_venta
            )
        )

    # 3️⃣ Crear venta
    nueva_venta = Venta(
        cliente_id=cliente.id,
        total=total
    )

    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)

    # 4️⃣ Guardar detalles + descontar stock
    for detalle in detalles_db:
        detalle.venta_id = nueva_venta.id

        producto = db.query(Producto).filter(
            Producto.id == detalle.producto_id
        ).first()

        producto.stock -= detalle.cantidad

        db.add(detalle)

    db.commit()

    return {
        "venta_id": nueva_venta.id,
        "cliente": cliente.nombre_razon_social,
        "total": total
    } 
       
@app.get("/ventas-web", response_class=HTMLResponse)    
def ventas_web():
    with open("app/static/ventas.html", encoding="utf-8") as f:
        return f.read()

@app.get("/ventas", response_model=list[VentaResponse])
def listar_ventas(user = Depends(require_permission("SELECT")),
                   db: Session = Depends(get_db)):
    return (
        db.query(Venta)
        .options(
            joinedload(Venta.detalles)
            .joinedload(DetalleVenta.producto)
            .joinedload(Producto.categoria)
        )
        .all()
    )

@app.get("/historial-web", response_class=HTMLResponse)
def historial_web():
    with open("app/static/historial.html", encoding="utf-8") as f:
        return f.read()
    
@app.get("/", response_class=HTMLResponse)
def home():
    with open("app/static/home.html", encoding="utf-8") as f:
        return f.read()    


@app.post("/categorias", response_model=CategoriaResponse)
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db), user = Depends(require_permission("CREATE"))):
    nueva = Categoria(nombre=categoria.nombre)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@app.get("/categorias", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db), user = Depends(require_permission("SELECT"))):
    return (
        db.query(Categoria)
        .filter(Categoria.eliminado == False)
        .order_by(Categoria.nombre)
        .all()
    )

@app.put("/categorias/{id}")
def editar_categoria(id: int, data: CategoriaUpdate, db: Session = Depends(get_db), user = Depends(require_permission("EDIT"))):
    c = db.query(Categoria).filter(Categoria.id == id).first()

    if not c:
        raise HTTPException(404, "Categoría no encontrada")

    c.nombre = data.nombre
    db.commit()

    return {"ok": True}

@app.delete("/categorias/{id}")
def eliminar_categoria(id: int, db: Session = Depends(get_db), user = Depends(require_permission("DELETE"))):

    c = db.query(Categoria).filter(Categoria.id == id).first()

    if not c:
        raise HTTPException(404, "Categoría no encontrada")

    # ✅ validar que no tenga productos activos
    productos = db.query(Producto).filter(
        Producto.categoria_id == id,
        Producto.eliminado == False
    ).count()

    if productos > 0:
        raise HTTPException(
            400,
            f"La categoría tiene {productos} productos asociados"
        )

    c.eliminado = True
    c.activo = False

    db.commit()

    return {"ok": True}

@app.get("/configuracion-web", response_class=HTMLResponse)
def configuracion():
    with open("app/static/configuracion.html", encoding="utf-8") as f:
        return f.read()  
    
@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db), user = Depends(require_permission("DELETE"))):
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.eliminado == False
    ).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    producto.eliminado = True
    db.commit()

    return {"mensaje": "Producto eliminado"}


from fastapi import HTTPException

@app.post("/productos/{producto_id}/desactivar")
def desactivar_producto(producto_id: int, db: Session = Depends(get_db), user = Depends(require_permission("EDIT"))):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()

    if not producto:
        raise HTTPException(404, "Producto no encontrado")

    if producto.eliminado:
        raise HTTPException(400, "Producto eliminado no puede activarse")

    producto.activo = False
    db.commit()

    return {"ok": True}


@app.post("/productos/{producto_id}/activar")
def activar_producto(producto_id: int, db: Session = Depends(get_db), user = Depends(require_permission("EDIT"))):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()

    if not producto:
        raise HTTPException(404, "Producto no encontrado")

    if producto.eliminado:
        raise HTTPException(400, "Producto eliminado no puede activarse")

    producto.activo = True
    db.commit()

    return {"ok": True}

@app.get("/productos-admin", response_model=list[ProductoResponse])
def listar_productos_admin(user = Depends(require_permission("SELECT")), db: Session = Depends(get_db)):

    productos = db.query(Producto).filter(Producto.eliminado == False).all()

    return productos
    
    
@app.post("/stock/ingreso")
def ingresar_stock(data: IngresoStockCreate, db: Session = Depends(get_db), user = Depends(require_permission("CREATE"))):
    producto = db.query(Producto).filter(
        Producto.id == data.producto_id,
        Producto.activo == True
    ).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no válido")

    # Registrar movimiento
    movimiento = MovimientoStock(
        producto_id=producto.id,
        tipo="INGRESO",
        cantidad=data.cantidad,
        motivo=data.motivo
    )
    db.add(movimiento)

    # Actualizar stock derivado
    producto.stock += data.cantidad

    db.commit()

    return {
        "mensaje": "Stock ingresado",
        "producto": producto.nombre,
        "nuevo_stock": producto.stock
    }
    
@app.get("/stock-web", response_class=HTMLResponse)
def stock_web():
    with open("app/static/stock.html", encoding="utf-8") as f:
        return f.read()    
    


@app.get("/productos/buscar")
def buscar_productos(q: str, db: Session = Depends(get_db), user = Depends(require_permission("SELECT"))):
    q = q.strip()
    if len(q) < 2:
        return []

    productos = (
        db.query(Producto)
        .filter(
            or_(
                Producto.nombre.ilike(f"%{q}%"),
                Producto.codigo.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

    return [
        {
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "precio": p.precio_venta,
            "stock": p.stock,
            "activo": p.activo
        }
        for p in productos
    ]
    
@app.post("/clientes", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db), user = Depends(require_permission("CREATE"))):

    # Validaciones por tipo
    if cliente.tipo_cliente == "EMPRESA":
        if not cliente.codigo_fiscal:
            raise HTTPException(status_code=400, detail="Código fiscal obligatorio para Empresa")
        prefijo = "200"

    elif cliente.tipo_cliente == "PERSONA":
        prefijo = "300"

    else:
        raise HTTPException(status_code=400, detail="Tipo de cliente inválido")

    # Obtener último código del tipo
    ultimo_codigo = (
        db.query(func.max(Cliente.codigo_cliente))
        .filter(Cliente.codigo_cliente.like(f"{prefijo}%"))
        .scalar()
    )

    if ultimo_codigo:
        secuencia = int(ultimo_codigo[-3:]) + 1
    else:
        secuencia = 1

    if secuencia > 999:
        raise HTTPException(status_code=400, detail="Límite de clientes alcanzado")

    codigo_cliente = f"{prefijo}{secuencia:03d}"

    nuevo = Cliente(
        codigo_cliente=codigo_cliente,
        tipo_cliente=cliente.tipo_cliente,
        nombre_razon_social=cliente.nombre_razon_social,
        telefono=cliente.telefono,
        calle=cliente.calle,
        numero=cliente.numero,
        localidad=cliente.localidad,
        codigo_postal=cliente.codigo_postal,
        codigo_fiscal=cliente.codigo_fiscal,
        dni=cliente.dni,
        activo=True
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo

@app.get("/clientes/buscar", response_model=list[ClienteResponse])
def buscar_clientes(q: str, db: Session = Depends(get_db), user = Depends(require_permission("SELECT"))):
    q = q.strip()
    if len(q) < 2:
        return []

    return (
        db.query(Cliente)
        .filter(
            Cliente.activo == True,
            or_(
                Cliente.codigo_cliente.ilike(f"%{q}%"),
                Cliente.nombre_razon_social.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

from fastapi.responses import HTMLResponse

@app.get("/clientes-web", response_class=HTMLResponse)
def clientes_web():
    with open("app/static/clientes.html", encoding="utf-8") as f:
        return f.read()
    
@app.get("/clientes", response_model=list[ClienteResponse])
def listar_clientes(db: Session = Depends(get_db),                    user = Depends(require_permission("SELECT"))):
    return (
        db.query(Cliente)
        .filter(Cliente.eliminado == False)
        .order_by(Cliente.codigo_cliente)
        .all()
    )    
    
@app.get("/api/configuracion", response_model=ConfiguracionResponse)
def obtener_configuracion(db: Session = Depends(get_db), user = Depends(require_permission("SELECT"))):

    config = db.query(Configuracion).first()

    if not config:
        config = Configuracion(
            max_precio_producto=9999.99,
            max_stock_producto=10000
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


@app.put("/api/configuracion", response_model=ConfiguracionResponse)
def actualizar_configuracion(
    data: ConfiguracionUpdate,
    user = Depends(require_permission("CONFIGURATION")),
    db: Session = Depends(get_db)):
    
    config = db.query(Configuracion).first()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Configuración no encontrada"
        )

    config.max_precio_producto = data.max_precio_producto
    config.max_stock_producto = data.max_stock_producto

    db.commit()
    db.refresh(config)

    return config

def get_configuracion(db: Session) -> Configuracion:
    config = db.query(Configuracion).first()
    if not config:
        raise HTTPException(status_code=500, detail="Configuración no inicializada")
    return config

@app.put("/productos/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: int,
    data: ProductoUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_permission("EDIT"))
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    config = get_configuracion(db)

    if data.precio_venta > config.max_precio_producto:
        raise HTTPException(
            status_code=400,
            detail=f"Precio máximo permitido: {config.max_precio_producto}"
        )

    if data.stock > config.max_stock_producto:
        raise HTTPException(
            status_code=400,
            detail=f"Stock máximo permitido: {config.max_stock_producto}"
        )

    producto.nombre = data.nombre
    producto.precio_venta = data.precio_venta
    producto.stock = data.stock
    producto.categoria_id = data.categoria_id

    db.commit()
    db.refresh(producto)

    return producto

@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db), user = Depends(require_permission("DELETE"))):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    producto.eliminado = True
    producto.activo = False

    db.commit()

    return {"ok": True}

@app.get("/productos/{producto_id}/detalle", response_model=ProductoResponse)
def detalle_producto(producto_id: int, db: Session = Depends(get_db),                   user = Depends(require_permission("SELECT"))):
    producto = (
        db.query(Producto)
        .filter(Producto.id == producto_id)
        .first()
    )

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return producto

@app.put("/clientes/{id}")
def editar_cliente(id: int, data: ClienteUpdate, db: Session = Depends(get_db), user = Depends(require_permission("EDIT"))):

    c = db.query(Cliente).filter(Cliente.id == id).first()

    if not c:
        raise HTTPException(404, "Cliente no encontrado")

    c.tipo_cliente = data.tipo_cliente
    c.nombre_razon_social = data.nombre_razon_social
    c.telefono = data.telefono

    c.calle = data.calle
    c.numero = data.numero
    c.localidad = data.localidad
    c.codigo_postal = data.codigo_postal

    c.codigo_fiscal = data.codigo_fiscal
    c.dni = data.dni

    db.commit()

    return {"ok": True}

@app.delete("/clientes/{id}")
def eliminar_cliente(id: int, db: Session = Depends(get_db), user = Depends(require_permission("DELETE"))):

    c = db.query(Cliente).filter(Cliente.id == id).first()

    if not c:
        raise HTTPException(404, "Cliente no encontrado")

    c.eliminado = True
    c.activo = False

    db.commit()

    return {"ok": True}

@app.get("/clientes/{id}", response_model=ClienteResponse)
def obtener_cliente(id: int, db: Session = Depends(get_db), user = Depends(require_permission("SELECT"))):

    c = db.query(Cliente).filter(Cliente.id == id).first()

    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return c

#@app.get("/login-web", response_class=HTMLResponse)
#def login_web():
##   with open("app/static/login.html", encoding="utf-8") as f:
#    with open(os.path.join(BASE_DIR, "static", "login.html"), encoding="utf-8") as f:
#        return f.read()

@app.post("/login", response_model=UsuarioResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(Usuario).filter(
        Usuario.username == data.username,
        Usuario.activo == True
    ).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    return user

@app.get("/usuarios")
def listar_usuarios(
    user = Depends(require_permission("CONFIGURATION")),
    db: Session = Depends(get_db)
):
    return db.query(Usuario).all()

@app.post("/usuarios")
def crear_usuario(
    data: UsuarioCreate,
    user = Depends(require_permission("CONFIGURATION")),
    db: Session = Depends(get_db)
):

    # 🔥 VALIDACIÓN DUPLICADO
    existente = db.query(Usuario).filter(
        Usuario.username == data.username
    ).first()

    if existente:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    if len(data.password) < 6:
        raise HTTPException(400, "Password mínimo 6 caracteres")

    if data.password.isnumeric():
        raise HTTPException(400, "Password demasiado débil")

    nuevo = Usuario(
        username=data.username,
        password=hash_password(data.password),
        rol=data.rol,
        nombre=data.nombre
    )

    db.add(nuevo)
    db.commit()

    return {"ok": True}

@app.put("/usuarios/{id}/password")
def cambiar_password(
    id: int,
    data: dict,
    user = Depends(require_permission("CONFIGURATION")),
    db: Session = Depends(get_db)
):

    u = db.query(Usuario).filter(Usuario.id == id).first()

    if not u:
        raise HTTPException(404)

    if len(data.password) < 6:
        raise HTTPException(400, "Password mínimo 6 caracteres")

    if data.password.isnumeric():
        raise HTTPException(400, "Password demasiado débil")

    u.password = hash_password(data["password"])
    db.commit()

    return {"ok": True}

@app.put("/usuarios/{id}/toggle")
def toggle_usuario(
    id: int,
    user = Depends(require_permission("CONFIGURATION")),
    db: Session = Depends(get_db)
):

    u = db.query(Usuario).filter(Usuario.id == id).first()

    if not u:
        raise HTTPException(404)

    # 🔥 VALIDAR ANTES DE MODIFICAR
    if u.rol == "ADMIN" and u.activo:
        raise HTTPException(
            status_code=400,
            detail="No se puede desactivar un ADMIN"
        )

    u.activo = not u.activo
    db.commit()

    return {"ok": True}


@app.delete("/usuarios/{id}")
def eliminar_usuario(
    id: int,
    user = Depends(require_permission("CONFIGURATION")),
    db: Session = Depends(get_db)):
    
    u = db.query(Usuario).filter(Usuario.id == id).first()

    if not u:
        raise HTTPException(404)

    # 🔥 CRÍTICO: NO PERMITIR BORRAR ADMIN
    if u.rol == "ADMIN":
        raise HTTPException(400, "No se puede eliminar un usuario ADMIN")

    db.delete(u)
    db.commit()

    return {"ok": True}

@app.get("/usuarios-web", response_class=HTMLResponse)
def usuarios_web():
    with open("app/static/usuarios.html", encoding="utf-8") as f:
        return f.read()