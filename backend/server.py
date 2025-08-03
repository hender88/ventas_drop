from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo

# Configuración
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "control_gastos")

# Inicializar MongoDB
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class Cliente(BaseModel):
    id: Optional[str] = None
    nombre: str
    apellidos: str
    telefono: str

class Venta(BaseModel):
    id: Optional[str] = None
    cliente_id: str
    producto: str
    fecha_venta: date
    fecha_entrega: date
    valor_venta: float
    ganancia: float
    entregado: bool
    valor_perdida: Optional[float] = 0

class Gasto(BaseModel):
    id: Optional[str] = None
    concepto: str
    valor: float
    fecha_inicio: date
    fecha_final: date

class EstadisticasResponse(BaseModel):
    ganancias_totales: float
    perdidas_totales: float
    inversion_publicidad: float
    productos_vendidos: int
    productos_devueltos: int
    ventas_por_dia: List[dict]
    ganancias_por_producto: List[dict]

# Datos simulados para demo
async def crear_datos_demo():
    """Crear datos de demostración si no existen"""
    # Verificar si ya hay datos
    ventas_count = await db.ventas.count_documents({})
    if ventas_count > 0:
        return
    
    # Clientes demo
    clientes_demo = [
        {"id": str(uuid.uuid4()), "nombre": "Juan", "apellidos": "Pérez", "telefono": "3001234567"},
        {"id": str(uuid.uuid4()), "nombre": "María", "apellidos": "González", "telefono": "3007654321"},
        {"id": str(uuid.uuid4()), "nombre": "Carlos", "apellidos": "Rodríguez", "telefono": "3009876543"},
        {"id": str(uuid.uuid4()), "nombre": "Ana", "apellidos": "Martínez", "telefono": "3005555555"}
    ]
    
    for cliente in clientes_demo:
        await db.clientes.insert_one(cliente)
    
    # Ventas demo (últimos 30 días)
    from datetime import datetime, timedelta
    import random
    
    productos = ["Producto A", "Producto B", "Producto C", "Producto D", "Producto E"]
    
    ventas_demo = []
    for i in range(25):  # 25 ventas de ejemplo
        fecha_venta = datetime.now().date() - timedelta(days=random.randint(0, 30))
        fecha_entrega = fecha_venta + timedelta(days=random.randint(1, 7))
        
        valor_venta = round(random.uniform(50000, 500000), 2)
        ganancia = round(valor_venta * random.uniform(0.2, 0.4), 2)
        entregado = random.choice([True, True, True, False])  # 75% entregados
        valor_perdida = round(random.uniform(10000, 50000), 2) if not entregado else 0
        
        venta = {
            "id": str(uuid.uuid4()),
            "cliente_id": random.choice(clientes_demo)["id"],
            "producto": random.choice(productos),
            "fecha_venta": fecha_venta.isoformat(),
            "fecha_entrega": fecha_entrega.isoformat(),
            "valor_venta": valor_venta,
            "ganancia": ganancia,
            "entregado": entregado,
            "valor_perdida": valor_perdida
        }
        ventas_demo.append(venta)
    
    for venta in ventas_demo:
        await db.ventas.insert_one(venta)
    
    # Gastos de publicidad demo
    gastos_demo = [
        {
            "id": str(uuid.uuid4()),
            "concepto": "Facebook Ads",
            "valor": 200000,
            "fecha_inicio": (datetime.now().date() - timedelta(days=20)).isoformat(),
            "fecha_final": (datetime.now().date() - timedelta(days=13)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "concepto": "Google Ads",
            "valor": 150000,
            "fecha_inicio": (datetime.now().date() - timedelta(days=15)).isoformat(),
            "fecha_final": (datetime.now().date() - timedelta(days=8)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "concepto": "Instagram Promoción",
            "valor": 80000,
            "fecha_inicio": (datetime.now().date() - timedelta(days=10)).isoformat(),
            "fecha_final": (datetime.now().date() - timedelta(days=3)).isoformat()
        }
    ]
    
    for gasto in gastos_demo:
        await db.gastos.insert_one(gasto)

@app.on_event("startup")
async def startup_event():
    """Inicializar datos demo al arrancar"""
    await crear_datos_demo()

# Endpoints

@app.get("/")
async def root():
    return {"message": "Sistema de Control de Gastos y Ganancias API"}

@app.get("/api/dashboard", response_model=EstadisticasResponse)
async def get_dashboard():
    """Obtener estadísticas del dashboard"""
    from datetime import datetime, timedelta
    
    # Obtener todas las ventas
    ventas = await db.ventas.find({}).to_list(length=None)
    gastos = await db.gastos.find({}).to_list(length=None)
    
    # Calcular métricas
    ganancias_totales = sum(v["ganancia"] for v in ventas if v["entregado"])
    perdidas_totales = sum(v["valor_perdida"] for v in ventas if not v["entregado"])
    inversion_publicidad = sum(g["valor"] for g in gastos)
    productos_vendidos = len([v for v in ventas if v["entregado"]])
    productos_devueltos = len([v for v in ventas if not v["entregado"]])
    
    # Ventas por día (últimos 7 días)
    ventas_por_dia = []
    for i in range(7):
        fecha = datetime.now().date() - timedelta(days=i)
        ventas_dia = len([v for v in ventas if v["fecha_venta"] == fecha.isoformat() and v["entregado"]])
        ventas_por_dia.append({
            "fecha": fecha.isoformat(),
            "ventas": ventas_dia
        })
    
    ventas_por_dia.reverse()
    
    # Ganancias por producto
    productos = {}
    for venta in ventas:
        if venta["entregado"]:
            if venta["producto"] not in productos:
                productos[venta["producto"]] = 0
            productos[venta["producto"]] += venta["ganancia"]
    
    ganancias_por_producto = [
        {"producto": k, "ganancia": v} for k, v in productos.items()
    ]
    
    return EstadisticasResponse(
        ganancias_totales=ganancias_totales,
        perdidas_totales=perdidas_totales,
        inversion_publicidad=inversion_publicidad,
        productos_vendidos=productos_vendidos,
        productos_devueltos=productos_devueltos,
        ventas_por_dia=ventas_por_dia,
        ganancias_por_producto=ganancias_por_producto
    )

@app.post("/api/ventas")
async def crear_venta(venta: Venta):
    """Crear nueva venta"""
    venta.id = str(uuid.uuid4())
    venta_dict = venta.dict()
    venta_dict["fecha_venta"] = venta.fecha_venta.isoformat()
    venta_dict["fecha_entrega"] = venta.fecha_entrega.isoformat()
    
    result = await db.ventas.insert_one(venta_dict)
    if result.inserted_id:
        return {"message": "Venta creada exitosamente", "id": venta.id}
    raise HTTPException(status_code=400, detail="Error al crear venta")

@app.post("/api/clientes")
async def crear_cliente(cliente: Cliente):
    """Crear nuevo cliente"""
    cliente.id = str(uuid.uuid4())
    cliente_dict = cliente.dict()
    
    result = await db.clientes.insert_one(cliente_dict)
    if result.inserted_id:
        return {"message": "Cliente creado exitosamente", "id": cliente.id}
    raise HTTPException(status_code=400, detail="Error al crear cliente")

@app.post("/api/gastos")
async def crear_gasto(gasto: Gasto):
    """Crear nuevo gasto"""
    gasto.id = str(uuid.uuid4())
    gasto_dict = gasto.dict()
    gasto_dict["fecha_inicio"] = gasto.fecha_inicio.isoformat()
    gasto_dict["fecha_final"] = gasto.fecha_final.isoformat()
    
    result = await db.gastos.insert_one(gasto_dict)
    if result.inserted_id:
        return {"message": "Gasto creado exitosamente", "id": gasto.id}
    raise HTTPException(status_code=400, detail="Error al crear gasto")

@app.get("/api/clientes")
async def listar_clientes():
    """Obtener lista de clientes"""
    clientes = await db.clientes.find({}).to_list(length=None)
    return clientes

@app.get("/api/ventas")
async def listar_ventas():
    """Obtener lista de ventas"""
    ventas = await db.ventas.find({}).to_list(length=None)
    return ventas

@app.get("/api/gastos")
async def listar_gastos():
    """Obtener lista de gastos"""
    gastos = await db.gastos.find({}).to_list(length=None)
    return gastos

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)