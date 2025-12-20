"""
Schemas Module - Gyro Control
==============================

MÓDULO: schemas
VERSIÓN: 2.0
ESTADO: [VALIDADO]

RESPONSABILIDAD:
Contratos de datos (Input/Output) para interacción espacial usando Pydantic V2.

HACE:
- Validación estricta de datos del sensor (SensorData)
- Estructura inmutable para vectores 3D (Vector3D)
- Resultado de procesamiento espacial (InteractionResult)
- Estado de calibración (CalibrationState)

NO HACE:
- ❌ Cálculos matemáticos
- ❌ Comunicación de red
- ❌ Estado mutable  

DEPENDENCIAS: pydantic, numpy
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import numpy as np


# ============================================================================
# VECTOR 3D
# ============================================================================

class Vector3D(BaseModel):
    """
    Vector 3D inmutable para coordenadas espaciales.
    
    Sistema de coordenadas Z-UP:
    - X: Ancho (Este/Oeste)
    - Y: Profundidad (Norte/Sur)
    - Z: Altura (Arriba/Abajo)
    """
    x: float
    y: float
    z: float
    
    def to_numpy(self) -> np.ndarray:
        """Convierte a numpy array [x, y, z]."""
        return np.array([self.x, self.y, self.z])
    
    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> "Vector3D":
        """Crea Vector3D desde numpy array."""
        return cls(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))
    
    def to_list(self) -> list[float]:
        """Convierte a lista [x, y, z] para JSON."""
        return [self.x, self.y, self.z]
    
    def __repr__(self) -> str:
        return f"Vector3D({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


# ============================================================================
# SENSOR DATA (INPUT)
# ============================================================================

class SensorData(BaseModel):
    """
    Datos de entrada del giroscopio/acelerómetro.
    
    Provienen del evento DeviceOrientationEvent del navegador móvil.
    """
    alpha: float = Field(
        ..., 
        ge=0, 
        le=360, 
        description="Yaw/Compass rotation around Z axis (0-360°)"
    )
    beta: float = Field(
        ..., 
        ge=-180, 
        le=180, 
        description="Pitch rotation around X axis (-180 to 180°)"
    )
    gamma: float = Field(
        ..., 
        ge=-90, 
        le=90, 
        description="Roll rotation around Y axis (-90 to 90°)"
    )
    timestamp: Optional[float] = Field(
        default=None, 
        description="Timestamp en milisegundos para sincronización"
    )
    
    @field_validator('alpha', 'beta', 'gamma', mode='before')
    @classmethod
    def coerce_to_float(cls, v):
        """Asegura que los valores sean floats válidos."""
        if v is None:
            raise ValueError("Sensor values cannot be None")
        return float(v)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"alpha": 180.0, "beta": 45.0, "gamma": 0.0, "timestamp": 1703073600000}
            ]
        }
    }


# ============================================================================
# CALIBRATION STATE
# ============================================================================

class CalibrationState(BaseModel):
    """
    Estado de calibración del sistema.
    
    Utiliza calibración matricial (Rodrigues' formula) para
    alinear el vector del sensor con la dirección objetivo.
    """
    is_calibrated: bool = False
    rotation_matrix: Optional[list[list[float]]] = Field(
        default=None,
        description="Matriz de rotación 3x3 para calibración"
    )
    target_direction: Optional[Vector3D] = Field(
        default=None,
        description="Vector objetivo de la calibración"
    )
    
    def get_matrix_numpy(self) -> Optional[np.ndarray]:
        """Retorna la matriz de rotación como numpy array 3x3."""
        if self.rotation_matrix is None:
            return None
        return np.array(self.rotation_matrix)
    
    model_config = {
        "arbitrary_types_allowed": True
    }


# ============================================================================
# INTERACTION RESULT (OUTPUT)
# ============================================================================

class InteractionResult(BaseModel):
    """
    Resultado del procesamiento espacial (Output del SpatialProcessor).
    
    Contiene toda la información necesaria para visualización y broadcast.
    """
    intersection: Vector3D = Field(
        ...,
        description="Punto donde el rayo intersecta el venue [x, y, z]"
    )
    direction: Vector3D = Field(
        ...,
        description="Vector direccional normalizado del puntero"
    )
    calibrated: bool = Field(
        ...,
        description="Indica si el sistema está calibrado"
    )
    raw_sensor: SensorData = Field(
        ...,
        description="Datos originales del sensor (echo para validación)"
    )
    
    def to_broadcast_dict(self) -> dict:
        """
        Convierte a formato de broadcast para WebSocket.
        
        Returns:
            Dict compatible con el protocolo existente
        """
        return {
            'type': 'state_update',
            'sensor': {
                'alpha': self.raw_sensor.alpha,
                'beta': self.raw_sensor.beta,
                'gamma': self.raw_sensor.gamma,
                'timestamp': self.raw_sensor.timestamp
            },
            'pointer': {
                'direction': self.direction.to_list(),
                'intersection': self.intersection.to_list()
            },
            'calibrated': self.calibrated
        }
    
    model_config = {
        "arbitrary_types_allowed": True
    }


# ============================================================================
# TESTS
# ============================================================================

def test_vector3d_conversion():
    """Test: conversión Vector3D ↔ numpy."""
    v = Vector3D(x=1.0, y=2.0, z=3.0)
    arr = v.to_numpy()
    assert arr.shape == (3,), "Should be 3D array"
    assert list(arr) == [1.0, 2.0, 3.0], "Values should match"
    
    v2 = Vector3D.from_numpy(arr)
    assert v2.x == v.x and v2.y == v.y and v2.z == v.z, "Roundtrip should match"
    print("✅ test_vector3d_conversion passed")


def test_sensor_data_validation():
    """Test: validación de SensorData."""
    # Caso válido
    sensor = SensorData(alpha=180, beta=45, gamma=0)
    assert sensor.alpha == 180.0, "Should coerce to float"
    
    # Caso inválido: alpha fuera de rango
    try:
        SensorData(alpha=400, beta=0, gamma=0)
        assert False, "Should have raised validation error"
    except ValueError:
        pass
    
    # Caso inválido: beta fuera de rango
    try:
        SensorData(alpha=0, beta=200, gamma=0)
        assert False, "Should have raised validation error"
    except ValueError:
        pass
    
    print("✅ test_sensor_data_validation passed")


def test_calibration_state():
    """Test: CalibrationState con matriz."""
    # Estado inicial
    cal = CalibrationState()
    assert not cal.is_calibrated, "Should start uncalibrated"
    assert cal.get_matrix_numpy() is None, "No matrix initially"
    
    # Con matriz
    matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    cal2 = CalibrationState(
        is_calibrated=True,
        rotation_matrix=matrix,
        target_direction=Vector3D(x=0, y=1, z=0)
    )
    arr = cal2.get_matrix_numpy()
    assert arr is not None, "Should have matrix"
    assert arr.shape == (3, 3), "Should be 3x3"
    
    print("✅ test_calibration_state passed")


def test_interaction_result_broadcast():
    """Test: InteractionResult.to_broadcast_dict()."""
    result = InteractionResult(
        intersection=Vector3D(x=5, y=10, z=2),
        direction=Vector3D(x=0, y=1, z=0),
        calibrated=True,
        raw_sensor=SensorData(alpha=0, beta=0, gamma=0)
    )
    
    broadcast = result.to_broadcast_dict()
    assert broadcast['type'] == 'state_update', "Should have correct type"
    assert broadcast['pointer']['intersection'] == [5, 10, 2], "Intersection should match"
    assert broadcast['calibrated'] is True, "Should be calibrated"
    
    print("✅ test_interaction_result_broadcast passed")


def run_all_tests():
    """Ejecuta todos los tests de schemas."""
    print("\n" + "=" * 60)
    print("RUNNING SCHEMAS TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_vector3d_conversion,
        test_sensor_data_validation,
        test_calibration_state,
        test_interaction_result_broadcast
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    run_all_tests()
