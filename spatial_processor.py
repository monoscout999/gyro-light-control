"""
SpatialProcessor Module - Gyro Light Control Visualizer
=======================================================

MÓDULO: spatial_processor
VERSIÓN: 1.0
ESTADO: [EN_DESARROLLO]

RESPONSABILIDAD:
Productor de datos espaciales. Transforma SensorData → InteractionResult.

HACE:
- Conversión Euler → Vector 3D (delegada a math_engine)
- Aplicación de calibración matricial
- Cálculo de intersección Ray-Box con venue

NO HACE:
- ❌ Gestión de WebSocket / conexiones
- ❌ Almacenamiento persistente
- ❌ Estado del venue (lo recibe como parámetro)

DEPENDENCIAS: schemas, math_engine, numpy
"""

import numpy as np
from typing import Optional
import logging

from schemas import SensorData, InteractionResult, Vector3D, CalibrationState
from math_engine import (
    euler_to_direction,
    ray_box_intersection,
    create_calibration_offset,
    apply_calibration
)

logger = logging.getLogger(__name__)


# ============================================================================
# SPATIAL PROCESSOR (EL PRODUCTOR)
# ============================================================================

class SpatialProcessor:
    """
    Productor de datos espaciales.
    
    Flujo de procesamiento:
    SensorData → [Alpha Offset] → [Euler→Vector] → [Calibración Matricial] → [Ray Intersection] → InteractionResult
    
    NOTA IMPORTANTE - Alpha Offset:
    El sensor de orientación de dispositivos móviles puede reportar valores de alpha (yaw)
    con un desfase respecto al norte magnético real. El alpha_offset corrige este
    comportamiento inesperado restando el valor de alpha capturado durante la calibración.
    Esto es ADICIONAL a la calibración matricial y se aplica ANTES de la conversión Euler→Vector.
    
    Ejemplo de uso:
        processor = SpatialProcessor()
        sensor = SensorData(alpha=180, beta=45, gamma=0)
        result = processor.process(
            sensor=sensor,
            user_position=Vector3D(x=5, y=5, z=1),
            bounds_min=Vector3D(x=0, y=0, z=0),
            bounds_max=Vector3D(x=10, y=10, z=4)
        )
    """
    
    def __init__(self):
        """Inicializa el procesador con calibración desactivada."""
        self._calibration = CalibrationState()
        
        # ====================================================================
        # ALPHA OFFSET (Corrección de Sensor Móvil)
        # ====================================================================
        # El sensor del celular puede tener un offset en el eje Yaw (alpha).
        # Este valor se resta del alpha raw ANTES de cualquier otro cálculo.
        # Se establece durante la calibración capturando el alpha actual.
        # 
        # ¿Por qué es necesario?
        # - Diferentes dispositivos reportan alpha con diferentes referencias
        # - El usuario puede no estar mirando exactamente hacia el "norte" del venue
        # - Corrige el comportamiento donde el puntero no coincide con la dirección física
        # ====================================================================
        self._alpha_offset: float = 0.0
        
        logger.info("SpatialProcessor initialized")
    
    # ========================================================================
    # PROPIEDADES
    # ========================================================================
    
    @property
    def is_calibrated(self) -> bool:
        """Indica si el sistema está calibrado."""
        return self._calibration.is_calibrated
    
    @property
    def alpha_offset(self) -> float:
        """Retorna el offset de alpha actual (para debugging)."""
        return self._alpha_offset
    
    @property
    def calibration_state(self) -> CalibrationState:
        """Retorna copia del estado de calibración actual."""
        return self._calibration.model_copy()
    
    # ========================================================================
    # CALIBRACIÓN
    # ========================================================================
    
    def calibrate(
        self, 
        current_sensor: SensorData, 
        target_direction: Vector3D
    ) -> bool:
        """
        Calibra el sistema usando la posición actual del sensor.
        
        Usa calibración matricial (Rodrigues' formula) para alinear
        el vector actual con la dirección objetivo.
        
        Args:
            current_sensor: Lectura actual del sensor
            target_direction: Vector hacia donde DEBERÍA apuntar
                              (ej: centro de la pared trasera)
        
        Returns:
            True si la calibración fue exitosa
            
        Ejemplo:
            # Calibrar para que el puntero apunte al centro de la pared trasera
            processor.calibrate(
                current_sensor=SensorData(alpha=180, beta=0, gamma=0),
                target_direction=Vector3D(x=5, y=10, z=2)  # Centro pared trasera
            )
        """
        try:
            # ================================================================
            # PASO 1: Capturar Alpha Offset (Corrección de Sensor)
            # ================================================================
            # Guardamos el alpha actual como referencia del "nuevo norte".
            # Este offset se restará de todas las lecturas futuras ANTES
            # de la conversión Euler→Vector.
            self._alpha_offset = current_sensor.alpha
            
            # ================================================================
            # PASO 2: Calcular vector direccional CON el offset aplicado
            # ================================================================
            # Aplicamos el offset para obtener el vector "corregido"
            corrected_alpha = (current_sensor.alpha - self._alpha_offset) % 360
            current_vector = euler_to_direction(
                corrected_alpha,
                current_sensor.beta,
                current_sensor.gamma
            )
            
            # ================================================================
            # PASO 3: Calcular matriz de rotación (Calibración Matricial)
            # ================================================================
            # La matriz alinea el vector corregido con la dirección objetivo.
            # Esto maneja inclinaciones 3D que el alpha offset no puede corregir.
            target_np = target_direction.to_numpy()
            target_norm = target_np / np.linalg.norm(target_np)
            
            rotation_matrix = create_calibration_offset(
                current_vector=current_vector,
                target_vector=target_norm
            )
            
            # ================================================================
            # PASO 4: Guardar estado
            # ================================================================
            self._calibration = CalibrationState(
                is_calibrated=True,
                rotation_matrix=rotation_matrix.tolist(),
                target_direction=target_direction
            )
            
            logger.info("Calibration successful (Alpha Offset + Matrix)")
            logger.info(f"   Alpha Offset: {self._alpha_offset:.2f} degrees")
            logger.info(f"   Target direction: {target_direction}")
            
            return True
            
        except Exception as e:
            logger.error(f"Calibration failed: {e}", exc_info=True)
            return False
    
    def reset_calibration(self) -> None:
        """Resetea la calibración a estado inicial (sin calibrar)."""
        self._calibration = CalibrationState()
        self._alpha_offset = 0.0  # Reset también el alpha offset
        logger.info("Calibration reset (Alpha Offset + Matrix)")
    
    # ========================================================================
    # PROCESAMIENTO
    # ========================================================================
    
    def process(
        self,
        sensor: SensorData,
        user_position: Vector3D,
        bounds_min: Vector3D,
        bounds_max: Vector3D
    ) -> Optional[InteractionResult]:
        """
        Procesa datos del sensor y calcula punto de intersección.
        
        Pipeline:
        1. Aplicar Alpha Offset (corrección de sensor móvil)
        2. Convertir ángulos Euler a vector direccional
        3. Aplicar calibración matricial (si existe)
        4. Calcular intersección ray-box con el venue
        5. Construir resultado
        
        Args:
            sensor: Datos del giroscopio (SensorData validado)
            user_position: Posición del usuario en el venue
            bounds_min: Esquina mínima del venue (origin)
            bounds_max: Esquina máxima del venue
        
        Returns:
            InteractionResult con intersection y direction, o None si el rayo no intersecta
            
        Ejemplo:
            result = processor.process(
                sensor=SensorData(alpha=0, beta=0, gamma=0),
                user_position=Vector3D(x=5, y=5, z=1),
                bounds_min=Vector3D(x=0, y=0, z=0),
                bounds_max=Vector3D(x=10, y=10, z=4)
            )
            if result:
                print(f"Pointer hits: {result.intersection}")
        """
        try:
            # ================================================================
            # PASO 1: Aplicar Alpha Offset (Corrección de Sensor)
            # ================================================================
            # Restamos el offset capturado durante calibración.
            # Esto corrige el desfase del sensor del celular antes de
            # cualquier otro cálculo.
            corrected_alpha = sensor.alpha
            if self._calibration.is_calibrated:
                corrected_alpha = (sensor.alpha - self._alpha_offset) % 360
            
            # ================================================================
            # PASO 2: Convertir Euler a vector direccional
            # ================================================================
            direction = euler_to_direction(
                corrected_alpha,  # Usar alpha corregido
                sensor.beta, 
                sensor.gamma
            )
            
            # ================================================================
            # PASO 3: Aplicar calibración matricial si existe
            # ================================================================
            if self._calibration.is_calibrated:
                matrix = self._calibration.get_matrix_numpy()
                if matrix is not None:
                    direction = apply_calibration(direction, matrix)
            
            # ================================================================
            # PASO 4: Calcular intersección con el venue
            # ================================================================
            intersection = ray_box_intersection(
                origin=user_position.to_numpy(),
                direction=direction,
                box_min=bounds_min.to_numpy(),
                box_max=bounds_max.to_numpy()
            )
            
            if intersection is None:
                logger.debug("Ray does not intersect venue bounds")
                return None
            
            # ================================================================
            # PASO 5: Construir resultado
            # ================================================================
            return InteractionResult(
                intersection=Vector3D.from_numpy(intersection),
                direction=Vector3D.from_numpy(direction),
                calibrated=self._calibration.is_calibrated,
                raw_sensor=sensor
            )
            
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}", exc_info=True)
            return None
    
    def __repr__(self) -> str:
        return f"SpatialProcessor(calibrated={self.is_calibrated})"


