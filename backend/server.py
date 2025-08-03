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
    fecha_entrega: Optional[date] = None
    valor_venta: float
    ganancia: float
    entregado: Optional[bool] = None  # null = pendiente, True = entregado, False = devuelto
    valor_perdida: Optional[float] = 0

class VentaUpdate(BaseModel):
    fecha_entrega: Optional[date] = None
    entregado: Optional[bool] = None
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
    for i in range(30):  # 30 ventas de ejemplo
        fecha_venta = datetime.now().date() - timedelta(days=random.randint(0, 30))
        
        valor_venta = round(random.uniform(50000, 500000), 2)
        ganancia = round(valor_venta * random.uniform(0.2, 0.4), 2)
        
        # 40% pendientes (null), 40% entregados (True), 20% devueltos (False)
        estado_random = random.choice([None, None, None, None, True, True, True, True, False, False])
        
        fecha_entrega = None
        valor_perdida = 0
        
        if estado_random is not None:  # Si no está pendiente
            fecha_entrega = fecha_venta + timedelta(days=random.randint(1, 7))
            if estado_random == False:  # Si fue devuelto
                valor_perdida = round(random.uniform(10000, 50000), 2)
        
        venta = {
            "id": str(uuid.uuid4()),
            "cliente_id": random.choice(clientes_demo)["id"],
            "producto": random.choice(productos),
            "fecha_venta": fecha_venta.isoformat(),
            "fecha_entrega": fecha_entrega.isoformat() if fecha_entrega else None,
            "valor_venta": valor_venta,
            "ganancia": ganancia,
            "entregado": estado_random,
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
async def get_dashboard(fecha_inicio: Optional[str] = None, fecha_final: Optional[str] = None):
    """Obtener estadísticas del dashboard con filtros opcionales de fecha"""
    from datetime import datetime, timedelta
    
    # Configurar filtros de fecha
    filtro_fecha = {}
    if fecha_inicio and fecha_final:
        try:
            fecha_inicio_dt = datetime.fromisoformat(fecha_inicio).date()
            fecha_final_dt = datetime.fromisoformat(fecha_final).date()
            filtro_fecha = {
                "fecha_venta": {
                    "$gte": fecha_inicio_dt.isoformat(),
                    "$lte": fecha_final_dt.isoformat()
                }
            }
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    # Obtener ventas con filtro de fecha
    ventas = await db.ventas.find(filtro_fecha).to_list(length=None)
    
    # Obtener gastos con filtro de fecha (si aplica)
    filtro_gastos = {}
    if fecha_inicio and fecha_final:
        try:
            filtro_gastos = {
                "$or": [
                    {
                        "fecha_inicio": {
                            "$gte": fecha_inicio_dt.isoformat(),
                            "$lte": fecha_final_dt.isoformat()
                        }
                    },
                    {
                        "fecha_final": {
                            "$gte": fecha_inicio_dt.isoformat(),
                            "$lte": fecha_final_dt.isoformat()
                        }
                    }
                ]
            }
        except:
            pass
    
    gastos = await db.gastos.find(filtro_gastos).to_list(length=None)
    
    # Calcular métricas
    ganancias_totales = sum(v["ganancia"] for v in ventas if v.get("entregado") == True)
    perdidas_totales = sum(v.get("valor_perdida", 0) for v in ventas if v.get("entregado") == False)
    inversion_publicidad = sum(g["valor"] for g in gastos)
    productos_vendidos = len([v for v in ventas if v.get("entregado") == True])
    productos_devueltos = len([v for v in ventas if v.get("entregado") == False])
    
    # Ventas por día (últimos 7 días o período seleccionado)
    ventas_por_dia = []
    if fecha_inicio and fecha_final:
        # Usar rango seleccionado
        current_date = fecha_inicio_dt
        while current_date <= fecha_final_dt:
            ventas_dia = len([v for v in ventas if v["fecha_venta"] == current_date.isoformat() and v.get("entregado") == True])
            ventas_por_dia.append({
                "fecha": current_date.isoformat(),
                "ventas": ventas_dia
            })
            current_date += timedelta(days=1)
    else:
        # Últimos 7 días por defecto
        for i in range(7):
            fecha = datetime.now().date() - timedelta(days=i)
            ventas_dia = len([v for v in ventas if v["fecha_venta"] == fecha.isoformat() and v.get("entregado") == True])
            ventas_por_dia.append({
                "fecha": fecha.isoformat(),
                "ventas": ventas_dia
            })
        ventas_por_dia.reverse()
    
    # Ganancias por producto
    productos = {}
    for venta in ventas:
        if venta.get("entregado") == True:
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
    """Crear nueva venta (inicialmente sin estado de entrega)"""
    venta.id = str(uuid.uuid4())
    venta_dict = venta.dict()
    venta_dict["fecha_venta"] = venta.fecha_venta.isoformat()
    if venta.fecha_entrega:
        venta_dict["fecha_entrega"] = venta.fecha_entrega.isoformat()
    
    result = await db.ventas.insert_one(venta_dict)
    if result.inserted_id:
        return {"message": "Venta creada exitosamente", "id": venta.id}
    raise HTTPException(status_code=400, detail="Error al crear venta")

@app.put("/api/ventas/{venta_id}")
async def actualizar_venta(venta_id: str, venta_update: VentaUpdate):
    """Actualizar estado de entrega de una venta"""
    update_dict = {}
    
    if venta_update.fecha_entrega:
        update_dict["fecha_entrega"] = venta_update.fecha_entrega.isoformat()
    
    if venta_update.entregado is not None:
        update_dict["entregado"] = venta_update.entregado
    
    if venta_update.valor_perdida is not None:
        update_dict["valor_perdida"] = venta_update.valor_perdida
    
    result = await db.ventas.update_one(
        {"id": venta_id}, 
        {"$set": update_dict}
    )
    
    if result.matched_count:
        return {"message": "Venta actualizada exitosamente"}
    raise HTTPException(status_code=404, detail="Venta no encontrada")

@app.get("/api/ventas/pendientes")
async def listar_ventas_pendientes():
    """Obtener ventas sin estado definido (pendientes de procesamiento)"""
    ventas_pendientes = await db.ventas.find({"entregado": None}).to_list(length=None)
    
    # Get client names for better display
    clientes = await db.clientes.find({}).to_list(length=None)
    clientes_dict = {c["id"]: f"{c['nombre']} {c['apellidos']}" for c in clientes}
    
    for venta in ventas_pendientes:
        if '_id' in venta:
            del venta['_id']
        venta['cliente_nombre'] = clientes_dict.get(venta['cliente_id'], 'Cliente no encontrado')
    
    return ventas_pendientes

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
    # Convert ObjectId to string for JSON serialization
    for cliente in clientes:
        if '_id' in cliente:
            del cliente['_id']
    return clientes

@app.get("/api/ventas")
async def listar_ventas():
    """Obtener lista de ventas"""
    ventas = await db.ventas.find({}).to_list(length=None)
    # Convert ObjectId to string for JSON serialization
    for venta in ventas:
        if '_id' in venta:
            del venta['_id']
    return ventas

@app.get("/api/gastos")
async def listar_gastos():
    """Obtener lista de gastos"""
    gastos = await db.gastos.find({}).to_list(length=None)
    # Convert ObjectId to string for JSON serialization
    for gasto in gastos:
        if '_id' in gasto:
            del gasto['_id']
    return gastos

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)