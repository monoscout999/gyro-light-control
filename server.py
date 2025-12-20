"""
Server Module - Gyro Light Control Visualizer
==============================================

MÓDULO: server
VERSIÓN: 2.0
ESTADO: [EN_DESARROLLO]

RESPONSABILIDAD:
Servidor principal que ORQUESTA los módulos backend.

ARQUITECTURA PRODUCTOR-CONSUMIDOR:
- SpatialProcessor: Productor (transforma SensorData → InteractionResult)
- VenueManager: Estado del venue (Single Source of Truth)
- WebSocketHandler: I/O de red

INTEGRA:
- schemas.py [VALIDADO]
- spatial_processor.py [VALIDADO]
- venue_manager.py [VALIDADO]
- websocket_handler.py

DEPENDENCIAS:
- FastAPI, uvicorn, qrcode
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import socket
import qrcode
from typing import Optional, Dict, Any

# Módulos propios - Arquitectura Producer-Consumer
from schemas import SensorData, Vector3D, InteractionResult
from spatial_processor import SpatialProcessor
from venue_manager import VenueManager
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
    
    Orquesta los agentes del sistema:
    - SpatialProcessor: El Productor (lógica matemática)
    - VenueManager: Estado del espacio 3D
    - WebSocketHandler: Comunicación de red
    """
    
    def __init__(self):
        # Estado del venue (Single Source of Truth)
        self.venue = VenueManager()
        
        # Productor de datos espaciales
        self.processor = SpatialProcessor()
        
        # Handler de WebSocket
        self.websocket = WebSocketHandler(buffer_size=3)
        
        # Último estado conocido (para debugging/status)
        self.last_pointer_position: Optional[tuple] = None
        self.last_sensor_data: Optional[dict] = None
        
        logger.info("AppState initialized (Producer-Consumer Architecture)")
    
    @property
    def is_calibrated(self) -> bool:
        """Delega al SpatialProcessor."""
        return self.processor.is_calibrated
    
    def reset_calibration(self):
        """Resetea la calibración delegando al SpatialProcessor."""
        self.processor.reset_calibration()
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

def process_sensor_data(raw_data: Dict) -> Optional[Dict]:
    """
    Procesa datos del sensor delegando al SpatialProcessor.
    
    Args:
        raw_data: Dict con alpha, beta, gamma, timestamp
        
    Returns:
        Dict con estado completo para broadcast o None si hay error
        
    Pipeline (delegado a SpatialProcessor):
    1. Validar input con Pydantic (SensorData)
    2. Aplicar calibración matricial (si existe)
    3. Convertir euler → vector direccional  
    4. Calcular intersección con venue
    5. Retornar estado para broadcast
    """
    try:
        # 1. Validar input con Pydantic schema
        sensor = SensorData(
            alpha=raw_data.get('alpha', 0),
            beta=raw_data.get('beta', 0),
            gamma=raw_data.get('gamma', 0),
            timestamp=raw_data.get('timestamp')
        )
        
        # 2. Obtener contexto del venue
        user_pos = app_state.venue.get_user_position_v3d()
        bounds_min, bounds_max = app_state.venue.get_bounds_v3d()
        
        # 3. Delegar al Productor (SpatialProcessor)
        result = app_state.processor.process(
            sensor=sensor,
            user_position=user_pos,
            bounds_min=bounds_min,
            bounds_max=bounds_max
        )
        
        if result is None:
            logger.debug("Ray does not intersect venue")
            return None
        
        # 4. Guardar estado para debugging
        app_state.last_pointer_position = result.intersection.to_list()
        app_state.last_sensor_data = raw_data
        
        # 5. Retornar formato de broadcast
        return result.to_broadcast_dict()
        
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}", exc_info=True)
        return None