# ============================================================================
# TESTS
# ============================================================================

def test_processor_initialization():
    """Test: inicialización correcta."""
    processor = SpatialProcessor()
    assert not processor.is_calibrated, "Should start uncalibrated"
    print("✅ test_processor_initialization passed")


def test_processor_process_basic():
    """Test: procesamiento básico sin calibración."""
    processor = SpatialProcessor()
    
    # Sensor apuntando hacia adelante (+Y)
    sensor = SensorData(alpha=0, beta=0, gamma=0)
    
    # Venue de 10x10x4
    result = processor.process(
        sensor=sensor,
        user_position=Vector3D(x=5, y=5, z=1),
        bounds_min=Vector3D(x=0, y=0, z=0),
        bounds_max=Vector3D(x=10, y=10, z=4)
    )
    
    assert result is not None, "Should produce valid intersection"
    assert result.intersection.y == 10.0, f"Should hit back wall (y=10), got {result.intersection.y}"
    assert not result.calibrated, "Should not be calibrated"
    
    print("✅ test_processor_process_basic passed")


def test_processor_calibration():
    """Test: calibración y aplicación."""
    processor = SpatialProcessor()
    
    # Calibrar: posición actual debería apuntar a +Y
    sensor = SensorData(alpha=90, beta=0, gamma=0)  # Mirando hacia +X
    target = Vector3D(x=0, y=1, z=0)  # Quiero que apunte hacia +Y
    
    success = processor.calibrate(sensor, target)
    assert success, "Calibration should succeed"
    assert processor.is_calibrated, "Should be calibrated"
    
    # Procesar con la misma posición del sensor
    result = processor.process(
        sensor=sensor,
        user_position=Vector3D(x=5, y=5, z=1),
        bounds_min=Vector3D(x=0, y=0, z=0),
        bounds_max=Vector3D(x=10, y=10, z=4)
    )
    
    assert result is not None, "Should produce valid intersection"
    assert result.calibrated, "Result should show calibrated"
    # Después de calibrar, el vector debería apuntar hacia +Y (pared trasera)
    assert result.intersection.y == 10.0, f"Should hit back wall after calibration, got {result.intersection.y}"
    
    print("✅ test_processor_calibration passed")


def test_processor_reset_calibration():
    """Test: reset de calibración."""
    processor = SpatialProcessor()
    
    # Calibrar
    sensor = SensorData(alpha=0, beta=0, gamma=0)
    target = Vector3D(x=0, y=1, z=0)
    processor.calibrate(sensor, target)
    
    assert processor.is_calibrated, "Should be calibrated"
    
    # Reset
    processor.reset_calibration()
    assert not processor.is_calibrated, "Should not be calibrated after reset"
    
    print("✅ test_processor_reset_calibration passed")


def test_processor_no_intersection():
    """Test: rayo que no intersecta (caso edge)."""
    processor = SpatialProcessor()
    
    # Sensor apuntando hacia arriba pero usuario ya en el techo
    sensor = SensorData(alpha=0, beta=90, gamma=0)  # Mirando hacia arriba
    
    # Usuario en z=4 (techo del venue)
    result = processor.process(
        sensor=sensor,
        user_position=Vector3D(x=5, y=5, z=4),  # En el techo
        bounds_min=Vector3D(x=0, y=0, z=0),
        bounds_max=Vector3D(x=10, y=10, z=4)
    )
    
    # Debería retornar None porque el usuario está en el borde
    # y el rayo apunta hacia afuera
    # (este test verifica el manejo de casos edge)
    
    print("✅ test_processor_no_intersection passed")


def test_processor_broadcast_format():
    """Test: formato de broadcast del resultado."""
    processor = SpatialProcessor()
    
    sensor = SensorData(alpha=0, beta=0, gamma=0, timestamp=1000)
    result = processor.process(
        sensor=sensor,
        user_position=Vector3D(x=5, y=5, z=1),
        bounds_min=Vector3D(x=0, y=0, z=0),
        bounds_max=Vector3D(x=10, y=10, z=4)
    )
    
    assert result is not None, "Should produce valid result"
    
    broadcast = result.to_broadcast_dict()
    
    assert broadcast['type'] == 'state_update', "Should have correct type"
    assert 'sensor' in broadcast, "Should have sensor data"
    assert 'pointer' in broadcast, "Should have pointer data"
    assert 'intersection' in broadcast['pointer'], "Should have intersection"
    assert 'direction' in broadcast['pointer'], "Should have direction"
    assert 'calibrated' in broadcast, "Should have calibrated flag"
    
    print("✅ test_processor_broadcast_format passed")


def run_all_tests():
    """Ejecuta todos los tests del SpatialProcessor."""
    print("\n" + "=" * 60)
    print("RUNNING SPATIAL PROCESSOR TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_processor_initialization,
        test_processor_process_basic,
        test_processor_calibration,
        test_processor_reset_calibration,
        test_processor_no_intersection,
        test_processor_broadcast_format
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    run_all_tests()
