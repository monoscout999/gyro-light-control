"""
WebSocket Handler Module - Gyro Light Control Visualizer
=========================================================

MÓDULO: websocket_handler
VERSIÓN: 1.0
ESTADO: [EN_DESARROLLO]

RESPONSABILIDAD:
Gestión de conexiones WebSocket y buffer de latencia.

HACE:
- Gestionar conexiones/desconexiones
- Recibir datos del sensor
- Buffer con interpolación
- Broadcast de estados

DEPENDENCIAS:
- FastAPI (WebSocket)
- asyncio (stdlib)
"""

from fastapi import WebSocket
from collections import deque
from typing import Set, Dict, Any, Optional
import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LatencyBuffer:
    """
    Buffer de datos del sensor para compensar latencia de red.
    
    Mantiene las últimas N muestras y puede interpolar entre ellas
    para predecir valores futuros y suavizar movimiento.
    """
    
    def __init__(self, buffer_size: int = 3):
        """
        Args:
            buffer_size: Cantidad de muestras a mantener (3-5 recomendado)
        """
        self.buffer_size = buffer_size
        self.samples: deque = deque(maxlen=buffer_size)
    
    def add_sample(self, data: Dict, timestamp: float) -> None:
        """
        Agrega una muestra al buffer.
        
        Args:
            data: Dict con alpha, beta, gamma
            timestamp: Timestamp en milisegundos
        """
        self.samples.append({
            'data': data,
            'timestamp': timestamp
        })
    
    def get_latest(self) -> Optional[Dict]:
        """
        Retorna la muestra más reciente.
        
        Returns:
            Dict con data del sensor o None si buffer vacío
        """
        if not self.samples:
            return None
        return self.samples[-1]['data']
    
    def get_interpolated(self, target_time: Optional[float] = None) -> Optional[Dict]:
        """
        Retorna datos interpolados para un tiempo específico.
        
        Args:
            target_time: Timestamp objetivo (None = now)
            
        Returns:
            Dict con alpha, beta, gamma interpolados
            
        Si solo hay 1 muestra, retorna esa muestra.
        Si hay 2+, interpola linealmente entre las 2 más recientes.
        """
        if not self.samples:
            return None
        
        if len(self.samples) == 1:
            return self.samples[0]['data']
        
        # Interpolar entre las 2 últimas muestras
        sample1 = self.samples[-2]
        sample2 = self.samples[-1]
        
        if target_time is None:
            target_time = time.time() * 1000  # ms
        
        t1 = sample1['timestamp']
        t2 = sample2['timestamp']
        
        # Evitar división por cero
        if t2 - t1 == 0:
            return sample2['data']
        
        # Factor de interpolación (0 a 1)
        # Si target_time > t2, extrapolamos ligeramente (predicción)
        factor = (target_time - t1) / (t2 - t1)
        factor = max(0, min(1.5, factor))  # Limitar extrapolación
        
        # Interpolar cada valor
        d1 = sample1['data']
        d2 = sample2['data']
        
        interpolated = {}
        for key in ['alpha', 'beta', 'gamma']:
            v1 = d1.get(key, 0)
            v2 = d2.get(key, 0)
            
            # Manejar wrap-around de alpha (0-360°)
            if key == 'alpha':
                diff = v2 - v1
                if abs(diff) > 180:
                    # Shortest path around circle
                    if diff > 0:
                        v1 += 360
                    else:
                        v2 += 360
            
            interpolated[key] = v1 + (v2 - v1) * factor
            
            # Normalizar alpha de vuelta a 0-360
            if key == 'alpha':
                interpolated[key] = interpolated[key] % 360
        
        return interpolated
    
    def clear(self) -> None:
        """Limpia el buffer."""
        self.samples.clear()
    
    def size(self) -> int:
        """Retorna cantidad de muestras en buffer."""
        return len(self.samples)


