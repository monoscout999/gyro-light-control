"""
Math Engine Module - Gyro Light Control Visualizer
===================================================

MÓDULO: math_engine
VERSIÓN: 1.0
ESTADO: [VALIDADO] ✅

RESPONSABILIDAD:
Todas las operaciones matemáticas del sistema de puntero 3D y control de fixtures.

NO HACE:
- ❌ Comunicación de red
- ❌ Renderizado 3D
- ❌ Gestión de estado
- ❌ Interacción con UI

DEPENDENCIAS: NumPy únicamente
"""

import numpy as np
from typing import Tuple, Optional


# ============================================================================
# CONVERSIÓN GIROSCOPIO → VECTOR 3D
# ============================================================================

def euler_to_direction(
    alpha: float, 
    beta: float, 
    gamma: float
) -> np.ndarray:
    """
    Convierte ángulos Euler del sensor a vector direccional 3D.
    
    Args:
        alpha: 0-360° compass/yaw (rotación Z)
        beta: -180 a 180° pitch (rotación X)  
        gamma: -90 a 90° roll (rotación Y)
        
    Returns:
        Vector normalizado [x, y, z] como numpy array
        
    Notas:
    - Asume que celular tiene pantalla hacia arriba (sky)
    - En estado sin calibrar, alpha=0 apunta a +Y (norte)
    - Beta positivo = celular inclinado hacia arriba
    - Gamma es corrección de roll (usualmente pequeño)
    
    Sistema de coordenadas:
    - X: Este (+) / Oeste (-)
    - Y: Norte (+) / Sur (-)
    - Z: Arriba (+) / Abajo (-)
    """
    # Convertir grados a radianes
    alpha_rad = np.radians(-alpha) # se agrego por USUARIO un signo menos para corregir comportamiento avisar en caso de querer modificar
    beta_rad = np.radians(beta)
    # gamma no se usa en la versión simplificada
    
    # Calcular componentes del vector
    # x = sin(alpha) * cos(beta)  -> Componente Este-Oeste
    # y = cos(alpha) * cos(beta)  -> Componente Norte-Sur
    # z = sin(beta)                -> Componente vertical
    x = np.sin(alpha_rad) * np.cos(beta_rad)
    y = np.cos(alpha_rad) * np.cos(beta_rad)
    z = np.sin(beta_rad)
    
    # Crear vector y normalizar
    vector = np.array([x, y, z])
    return normalize_vector(vector)


# ============================================================================
# SISTEMA DE CALIBRACIÓN
# ============================================================================

def create_calibration_offset(
    current_vector: np.ndarray,
    target_vector: np.ndarray
) -> np.ndarray:
    """
    Calcula matriz de rotación para alinear vector actual con target.
    
    Args:
        current_vector: Dirección donde apunta el celular ahora
        target_vector: Dirección donde DEBERÍA apuntar (centro pared trasera)
        
    Returns:
        Matriz 3x3 de rotación como numpy array
        
    Proceso:
    1. Calcular eje de rotación: cross(current, target)
    2. Calcular ángulo de rotación: arccos(dot(current, target))
    3. Construir matriz de rotación (Rodrigues' formula)
    
    Casos especiales:
    - Si current == target → retornar matriz identidad
    - Si current == -target → rotación 180° (elegir eje arbitrario)
    """
    # Normalizar ambos vectores
    current = normalize_vector(current_vector)
    target = normalize_vector(target_vector)
    
    # Calcular producto punto
    dot_product = np.dot(current, target)
    
    # Caso 1: Vectores ya alineados (dot ≈ 1)
    if dot_product > 0.9999:
        return np.eye(3)
    
    # Caso 2: Vectores opuestos (dot ≈ -1)
    if dot_product < -0.9999:
        # Encontrar un eje perpendicular arbitrario
        # Probamos con el eje Z primero, si no funciona usamos X
        arbitrary_axis = np.array([0, 0, 1])
        if abs(np.dot(current, arbitrary_axis)) > 0.9:
            arbitrary_axis = np.array([1, 0, 0])
        
        axis = np.cross(current, arbitrary_axis)
        axis = normalize_vector(axis)
        angle = np.pi  # 180 grados
    else:
        # Caso normal: calcular eje y ángulo
        axis = np.cross(current, target)
        axis = normalize_vector(axis)
        angle = np.arccos(np.clip(dot_product, -1.0, 1.0))
    
    # Construir matriz de rotación usando Rodrigues' formula
    # R = I + sin(θ)K + (1-cos(θ))K²
    # donde K es la matriz antisimétrica del eje de rotación
    
    K = np.array([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])
    
    I = np.eye(3)
    R = I + np.sin(angle) * K + (1 - np.cos(angle)) * np.dot(K, K)
    
    return R


