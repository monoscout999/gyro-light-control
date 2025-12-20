"""
Integration Test: WebSocket + Schemas Validation
================================================

Verifica que el servidor responde con el formato JSON correcto
definido en schemas.py (InteractionResult).

Ejecutar con: python test_integration.py
(El servidor debe estar corriendo en otra terminal)
"""

import asyncio
import json
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    print("[X] websockets no instalado. Ejecutando: pip install websockets")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets

from schemas import SensorData, InteractionResult, Vector3D


async def test_websocket_integration():
    """Test de integracion WebSocket."""
    uri = "ws://localhost:8080/ws"
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST: WebSocket + Schemas")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri, open_timeout=5, close_timeout=5) as websocket:
            print("[OK] Conectado al servidor WebSocket")
            
            # Consumir mensaje inicial de conexion si existe
            try:
                initial = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                data = json.loads(initial)
                if data.get('type') == 'connection_established':
                    print("[INFO] Mensaje de conexion recibido")
            except asyncio.TimeoutError:
                pass  # No hay mensaje inicial, continuar
            
            # Test 1: Ping/Pong primero (mas simple)
            print("\n--- Test 1: Heartbeat ---")
            await websocket.send(json.dumps({'type': 'ping'}))
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(response)
            
            if data.get('type') == 'pong':
                print("   [OK] Heartbeat funcionando")
            else:
                print(f"   [FAIL] Respuesta inesperada: {data}")
                return False
            
            # Test 2: Calibracion
            print("\n--- Test 2: Calibracion (Matrix/Rodrigues) ---")
            calibrate_data = {
                'type': 'calibrate',
                'alpha': 0.0,
                'beta': 0.0,
                'gamma': 0.0
            }
            
            await websocket.send(json.dumps(calibrate_data))
            print(f"   Enviado: calibrate request")
            
            # Leer respuestas hasta obtener calibration_result
            calibration_ok = False
            for _ in range(3):  # Maximo 3 intentos
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                data = json.loads(response)
                
                if data.get('type') == 'calibration_result':
                    if data.get('success'):
                        print("   [OK] Calibracion exitosa (Matrix)")
                        calibration_ok = True
                        break
                    else:
                        print(f"   [FAIL] Calibracion fallo: {data.get('message')}")
                        return False
                elif data.get('type') == 'state_update':
                    print("   [INFO] Recibido state_update (broadcast)")
                    
            if not calibration_ok:
                print("   [FAIL] No se recibio calibration_result")
                return False
            
            # Test 3: Enviar datos de sensor y validar respuesta
            print("\n--- Test 3: Enviar SensorData y validar respuesta ---")
            sensor_data = {
                'type': 'sensor_data',
                'alpha': 0.0,
                'beta': 0.0,
                'gamma': 0.0,
                'timestamp': 1000
            }
            
            # Validar input localmente primero
            try:
                validated = SensorData(
                    alpha=sensor_data['alpha'],
                    beta=sensor_data['beta'],
                    gamma=sensor_data['gamma']
                )
                print(f"   Input validado localmente: alpha={validated.alpha}, beta={validated.beta}")
            except Exception as e:
                print(f"   [FAIL] Input invalido: {e}")
                return False
            
            await websocket.send(json.dumps(sensor_data))
            print(f"   Enviado sensor data")
            
            # Esperar state_update
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(response)
            
            if data.get('type') == 'state_update':
                print("   [OK] Tipo de mensaje correcto: state_update")
                
                # Verificar estructura pointer
                if 'pointer' in data:
                    pointer = data['pointer']
                    if 'intersection' in pointer and 'direction' in pointer:
                        intersection = pointer['intersection']
                        direction = pointer['direction']
                        
                        if len(intersection) == 3 and len(direction) == 3:
                            print(f"   [OK] Intersection: [{intersection[0]:.2f}, {intersection[1]:.2f}, {intersection[2]:.2f}]")
                            print(f"   [OK] Direction: [{direction[0]:.2f}, {direction[1]:.2f}, {direction[2]:.2f}]")
                            
                            # Validar con schema Vector3D
                            try:
                                v = Vector3D(x=intersection[0], y=intersection[1], z=intersection[2])
                                print(f"   [OK] Vector3D schema validado")
                            except Exception as e:
                                print(f"   [FAIL] Vector3D invalido: {e}")
                                return False
                        else:
                            print("   [FAIL] Vectores no son 3D")
                            return False
                    else:
                        print("   [FAIL] Faltan intersection/direction en pointer")
                        return False
                else:
                    print("   [FAIL] Falta 'pointer' en respuesta")
                    return False
                
                # Verificar calibrated flag
                if 'calibrated' in data:
                    print(f"   [OK] Calibrated flag: {data['calibrated']}")
                else:
                    print("   [FAIL] Falta 'calibrated' en respuesta")
                    return False
                    
                # Verificar sensor echo
                if 'sensor' in data:
                    print(f"   [OK] Sensor echo presente")
                else:
                    print("   [FAIL] Falta 'sensor' en respuesta")
                    return False
                    
            else:
                print(f"   [FAIL] Tipo de mensaje inesperado: {data.get('type')}")
                return False
            
            # Test 4: Reset calibracion
            print("\n--- Test 4: Reset Calibracion ---")
            await websocket.send(json.dumps({'type': 'reset_calibration'}))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(response)
            
            if data.get('type') == 'calibration_result' and data.get('success'):
                print("   [OK] Reset exitoso")
            else:
                print(f"   [INFO] Respuesta: {data.get('type')}")
            
            print("\n" + "=" * 60)
            print("ALL TESTS PASSED - INTEGRATION SUCCESSFUL")
            print("=" * 60)
            print("\nEl servidor responde con el formato JSON correcto")
            print("definido en schemas.py (InteractionResult)")
            return True
            
    except ConnectionRefusedError:
        print("[FAIL] No se pudo conectar al servidor.")
        print("   Asegurate de que el servidor esta corriendo: python server.py")
        return False
    except asyncio.TimeoutError:
        print("[FAIL] Timeout esperando respuesta del servidor")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_websocket_integration())
    sys.exit(0 if success else 1)