class WebSocketHandler:
    """
    Gestor de conexiones WebSocket y comunicación bidireccional.
    
    Responsabilidades:
    - Gestionar conexiones activas
    - Recibir datos del sensor desde mobile
    - Broadcast de estados a todos los clientes
    - Buffer de latencia
    """
    
    def __init__(self, buffer_size: int = 3):
        """
        Args:
            buffer_size: Tamaño del buffer de latencia
        """
        self.active_connections: Set[WebSocket] = set()
        self.latency_buffer = LatencyBuffer(buffer_size)
        self.message_count = 0
        self.error_count = 0
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Acepta una nueva conexión WebSocket.
        
        Args:
            websocket: Instancia de WebSocket
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
        # Enviar mensaje de bienvenida
        await self.send_personal(websocket, {
            "type": "connected",
            "message": "WebSocket connection established",
            "timestamp": time.time() * 1000
        })
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remueve una conexión WebSocket.
        
        Args:
            websocket: Instancia de WebSocket
        """
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """
        Envía mensaje a un cliente específico.
        
        Args:
            websocket: Cliente destino
            message: Dict a enviar (se serializa a JSON)
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.error_count += 1
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Envía mensaje a TODOS los clientes conectados.
        
        Args:
            message: Dict a enviar (se serializa a JSON)
        """
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                self.message_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
                self.error_count += 1
        
        # Limpiar conexiones muertas
        for connection in disconnected:
            self.disconnect(connection)
    
    async def receive_sensor_data(self, websocket: WebSocket) -> Optional[Dict]:
        """
        Recibe datos del sensor desde un cliente.
        
        Args:
            websocket: Cliente que envía datos
            
        Returns:
            Dict con sensor data o None si hay error
            
        Agrega los datos al buffer de latencia automáticamente.
        """
        try:
            data = await websocket.receive_json()
            
            if data.get('type') == 'sensor_data':
                timestamp = data.get('timestamp', time.time() * 1000)
                
                sensor_data = {
                    'alpha': data.get('alpha', 0),
                    'beta': data.get('beta', 0),
                    'gamma': data.get('gamma', 0)
                }
                
                # Agregar a buffer
                self.latency_buffer.add_sample(sensor_data, timestamp)
                
                return sensor_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error receiving sensor data: {e}")
            return None
    
    def get_buffered_sensor_data(self, use_interpolation: bool = True) -> Optional[Dict]:
        """
        Obtiene datos del sensor desde el buffer.
        
        Args:
            use_interpolation: Si True, usa interpolación. Si False, retorna último valor.
            
        Returns:
            Dict con alpha, beta, gamma
        """
        if use_interpolation:
            return self.latency_buffer.get_interpolated()
        else:
            return self.latency_buffer.get_latest()
    
    def clear_buffer(self) -> None:
        """Limpia el buffer de latencia."""
        self.latency_buffer.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del handler.
        
        Returns:
            Dict con métricas útiles
        """
        return {
            'active_connections': len(self.active_connections),
            'buffer_size': self.latency_buffer.size(),
            'messages_sent': self.message_count,
            'errors': self.error_count
        }
    
    def __repr__(self) -> str:
        return (
            f"WebSocketHandler("
            f"connections={len(self.active_connections)}, "
            f"buffer={self.latency_buffer.size()})"
        )


# ============================================================================
# TESTS
# ============================================================================

def test_buffer_add_and_get():
    """Test: agregar y obtener datos del buffer"""
    buffer = LatencyBuffer(buffer_size=3)
    
    # Agregar muestra
    data = {'alpha': 180, 'beta': 0, 'gamma': 0}
    buffer.add_sample(data, 1000)
    
    # Obtener
    result = buffer.get_latest()
    assert result == data
    
    print("✅ Test buffer_add_and_get passed")


def test_buffer_size_limit():
    """Test: buffer respeta límite de tamaño"""
    buffer = LatencyBuffer(buffer_size=3)
    
    # Agregar más de 3 muestras
    for i in range(5):
        buffer.add_sample({'alpha': i}, 1000 + i)
    
    # Solo debe tener 3
    assert buffer.size() == 3
    
    # La más antigua (0) debe haberse eliminado
    latest = buffer.get_latest()
    assert latest['alpha'] == 4  # Última agregada
    
    print("✅ Test buffer_size_limit passed")