def perform_calibration(raw_data: Dict) -> bool:
    """
    Realiza calibración del sistema usando calibración matricial.
    
    Usa Rodrigues' formula para alinear el vector actual del sensor
    con la dirección hacia el centro de la pared trasera.
    """
    try:
        # Validar input
        sensor = SensorData(
            alpha=raw_data.get('alpha', 0),
            beta=raw_data.get('beta', 0),
            gamma=raw_data.get('gamma', 0)
        )
        
        # Obtener dirección target (hacia pared trasera)
        target_direction = app_state.venue.get_calibration_target_direction()
        
        # Delegar calibración al SpatialProcessor
        success = app_state.processor.calibrate(sensor, target_direction)
        
        if success:
            logger.info("✅ Calibration successful (Matrix/Rodrigues)")
            logger.info(f"   Target direction: {target_direction}")
        
        return success
        
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

            elif message_type == 'reset_calibration':
                # Resetear calibración
                app_state.reset_calibration()
                await websocket.send_json({
                    'type': 'calibration_result',
                    'success': True,
                    'message': 'Calibration reset'
                })
            
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

# OLD ROOT ROUTE - COMMENTED OUT (line 340-359)
# See line 508 for the correct route that serves frontend/index.html


@app.get("/api/status")
async def get_status():
    """Retorna estado del sistema."""
    return {
        'status': 'running',
        'architecture': 'producer-consumer',
        'venue': app_state.venue.to_dict(),
        'websocket': app_state.websocket.get_stats(),
        'processor': {
            'is_calibrated': app_state.processor.is_calibrated,
            'calibration_type': 'matrix' if app_state.processor.is_calibrated else 'none'
        },
        'last_state': {
            'sensor': app_state.last_sensor_data,
            'pointer': app_state.last_pointer_position
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


@app.delete("/api/fixtures/{fixture_id}")
async def delete_fixture(fixture_id: str):
    """Endpoint desactivado."""
    return JSONResponse(
        status_code=410,
        content={'status': 'error', 'message': 'Fixtures functionality removed'}
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
# SERVIR ARCHIVOS FRONTEND
# ============================================================================

# Montar carpeta js como estáticos
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")

# Ruta raíz - servir index.html
@app.get("/", response_class=FileResponse)
async def serve_index():
    """Sirve la página principal del visualizador."""
    return "frontend/index.html"

# Ruta mobile
@app.get("/mobile.html", response_class=FileResponse)
async def serve_mobile():
    """Sirve la interfaz móvil."""
    return "frontend/mobile.html"

# ============================================================================
# UTILITIES
# ============================================================================

def get_local_ip():
    """Obtiene la dirección IP local de la máquina."""
    try:
        # Crea un socket UDP temporal para detectar la IP de red
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # No necesita conectar realmente, solo para obtener la interfaz
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ============================================================================
# MAIN - PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configuración de red
    port = 8080
    local_ip = get_local_ip()
    mobile_url = f"http://{local_ip}:{port}/mobile.html"
    desktop_url = f"http://{local_ip}:{port}"
    
    logger.info("=" * 60)
    logger.info("GYRO LIGHT CONTROL - Starting Server")
    logger.info("=" * 60)
    logger.info(f"Local Access:   http://localhost:{port}")
    logger.info(f"Network Access: {desktop_url}")
    logger.info(f"Mobile Access:  {mobile_url}")
    logger.info("-" * 60)
    
    # Generar QR para el link móvil
    try:
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(mobile_url)
        qr.make(fit=True)
        
        # Imprimir QR en consola de forma minimalista
        logger.info("SCAN THIS QR TO OPEN MOBILE INTERFACE:")
        # Capturamos la salida ASCII del QR
        import io
        f = io.StringIO()
        qr.print_ascii(out=f, invert=True)
        print(f.getvalue())
    except Exception as e:
        logger.warning(f"Could not generate QR code: {e}")
        
    logger.info("-" * 60)
    logger.info(f"WebSocket: ws://{local_ip}:{port}/ws")
    logger.info(f"API Docs:  http://{local_ip}:{port}/docs")
    logger.info("=" * 60)
    
    # Iniciar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )

