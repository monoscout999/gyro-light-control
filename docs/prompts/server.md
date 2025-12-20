# PROMPT: Implementar server.py - Servidor Principal de Integración

## CONTEXTO DEL PROYECTO

Estás implementando el servidor principal que integra TODOS los módulos backend del sistema de control de luces. Este es el **corazón del backend** - conecta math_engine, venue_manager, fixture_manager y websocket_handler en una aplicación FastAPI funcional.

Este módulo **DEPENDE DE TODOS LOS ANTERIORES** que ya están validados.

---

## TU TAREA

Crear el archivo `server.py` que:
- Inicialice FastAPI con WebSocket support
- Integre los 4 módulos backend validados
- Maneje el loop de actualización (sensor → cálculos → broadcast)
- Sirva archivos frontend estáticos
- Provea endpoints REST para configuración
- Maneje calibración

---

## ESPECIFICACIONES TÉCNICAS

### Arquitectura General

```
server.py (Este archivo)
    ↓
    ├─ FastAPI app
    ├─ WebSocketHandler
    ├─ VenueManager
    ├─ FixtureManager
    └─ math_engine (funciones)

Flujo de datos:
1. Mobile envía sensor data → WebSocket
2. websocket_handler bufferea datos
3. math_engine convierte a vector 3D
4. math_engine calcula intersección con venue
5. fixture_manager actualiza todos los fixtures
6. server broadcast estado a todos los clientes
```

### Endpoints Requeridos

**WebSocket:**
- `ws://localhost:8080/ws` - Conexión principal

**REST (opcional, para debugging):**
- `GET /` - Sirve index.html
- `GET /api/venue` - Obtiene config del venue
- `POST /api/venue` - Actualiza venue
- `GET /api/fixtures` - Lista fixtures
- `POST /api/fixtures` - Agrega fixture
- `DELETE /api/fixtures/{id}` - Elimina fixture
- `POST /api/calibrate` - Trigger calibración

---

## ESTRUCTURA DEL ARCHIVO

```python
"""
Server Module - Gyro Light Control Visualizer
==============================================

MÓDULO: server
VERSIÓN: 1.0
ESTADO: [EN_DESARROLLO]

RESPONSABILIDAD:
Servidor principal que integra todos los módulos backend.

INTEGRA:
- math_engine.py [VALIDADO]
- venue_manager.py [VALIDADO]
- fixture_manager.py
- websocket_handler.py

DEPENDENCIAS:
- FastAPI
- uvicorn
- numpy
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import asyncio
import numpy as np
import logging
from typing import Optional, Dict, Any

# Importar módulos propios
from math_engine import (
    euler_to_direction,
    create_calibration_offset,
    apply_calibration,
    ray_box_intersection
)
from venue_manager import VenueManager
from fixture_manager import FixtureManager, Fixture
from websocket_handler import WebSocketHandler

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ESTADO GLOBAL DE LA APLICACIÓN
# ============================================================================

class AppState:
    """
    Estado global de la aplicación.
    
    Centraliza todos los managers y estado de calibración.
    """
    
    def __init__(self):
        # Managers
        self.venue = VenueManager()
        self.fixtures = FixtureManager()
        self.websocket = WebSocketHandler(buffer_size=3)
        
        # Estado de calibración
        self.is_calibrated = False
        self.calibration_matrix: Optional[np.ndarray] = None
        
        # Último estado conocido
        self.last_pointer_position: Optional[tuple] = None
        self.last_sensor_data: Optional[dict] = None
        
        logger.info("AppState initialized")
    
    def reset_calibration(self):
        """Resetea la calibración."""
        self.is_calibrated = False
        self.calibration_matrix = None
        logger.info("Calibration reset")


# Instancia global
app_state = AppState()


# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para inicialización y cleanup."""
    logger.info("🚀 Starting Gyro Light Control Server")
    logger.info(f"Venue: {app_state.venue}")
    logger.info(f"Fixtures: {app_state.fixtures}")
    yield
    logger.info("🛑 Shutting down server")


app = FastAPI(
    title="Gyro Light Control API",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# LÓGICA DE PROCESAMIENTO
# ============================================================================

def process_sensor_data(sensor_data: Dict) -> Optional[Dict]:
    """
    Procesa datos del sensor y actualiza todo el sistema.
    
    Args:
        sensor_data: Dict con alpha, beta, gamma
        
    Returns:
        Dict con estado completo para broadcast o None si hay error
        
    Pipeline:
    1. Convertir euler → vector direccional
    2. Aplicar calibración (si existe)
    3. Calcular intersección con venue
    4. Actualizar fixtures
    5. Retornar estado completo
    """
    try:
        alpha = sensor_data['alpha']
        beta = sensor_data['beta']
        gamma = sensor_data['gamma']
        
        # 1. Convertir a vector direccional
        direction_vector = euler_to_direction(alpha, beta, gamma)
        
        # 2. Aplicar calibración si existe
        if app_state.is_calibrated and app_state.calibration_matrix is not None:
            direction_vector = apply_calibration(
                direction_vector,
                app_state.calibration_matrix
            )
        
        # 3. Calcular intersección con venue
        user_position = np.array(app_state.venue.get_user_position())
        bounds = app_state.venue.get_bounds()
        box_min = np.array(bounds['min'])
        box_max = np.array(bounds['max'])
        
        intersection = ray_box_intersection(
            origin=user_position,
            direction=direction_vector,
            box_min=box_min,
            box_max=box_max
        )
        
        if intersection is None:
            logger.warning("Ray does not intersect venue")
            return None
        
        # Guardar estado
        app_state.last_pointer_position = tuple(intersection)
        app_state.last_sensor_data = sensor_data
        
        # 4. Actualizar fixtures
        app_state.fixtures.update_all_fixtures(tuple(intersection))
        
        # 5. Construir estado para broadcast
        state = {
            'type': 'state_update',
            'sensor': sensor_data,
            'pointer': {
                'direction': direction_vector.tolist(),
                'intersection': intersection.tolist()
            },
            'fixtures': [
                {
                    'id': f.id,
                    'name': f.name,
                    'pan': f.current_pan,
                    'tilt': f.current_tilt
                }
                for f in app_state.fixtures.get_all_fixtures()
            ],
            'calibrated': app_state.is_calibrated
        }
        
        return state
        
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}", exc_info=True)
        return None


def perform_calibration(sensor_data: Dict) -> bool:
    """
    Realiza calibración del sistema.
    
    Args:
        sensor_data: Datos del sensor EN EL MOMENTO de calibración
        
    Returns:
        True si calibración exitosa, False si error
        
    Proceso:
    1. Convertir sensor data → vector actual
    2. Calcular vector ideal (usuario → centro pared trasera)
    3. Calcular matriz de rotación
    4. Guardar matriz
    """
    try:
        alpha = sensor_data['alpha']
        beta = sensor_data['beta']
        gamma = sensor_data['gamma']
        
        # Vector actual (donde apunta el celular)
        current_vector = euler_to_direction(alpha, beta, gamma)
        
        # Vector ideal (hacia centro pared trasera)
        user_pos = np.array(app_state.venue.get_user_position())
        back_wall_center = np.array(app_state.venue.get_back_wall_center())
        target_vector = back_wall_center - user_pos
        target_vector = target_vector / np.linalg.norm(target_vector)
        
        # Calcular matriz de rotación
        calibration_matrix = create_calibration_offset(
            current_vector,
            target_vector
        )
        
        # Guardar
        app_state.calibration_matrix = calibration_matrix
        app_state.is_calibrated = True
        
        logger.info(f"✅ Calibration successful")
        logger.info(f"   Current vector: {current_vector}")
        logger.info(f"   Target vector: {target_vector}")
        
        return True
        
    except Exception as e:
        logger.error(f"Calibration failed: {e}", exc_info=True)
        return False


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint principal de WebSocket.
    
    Maneja:
    - Conexión/desconexión
    - Recepción de sensor data
    - Broadcast de estados
    - Comandos especiales (calibrate, etc.)
    """
    await app_state.websocket.connect(websocket)
    
    try:
        while True:
            # Recibir mensaje
            data = await websocket.receive_json()
            message_type = data.get('type')
            
            if message_type == 'sensor_data':
                # Procesar sensor data
                sensor_data = {
                    'alpha': data.get('alpha', 0),
                    'beta': data.get('beta', 0),
                    'gamma': data.get('gamma', 0)
                }
                
                # Agregar a buffer
                import time
                timestamp = data.get('timestamp', time.time() * 1000)
                app_state.websocket.latency_buffer.add_sample(
                    sensor_data, 
                    timestamp
                )
                
                # Procesar (con interpolación)
                buffered_data = app_state.websocket.get_buffered_sensor_data(
                    use_interpolation=True
                )
                
                if buffered_data:
                    state = process_sensor_data(buffered_data)
                    
                    if state:
                        # Broadcast a todos los clientes
                        await app_state.websocket.broadcast(state)
            
            elif message_type == 'calibrate':
                # Calibración solicitada
                sensor_data = {
                    'alpha': data.get('alpha', 0),
                    'beta': data.get('beta', 0),
                    'gamma': data.get('gamma', 0)
                }
                
                success = perform_calibration(sensor_data)
                
                # Responder
                await websocket.send_json({
                    'type': 'calibration_result',
                    'success': success,
                    'message': 'Calibration successful' if success else 'Calibration failed'
                })
                
                # Si exitosa, procesar inmediatamente
                if success:
                    state = process_sensor_data(sensor_data)
                    if state:
                        await app_state.websocket.broadcast(state)
            
            elif message_type == 'ping':
                # Heartbeat
                await websocket.send_json({'type': 'pong'})
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        app_state.websocket.disconnect(websocket)
        logger.info("Client disconnected normally")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        app_state.websocket.disconnect(websocket)


# ============================================================================
# REST API ENDPOINTS (para configuración)
# ============================================================================

@app.get("/")
async def root():
    """Sirve la página principal."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gyro Light Control</title>
    </head>
    <body>
        <h1>Gyro Light Control Server</h1>
        <p>Server is running!</p>
        <ul>
            <li>WebSocket: ws://localhost:8080/ws</li>
            <li>API Docs: <a href="/docs">/docs</a></li>
            <li>Venue Info: <a href="/api/venue">/api/venue</a></li>
        </ul>
    </body>
    </html>
    """)


@app.get("/api/status")
async def get_status():
    """Retorna estado del sistema."""
    return {
        'status': 'running',
        'venue': app_state.venue.to_dict(),
        'fixtures': {
            'count': app_state.fixtures.count(),
            'fixtures': [f.to_dict() for f in app_state.fixtures.get_all_fixtures()]
        },
        'websocket': app_state.websocket.get_stats(),
        'calibration': {
            'is_calibrated': app_state.is_calibrated,
            'last_sensor': app_state.last_sensor_data,
            'last_pointer': app_state.last_pointer_position
        }
    }


@app.get("/api/venue")
async def get_venue():
    """Obtiene configuración del venue."""
    return app_state.venue.to_dict()


@app.post("/api/venue")
async def update_venue(dimensions: Dict[str, float]):
    """
    Actualiza dimensiones del venue.
    
    Body: {"width": 10, "depth": 10, "height": 4}
    """
    try:
        app_state.venue.set_dimensions(
            width=dimensions.get('width', 10),
            depth=dimensions.get('depth', 10),
            height=dimensions.get('height', 4)
        )
        return {'status': 'success', 'venue': app_state.venue.to_dict()}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={'status': 'error', 'message': str(e)}
        )


@app.get("/api/fixtures")
async def get_fixtures():
    """Lista todos los fixtures."""
    return {
        'count': app_state.fixtures.count(),
        'fixtures': [f.to_dict() for f in app_state.fixtures.get_all_fixtures()]
    }


@app.post("/api/fixtures")
async def add_fixture(fixture_data: Dict):
    """
    Agrega un nuevo fixture.
    
    Body: {
        "name": "Moving Head 1",
        "position": [7, 9, 3.5],
        "pan_range": [-270, 270],
        "tilt_range": [-135, 135],
        "mounting": "ceiling"
    }
    """
    try:
        fixture = Fixture(
            name=fixture_data['name'],
            position=tuple(fixture_data['position']),
            pan_range=tuple(fixture_data['pan_range']),
            tilt_range=tuple(fixture_data['tilt_range']),
            mounting=fixture_data.get('mounting', 'ceiling'),
            pan_invert=fixture_data.get('pan_invert', False),
            tilt_invert=fixture_data.get('tilt_invert', False)
        )
        
        fixture_id = app_state.fixtures.add_fixture(fixture)
        
        return {
            'status': 'success',
            'fixture_id': fixture_id,
            'fixture': fixture.to_dict()
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={'status': 'error', 'message': str(e)}
        )


@app.delete("/api/fixtures/{fixture_id}")
async def delete_fixture(fixture_id: str):
    """Elimina un fixture por ID."""
    success = app_state.fixtures.remove_fixture(fixture_id)
    
    if success:
        return {'status': 'success', 'message': 'Fixture deleted'}
    else:
        return JSONResponse(
            status_code=404,
            content={'status': 'error', 'message': 'Fixture not found'}
        )


@app.post("/api/calibrate")
async def calibrate_endpoint(sensor_data: Dict):
    """
    Endpoint REST para calibración (alternativa a WebSocket).
    
    Body: {"alpha": 180, "beta": 0, "gamma": 0}
    """
    success = perform_calibration(sensor_data)
    
    if success:
        return {
            'status': 'success',
            'message': 'Calibration successful',
            'is_calibrated': app_state.is_calibrated
        }
    else:
        return JSONResponse(
            status_code=500,
            content={'status': 'error', 'message': 'Calibration failed'}
        )


@app.post("/api/reset-calibration")
async def reset_calibration():
    """Resetea la calibración."""
    app_state.reset_calibration()
    return {'status': 'success', 'message': 'Calibration reset'}


# ============================================================================
# MAIN - PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("GYRO LIGHT CONTROL - Starting Server")
    logger.info("=" * 60)
    logger.info("Access at: http://localhost:8080")
    logger.info("WebSocket: ws://localhost:8080/ws")
    logger.info("API Docs: http://localhost:8080/docs")
    logger.info("=" * 60)
    
    # Configuración inicial (ejemplo)
    # Agregar un fixture de ejemplo
    example_fixture = Fixture.from_preset(
        "Generic Moving Head",
        "Example Fixture",
        position=(5, 9, 3.5)
    )
    app_state.fixtures.add_fixture(example_fixture)
    logger.info(f"Added example fixture: {example_fixture.name}")
    
    # Iniciar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
```