def test_buffer_interpolation():
    """Test: interpolación entre muestras"""
    buffer = LatencyBuffer(buffer_size=3)
    
    # Agregar 2 muestras
    buffer.add_sample({'alpha': 0, 'beta': 0, 'gamma': 0}, 1000)
    buffer.add_sample({'alpha': 100, 'beta': 50, 'gamma': 10}, 2000)
    
    # Interpolar en medio (t=1500)
    result = buffer.get_interpolated(target_time=1500)
    
    # Debe estar aproximadamente en el medio
    assert 45 <= result['alpha'] <= 55  # ~50
    assert 20 <= result['beta'] <= 30   # ~25
    
    print("✅ Test buffer_interpolation passed")


def test_buffer_alpha_wraparound():
    """Test: alpha wrap-around (359° → 1°)"""
    buffer = LatencyBuffer(buffer_size=3)
    
    # De 350° a 10° (debería ir por 0°, no por 180°)
    buffer.add_sample({'alpha': 350, 'beta': 0, 'gamma': 0}, 1000)
    buffer.add_sample({'alpha': 10, 'beta': 0, 'gamma': 0}, 2000)
    
    # Interpolar en medio
    result = buffer.get_interpolated(target_time=1500)
    
    # Debe estar cerca de 0° o 360°, NO cerca de 180°
    assert result['alpha'] < 30 or result['alpha'] > 330
    
    print("✅ Test buffer_alpha_wraparound passed")


def test_buffer_clear():
    """Test: limpiar buffer"""
    buffer = LatencyBuffer(buffer_size=3)
    
    buffer.add_sample({'alpha': 180}, 1000)
    buffer.add_sample({'alpha': 190}, 2000)
    
    assert buffer.size() == 2
    
    buffer.clear()
    
    assert buffer.size() == 0
    assert buffer.get_latest() is None
    
    print("✅ Test buffer_clear passed")


def test_handler_initialization():
    """Test: inicializar handler"""
    handler = WebSocketHandler(buffer_size=5)
    
    assert len(handler.active_connections) == 0
    assert handler.latency_buffer.buffer_size == 5
    
    print("✅ Test handler_initialization passed")


def test_handler_stats():
    """Test: obtener estadísticas"""
    handler = WebSocketHandler()
    
    stats = handler.get_stats()
    
    assert 'active_connections' in stats
    assert 'buffer_size' in stats
    assert 'messages_sent' in stats
    assert 'errors' in stats
    
    print("✅ Test handler_stats passed")


def test_handler_buffer_integration():
    """Test: handler usa buffer correctamente"""
    handler = WebSocketHandler(buffer_size=3)
    
    # Simular recepción de datos (sin WebSocket real)
    sensor_data = {'alpha': 180, 'beta': 10, 'gamma': 0}
    handler.latency_buffer.add_sample(sensor_data, time.time() * 1000)
    
    # Obtener datos buffered
    result = handler.get_buffered_sensor_data(use_interpolation=False)
    
    assert result == sensor_data
    
    print("✅ Test handler_buffer_integration passed")


def run_all_tests():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("WEBSOCKET HANDLER - Running Tests")
    print("=" * 60)
    
    try:
        test_buffer_add_and_get()
        test_buffer_size_limit()
        test_buffer_interpolation()
        test_buffer_alpha_wraparound()
        test_buffer_clear()
        test_handler_initialization()
        test_handler_stats()
        test_handler_buffer_integration()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nNOTE: Full WebSocket tests require running server.")
        print("These tests cover buffer logic and handler initialization.")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    run_all_tests()
    
    # Demo
    print("\n" + "=" * 60)
    print("DEMO - WebSocket Handler Usage")
    print("=" * 60)
    
    handler = WebSocketHandler(buffer_size=3)
    print(f"\n{handler}")
    
    # Simular stream de datos
    print("\nSimulating sensor stream:")
    for i in range(5):
        data = {
            'alpha': 180 + i * 10,
            'beta': -10 + i * 2,
            'gamma': 0
        }
        timestamp = time.time() * 1000 + i * 100
        handler.latency_buffer.add_sample(data, timestamp)
        print(f"  Sample {i+1}: {data}")
    
    # Obtener dato interpolado
    interpolated = handler.get_buffered_sensor_data(use_interpolation=True)
    print(f"\nInterpolated result: {interpolated}")
    
    print(f"\nStats: {handler.get_stats()}")