def apply_calibration(
    vector: np.ndarray,
    rotation_matrix: np.ndarray
) -> np.ndarray:
    """
    Aplica matriz de calibración a un vector sin calibrar.
    
    Args:
        vector: Vector direccional sin calibrar
        rotation_matrix: Matriz de calibración (3x3)
        
    Returns:
        Vector calibrado y normalizado
        
    Implementación:
    - Multiplicar: rotation_matrix @ vector
    - Normalizar resultado (por si acumuló error numérico)
    """
    # Aplicar rotación
    calibrated = rotation_matrix @ vector
    
    # Normalizar para corregir errores numéricos acumulados
    return normalize_vector(calibrated)


# ============================================================================
# GEOMETRÍA - INTERSECCIONES
# ============================================================================

def ray_box_intersection(
    origin: np.ndarray,
    direction: np.ndarray,
    box_min: np.ndarray,
    box_max: np.ndarray
) -> Optional[np.ndarray]:
    """
    Calcula dónde un rayo intersecta con una caja axis-aligned.
    
    Args:
        origin: Punto de origen del rayo [x, y, z]
        direction: Dirección normalizada del rayo [x, y, z]
        box_min: Esquina mínima de la caja [x, y, z]
        box_max: Esquina máxima de la caja [x, y, z]
        
    Returns:
        Punto de intersección [x, y, z] o None si no hay intersección
        
    Algoritmo (slab method):
    1. Para cada eje (X, Y, Z):
       - Calcular t_min = (box_min[i] - origin[i]) / direction[i]
       - Calcular t_max = (box_max[i] - origin[i]) / direction[i]
       - Si direction[i] ≈ 0, manejar caso especial
    2. t_near = max(todos los t_min)
    3. t_far = min(todos los t_max)
    4. Si t_near > t_far → sin intersección
    5. Si t_far < 0 → rayo apunta en dirección opuesta
    6. Retornar: origin + direction * t_near (o t_far si t_near < 0)
    
    Caso uso:
    - origin = posición usuario (5, 5, 1)
    - direction = vector del giroscopio calibrado
    - box_min = (0, 0, 0)
    - box_max = (10, 10, 4)
    - Retorna: dónde el puntero toca pared/piso/techo del venue
    """
    # Normalizar dirección
    direction = normalize_vector(direction)
    
    # Inicializar t_near y t_far
    t_near = -np.inf
    t_far = np.inf
    
    # Iterar sobre cada eje (x, y, z)
    for i in range(3):
        if abs(direction[i]) < 1e-8:
            # Rayo paralelo a este plano
            # Verificar si el origen está dentro del rango
            if origin[i] < box_min[i] or origin[i] > box_max[i]:
                return None  # No hay intersección
        else:
            # Calcular t para ambos planos
            t1 = (box_min[i] - origin[i]) / direction[i]
            t2 = (box_max[i] - origin[i]) / direction[i]
            
            # Asegurar que t1 <= t2
            if t1 > t2:
                t1, t2 = t2, t1
            
            # Actualizar t_near y t_far
            t_near = max(t_near, t1)
            t_far = min(t_far, t2)
            
            # Verificar si hay intersección
            if t_near > t_far:
                return None  # No hay intersección
    
    # Si t_far < 0, la caja está completamente detrás del rayo
    if t_far < 0:
        return None
    
    # Elegir el t apropiado
    # Si t_near < 0, el origen está dentro de la caja, usar t_far
    # Si no, usar t_near
    t = t_near if t_near >= 0 else t_far
    
    # Calcular punto de intersección
    intersection_point = origin + direction * t
    
    return intersection_point


# ============================================================================
# CÁLCULOS DE FIXTURE
# ============================================================================

def calculate_fixture_pan_tilt(
    fixture_position: np.ndarray,
    target_position: np.ndarray,
    mounting: str = "ceiling",
    pan_invert: bool = False,
    tilt_invert: bool = False
) -> Tuple[float, float]:
    """
    Calcula ángulos pan/tilt para que fixture apunte a target.
    
    Args:
        fixture_position: Posición del fixture [x, y, z]
        target_position: Posición objetivo (donde está el pointer) [x, y, z]
        mounting: "ceiling", "floor", o "wall" (orientación del fixture)
        pan_invert: Si True, invierte pan (left↔right)
        tilt_invert: Si True, invierte tilt (up↔down)
        
    Returns:
        Tupla (pan_grados, tilt_grados)
        - pan: -270 a 270° (rotación horizontal)
        - tilt: -135 a 135° (rotación vertical)
        
    Proceso:
    1. Calcular vector: target - fixture
    2. Aplicar transformación según mounting:
       - "ceiling": fixture cuelga boca abajo
       - "floor": fixture para arriba desde piso
       - "wall": fixture montado horizontal
    3. Calcular pan = atan2(x_component, y_component)
    4. Calcular tilt = atan2(z_component, xy_magnitude)
    5. Convertir radianes → grados
    6. Aplicar inversiones si corresponde
    7. Retornar (pan, tilt)
    
    Nota mounting:
    - Por ahora implementa solo "ceiling" (más común)
    - Los otros modos son para futuro
    """
    # Calcular vector desde fixture hacia target
    vector = target_position - fixture_position
    
    # Extraer componentes
    dx = vector[0]
    dy = vector[1]
    dz = vector[2]
    
    if mounting == "ceiling":
        # Fixture colgado del techo, apuntando hacia abajo por defecto
        # Pan: rotación en el plano XY
        # Para ceiling mounted fixture:
        # - pan=0° apunta hacia -Y (sur, hacia el frente del venue)
        # - pan positivo = rotación hacia +X (este/derecha)
        # - pan negativo = rotación hacia -X (oeste/izquierda)
        
        # Invertir dy porque fixture desde el techo mira hacia -Y como "forward"
        pan_rad = np.arctan2(dx, -dy)
        
        # Tilt: ángulo vertical
        # Calcular magnitud en plano horizontal
        xy_magnitude = np.sqrt(dx**2 + dy**2)
        
        # Para ceiling:
        # - Si target está abajo del fixture (dz negativo) → tilt negativo
        # - Si target está arriba del fixture (dz positivo) → tilt positivo
        # - tilt = 0° significa horizontal
        tilt_rad = np.arctan2(dz, xy_magnitude)
        
    elif mounting == "floor":
        # Fixture en el piso, apuntando hacia arriba por defecto
        pan_rad = np.arctan2(dx, dy)
        xy_magnitude = np.sqrt(dx**2 + dy**2)
        tilt_rad = np.arctan2(dz, xy_magnitude)
        
    elif mounting == "wall":
        # Fixture en pared (implementación simplificada)
        # Se asume montado en pared mirando hacia el interior
        pan_rad = np.arctan2(dx, dy)
        xy_magnitude = np.sqrt(dx**2 + dy**2)
        tilt_rad = np.arctan2(dz, xy_magnitude)
    else:
        # Default a ceiling
        pan_rad = np.arctan2(dx, dy)
        xy_magnitude = np.sqrt(dx**2 + dy**2)
        tilt_rad = np.arctan2(-dz, xy_magnitude)
    
    # Convertir a grados
    pan_deg = np.degrees(pan_rad)
    tilt_deg = np.degrees(tilt_rad)
    
    # Aplicar inversiones si corresponde
    if pan_invert:
        pan_deg = -pan_deg
    
    if tilt_invert:
        tilt_deg = -tilt_deg
    
    return (pan_deg, tilt_deg)


# ============================================================================
# UTILIDADES
# ============================================================================

def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """Normaliza un vector a longitud 1.0"""
    magnitude = np.linalg.norm(vector)
    if magnitude < 1e-10:
        return np.array([0, 1, 0])  # Default: hacia adelante
    return vector / magnitude


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Limita un valor entre min y max"""
    return max(min_val, min(value, max_val))


# ============================================================================
# TESTS (incluir en el mismo archivo por ahora)
# ============================================================================

def test_euler_forward():
    """Test: apuntar hacia adelante (+Y)"""
    vector = euler_to_direction(0, 0, 0)
    expected = np.array([0, 1, 0])
    assert np.allclose(vector, expected, atol=0.01), \
        f"Expected {expected}, got {vector}"
    print("✅ Test euler_forward passed")


def test_euler_up():
    """Test: apuntar hacia arriba (+Z)"""
    vector = euler_to_direction(0, 90, 0)
    expected = np.array([0, 0, 1])
    assert np.allclose(vector, expected, atol=0.01), \
        f"Expected {expected}, got {vector}"
    print("✅ Test euler_up passed")


def test_euler_right():
    """Test: apuntar hacia derecha (+X)"""
    vector = euler_to_direction(90, 0, 0)
    expected = np.array([-1, 0, 0])
    assert np.allclose(vector, expected, atol=0.01), \
        f"Expected {expected}, got {vector}"
    print("✅ Test euler_right passed")


def test_calibration_identity():
    """Test: calibración con mismo vector (sin rotación)"""
    v = np.array([0, 1, 0])
    R = create_calibration_offset(v, v)
    assert np.allclose(R, np.eye(3), atol=0.01), \
        "Identity calibration should return identity matrix"
    print("✅ Test calibration_identity passed")


def test_calibration_90deg():
    """Test: calibración 90° de X a Y"""
    current = np.array([1, 0, 0])
    target = np.array([0, 1, 0])
    R = create_calibration_offset(current, target)
    result = apply_calibration(current, R)
    assert np.allclose(result, target, atol=0.01), \
        f"90° rotation failed: got {result}"
    print("✅ Test calibration_90deg passed")


def test_ray_hits_back_wall():
    """Test: rayo desde centro hacia pared trasera"""
    origin = np.array([5, 5, 1])
    direction = np.array([0, 1, 0])  # Hacia +Y
    box_min = np.array([0, 0, 0])
    box_max = np.array([10, 10, 4])
    
    hit = ray_box_intersection(origin, direction, box_min, box_max)
    
    assert hit is not None, "Ray should hit back wall"
    assert np.allclose(hit[1], 10, atol=0.01), \
        f"Should hit Y=10, got Y={hit[1]}"
    assert np.allclose(hit[0], 5, atol=0.01), \
        f"Should maintain X=5, got X={hit[0]}"
    print("✅ Test ray_hits_back_wall passed")


def test_ray_hits_floor():
    """Test: rayo hacia abajo toca piso"""
    origin = np.array([5, 5, 2])
    direction = np.array([0, 0, -1])  # Hacia -Z
    box_min = np.array([0, 0, 0])
    box_max = np.array([10, 10, 4])
    
    hit = ray_box_intersection(origin, direction, box_min, box_max)
    
    assert hit is not None, "Ray should hit floor"
    assert np.allclose(hit[2], 0, atol=0.01), \
        f"Should hit Z=0, got Z={hit[2]}"
    print("✅ Test ray_hits_floor passed")


def test_fixture_pan_tilt_centered():
    """Test: fixture en techo apuntando al centro"""
    fixture_pos = np.array([5, 9, 3.5])  # Techo, cerca pared trasera
    target_pos = np.array([5, 5, 1])     # Centro venue
    
    pan, tilt = calculate_fixture_pan_tilt(fixture_pos, target_pos, "ceiling")
    
    # Pan debería ser ~0° (centrado en X)
    # Tilt debería ser negativo (apuntando abajo)
    assert abs(pan) < 5, f"Pan should be near 0°, got {pan}°"
    assert tilt < 0, f"Tilt should be negative (down), got {tilt}°"
    print("✅ Test fixture_pan_tilt_centered passed")


def run_all_tests():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("MATH ENGINE - Running Tests")
    print("=" * 60)
    
    try:
        test_euler_forward()
        test_euler_up()
        test_euler_right()
        test_calibration_identity()
        test_calibration_90deg()
        test_ray_hits_back_wall()
        test_ray_hits_floor()
        test_fixture_pan_tilt_centered()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    run_all_tests()