---

## TESTING MANUAL

**No hay tests unitarios para server.py** porque requiere servidor corriendo.

### Test Manual - Checklist:

```bash
# 1. Iniciar servidor
python server.py

# 2. Verificar que arranca
# Deberías ver: "GYRO LIGHT CONTROL - Starting Server"

# 3. Abrir navegador
# http://localhost:8080
# Deberías ver: "Server is running!"

# 4. Verificar API docs
# http://localhost:8080/docs
# Deberías ver: Swagger UI con todos los endpoints

# 5. Test REST API
curl http://localhost:8080/api/status

# 6. Test WebSocket (requiere cliente)
# Usar herramienta como websocat o Postman
```

---

## CRITERIOS DE VALIDACIÓN

- [ ] Server arranca sin errores
- [ ] FastAPI app inicializa correctamente
- [ ] Todos los módulos importan sin error
- [ ] AppState inicializa managers
- [ ] WebSocket endpoint accesible
- [ ] REST endpoints responden
- [ ] `/api/status` retorna JSON válido
- [ ] Calibración funciona (probado manualmente)
- [ ] Proceso sensor_data sin crashes
- [ ] Logging configurado y visible

---

## DEPENDENCIAS

**Nuevas dependencias a instalar:**

```bash
pip install fastapi uvicorn[standard] --break-system-packages
```

O en requirements.txt:
```
numpy>=1.24.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
```

---

## NOTAS IMPORTANTES

1. **Integración completa**:
   - Este archivo USA los 4 módulos anteriores
   - Todos deben estar en la misma carpeta

2. **AppState global**:
   - Almacena instancias de todos los managers
   - Accessible desde todos los endpoints

3. **WebSocket flow**:
   - Cliente envía sensor_data
   - Server procesa y broadcast
   - Todos los clientes reciben update

4. **Calibración**:
   - Se puede hacer vía WebSocket o REST
   - Matriz se guarda en AppState
   - Persiste durante sesión del servidor

5. **Logging**:
   - INFO level por default
   - Todos los eventos importantes loggeados
   - Útil para debugging

---

## PRÓXIMOS PASOS DESPUÉS DE VALIDAR

1. **Test manual completo**:
   - Arrancar servidor
   - Conectar con cliente WebSocket
   - Enviar sensor data
   - Verificar broadcast

2. **Crear cliente mobile básico**:
   - HTML simple con JavaScript
   - Acceso a DeviceOrientation API
   - WebSocket client

3. **Frontend visualización**:
   - scene3d.js con Three.js
   - Renderizar venue, pointer, fixtures

---

## TIEMPO ESTIMADO

**30-40 minutos** (el más complejo, integra todo)

---

**ENTREGA**: Archivo `server.py` completo, ejecutable con `python server.py`, todos los endpoints funcionando.
