# PROMPT: Implementar fixture_manager.py - Gestor de Fixtures (Luces Móviles)

## CONTEXTO DEL PROYECTO

Estás implementando el gestor de fixtures (luces móviles) para un sistema de control de iluminación. Este módulo gestiona el estado de cada fixture, calcula sus ángulos pan/tilt para seguir el pointer, y maneja presets/serialización.

Este módulo **USA math_engine.py** que ya está validado, específicamente la función `calculate_fixture_pan_tilt()`.

---

## TU TAREA

Crear el archivo `fixture_manager.py` que gestione:
- CRUD de fixtures (crear, leer, actualizar, eliminar)
- Tracking automático del pointer (calcular pan/tilt)
- Presets de fixtures comunes (JSON)
- Serialización para save/load de escenas
- Validación de configuraciones

---

## ESPECIFICACIONES TÉCNICAS

### Datos de un Fixture

Cada fixture tiene:
- **ID único**: UUID generado automáticamente
- **Nombre**: String descriptivo (ej: "Moving Head 1")
- **Posición**: (x, y, z) en metros dentro del venue
- **Mounting**: "ceiling", "floor", "wall" (cómo está montado)
- **Pan range**: (min, max) en grados (ej: -270, 270)
- **Tilt range**: (min, max) en grados (ej: -135, 135)
- **Pan invert**: Boolean (invertir dirección pan)
- **Tilt invert**: Boolean (invertir dirección tilt)
- **Pan actual**: Grados actuales (calculados, no editables)
- **Tilt actual**: Grados actuales (calculados, no editables)

### Presets Comunes (Built-in)

```python
FIXTURE_PRESETS = {
    "Generic Moving Head": {
        "pan_range": (-270, 270),
        "tilt_range": (-135, 135),
        "mounting": "ceiling"
    },
    "Generic LED Par": {
        "pan_range": (0, 0),      # Sin pan (luz fija)
        "tilt_range": (-90, 90),
        "mounting": "floor"
    },
    "Generic Wash Light": {
        "pan_range": (-180, 180),
        "tilt_range": (-110, 110),
        "mounting": "ceiling"
    }
}
```

---

## CLASE PRINCIPAL: Fixture

```python
import uuid
from typing import Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Fixture:
    """
    Representa una luz móvil (moving light fixture).
    
    Attributes:
        name: Nombre descriptivo del fixture
        position: Posición (x, y, z) en el venue
        pan_range: Rango de pan en grados (min, max)
        tilt_range: Rango de tilt en grados (min, max)
        mounting: Tipo de montaje ("ceiling", "floor", "wall")
        pan_invert: Invertir dirección de pan
        tilt_invert: Invertir dirección de tilt
        id: UUID único (generado automáticamente)
        current_pan: Ángulo pan actual en grados
        current_tilt: Ángulo tilt actual en grados
    """
    
    name: str
    position: Tuple[float, float, float]
    pan_range: Tuple[float, float]
    tilt_range: Tuple[float, float]
    mounting: str = "ceiling"
    pan_invert: bool = False
    tilt_invert: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_pan: float = 0.0
    current_tilt: float = 0.0
    
    def __post_init__(self):
        """Validar datos después de inicialización."""
        self._validate()
    
    def _validate(self):
        """
        Valida la configuración del fixture.
        
        Raises:
            ValueError: Si algún parámetro es inválido
        """
        # Validar mounting
        valid_mountings = ["ceiling", "floor", "wall"]
        if self.mounting not in valid_mountings:
            raise ValueError(
                f"mounting must be one of {valid_mountings}, "
                f"got '{self.mounting}'"
            )
        
        # Validar rangos
        if self.pan_range[0] >= self.pan_range[1]:
            raise ValueError(
                f"pan_range min must be < max, got {self.pan_range}"
            )
        
        if self.tilt_range[0] >= self.tilt_range[1]:
            raise ValueError(
                f"tilt_range min must be < max, got {self.tilt_range}"
            )
        
        # Validar posición (básico)
        if len(self.position) != 3:
            raise ValueError(
                f"position must be (x, y, z), got {self.position}"
            )
    
    def point_at(self, target_position: Tuple[float, float, float]) -> None:
        """
        Calcula y actualiza pan/tilt para apuntar al target.
        
        Args:
            target_position: Posición (x, y, z) donde está el pointer
            
        Esta función USA math_engine.calculate_fixture_pan_tilt()
        """
        from math_engine import calculate_fixture_pan_tilt
        import numpy as np
        
        # Calcular ángulos ideales
        pan, tilt = calculate_fixture_pan_tilt(
            fixture_position=np.array(self.position),
            target_position=np.array(target_position),
            mounting=self.mounting,
            pan_invert=self.pan_invert,
            tilt_invert=self.tilt_invert
        )
        
        # Clampear a rangos permitidos
        self.current_pan = self._clamp(pan, *self.pan_range)
        self.current_tilt = self._clamp(tilt, *self.tilt_range)
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Limita un valor entre min y max."""
        return max(min_val, min(value, max_val))
    
    def to_dict(self) -> dict:
        """
        Serializa el fixture a diccionario.
        
        Returns:
            Dict con toda la configuración del fixture
        """
        return {
            'id': self.id,
            'name': self.name,
            'position': list(self.position),
            'pan_range': list(self.pan_range),
            'tilt_range': list(self.tilt_range),
            'mounting': self.mounting,
            'pan_invert': self.pan_invert,
            'tilt_invert': self.tilt_invert,
            'current_pan': self.current_pan,
            'current_tilt': self.current_tilt
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Fixture':
        """
        Crea un fixture desde diccionario.
        
        Args:
            data: Dict con configuración del fixture
            
        Returns:
            Nueva instancia de Fixture
        """
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data['name'],
            position=tuple(data['position']),
            pan_range=tuple(data['pan_range']),
            tilt_range=tuple(data['tilt_range']),
            mounting=data.get('mounting', 'ceiling'),
            pan_invert=data.get('pan_invert', False),
            tilt_invert=data.get('tilt_invert', False),
            current_pan=data.get('current_pan', 0.0),
            current_tilt=data.get('current_tilt', 0.0)
        )
    
    @classmethod
    def from_preset(
        cls, 
        preset_name: str, 
        name: str, 
        position: Tuple[float, float, float]
    ) -> 'Fixture':
        """
        Crea un fixture desde preset built-in.
        
        Args:
            preset_name: Nombre del preset (ej: "Generic Moving Head")
            name: Nombre custom para este fixture
            position: Posición (x, y, z) en el venue
            
        Returns:
            Nueva instancia de Fixture
            
        Raises:
            KeyError: Si el preset no existe
        """
        if preset_name not in FIXTURE_PRESETS:
            available = list(FIXTURE_PRESETS.keys())
            raise KeyError(
                f"Preset '{preset_name}' not found. "
                f"Available: {available}"
            )
        
        preset = FIXTURE_PRESETS[preset_name]
        
        return cls(
            name=name,
            position=position,
            pan_range=preset['pan_range'],
            tilt_range=preset['tilt_range'],
            mounting=preset['mounting']
        )
    
    def __repr__(self) -> str:
        return (
            f"Fixture(id={self.id[:8]}..., name='{self.name}', "
            f"pos={self.position}, pan={self.current_pan:.1f}°, "
            f"tilt={self.current_tilt:.1f}°)"
        )
```

---

## CLASE MANAGER: FixtureManager

```python
class FixtureManager:
    """
    Gestor de múltiples fixtures.
    
    Responsabilidades:
    - Almacenar colección de fixtures
    - CRUD operations
    - Update all fixtures to follow pointer
    - Load/save fixtures
    """
    
    def __init__(self):
        """Inicializa el manager sin fixtures."""
        self.fixtures: dict[str, Fixture] = {}
    
    def add_fixture(self, fixture: Fixture) -> str:
        """
        Agrega un fixture a la colección.
        
        Args:
            fixture: Instancia de Fixture
            
        Returns:
            ID del fixture agregado
        """
        self.fixtures[fixture.id] = fixture
        return fixture.id
    
    def remove_fixture(self, fixture_id: str) -> bool:
        """
        Elimina un fixture por ID.
        
        Args:
            fixture_id: UUID del fixture
            
        Returns:
            True si se eliminó, False si no existía
        """
        if fixture_id in self.fixtures:
            del self.fixtures[fixture_id]
            return True
        return False
    
    def get_fixture(self, fixture_id: str) -> Optional[Fixture]:
        """
        Obtiene un fixture por ID.
        
        Args:
            fixture_id: UUID del fixture
            
        Returns:
            Fixture o None si no existe
        """
        return self.fixtures.get(fixture_id)
    
    def get_all_fixtures(self) -> list[Fixture]:
        """
        Retorna lista de todos los fixtures.
        
        Returns:
            Lista de Fixtures (ordenada por nombre)
        """
        return sorted(self.fixtures.values(), key=lambda f: f.name)
    
    def update_all_fixtures(
        self, 
        target_position: Tuple[float, float, float]
    ) -> None:
        """
        Actualiza TODOS los fixtures para apuntar al target.
        
        Args:
            target_position: Posición (x, y, z) donde está el pointer
            
        Llama a fixture.point_at() para cada fixture.
        """
        for fixture in self.fixtures.values():
            fixture.point_at(target_position)
    
    def clear_all(self) -> None:
        """Elimina todos los fixtures."""
        self.fixtures.clear()
    
    def count(self) -> int:
        """Retorna cantidad de fixtures."""
        return len(self.fixtures)
    
    def to_dict(self) -> dict:
        """
        Serializa todos los fixtures a diccionario.
        
        Returns:
            Dict con lista de fixtures
        """
        return {
            'fixtures': [f.to_dict() for f in self.fixtures.values()]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FixtureManager':
        """
        Crea un manager desde diccionario.
        
        Args:
            data: Dict con configuración de fixtures
            
        Returns:
            Nueva instancia de FixtureManager
        """
        manager = cls()
        
        for fixture_data in data.get('fixtures', []):
            fixture = Fixture.from_dict(fixture_data)
            manager.add_fixture(fixture)
        
        return manager
    
    def __repr__(self) -> str:
        return f"FixtureManager(fixtures={self.count()})"
```

---

## PRESETS GLOBALES

```python
# Presets built-in (al inicio del archivo)
FIXTURE_PRESETS = {
    "Generic Moving Head": {
        "pan_range": (-270, 270),
        "tilt_range": (-135, 135),
        "mounting": "ceiling"
    },
    "Generic LED Par": {
        "pan_range": (0, 0),
        "tilt_range": (-90, 90),
        "mounting": "floor"
    },
    "Generic Wash Light": {
        "pan_range": (-180, 180),
        "tilt_range": (-110, 110),
        "mounting": "ceiling"
    }
}


def get_available_presets() -> list[str]:
    """Retorna lista de nombres de presets disponibles."""
    return list(FIXTURE_PRESETS.keys())
```

---

## ESTRUCTURA COMPLETA DEL ARCHIVO

```python
"""
Fixture Manager Module - Gyro Light Control Visualizer
======================================================

MÓDULO: fixture_manager
VERSIÓN: 1.0
ESTADO: [EN_DESARROLLO]

RESPONSABILIDAD:
Gestión de fixtures (luces móviles) y sus estados.

HACE:
- CRUD de fixtures
- Tracking automático del pointer
- Presets de fixtures comunes
- Serialización para save/load

DEPENDENCIAS:
- math_engine.py (para calculate_fixture_pan_tilt)
- uuid (stdlib)
- dataclasses (stdlib)
"""

import uuid
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass, field


# Presets built-in
FIXTURE_PRESETS = {
    # Implementar aquí
}


@dataclass
class Fixture:
    # Implementar aquí según especificación arriba
    pass


class FixtureManager:
    # Implementar aquí según especificación arriba
    pass


def get_available_presets() -> List[str]:
    # Implementar aquí
    pass


# ============================================================================
# TESTS
# ============================================================================

def test_fixture_creation():
    """Test: crear fixture básico"""
    fixture = Fixture(
        name="Test Fixture",
        position=(5, 9, 3),
        pan_range=(-270, 270),
        tilt_range=(-135, 135)
    )
    
    assert fixture.name == "Test Fixture"
    assert fixture.position == (5, 9, 3)
    assert fixture.mounting == "ceiling"  # default
    assert len(fixture.id) > 0  # UUID generado
    
    print("✅ Test fixture_creation passed")


def test_fixture_validation():
    """Test: validación rechaza valores inválidos"""
    
    # Mounting inválido
    try:
        Fixture(
            name="Bad",
            position=(5, 5, 3),
            pan_range=(-270, 270),
            tilt_range=(-135, 135),
            mounting="invalid"
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    # Pan range invertido
    try:
        Fixture(
            name="Bad",
            position=(5, 5, 3),
            pan_range=(270, -270),  # min > max
            tilt_range=(-135, 135)
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("✅ Test fixture_validation passed")


def test_fixture_from_preset():
    """Test: crear fixture desde preset"""
    fixture = Fixture.from_preset(
        preset_name="Generic Moving Head",
        name="My Moving Head",
        position=(7, 9, 3.5)
    )
    
    assert fixture.name == "My Moving Head"
    assert fixture.position == (7, 9, 3.5)
    assert fixture.pan_range == (-270, 270)
    assert fixture.tilt_range == (-135, 135)
    
    print("✅ Test fixture_from_preset passed")


def test_fixture_point_at():
    """Test: fixture calcula pan/tilt correctamente"""
    # Fixture en techo
    fixture = Fixture(
        name="Test",
        position=(5, 9, 3.5),
        pan_range=(-270, 270),
        tilt_range=(-135, 135),
        mounting="ceiling"
    )
    
    # Apuntar al centro del venue (abajo)
    fixture.point_at((5, 5, 1))
    
    # Pan debe ser ~0° (centrado en X)
    assert abs(fixture.current_pan) < 5, \
        f"Pan should be near 0°, got {fixture.current_pan}°"
    
    # Tilt debe ser negativo (apuntando abajo)
    assert fixture.current_tilt < 0, \
        f"Tilt should be negative, got {fixture.current_tilt}°"
    
    print("✅ Test fixture_point_at passed")


def test_fixture_clamping():
    """Test: pan/tilt se clampean a rangos permitidos"""
    # Fixture con rango limitado
    fixture = Fixture(
        name="Limited",
        position=(5, 9, 3),
        pan_range=(-90, 90),
        tilt_range=(-45, 45),
        mounting="ceiling"
    )
    
    # Apuntar a algo fuera de rango
    fixture.point_at((0, 0, 0))  # Esquina lejana
    
    # Verificar que está dentro de rangos
    assert -90 <= fixture.current_pan <= 90
    assert -45 <= fixture.current_tilt <= 45
    
    print("✅ Test fixture_clamping passed")


def test_fixture_serialization():
    """Test: to_dict y from_dict"""
    original = Fixture(
        name="Serialized Fixture",
        position=(7, 8, 3.2),
        pan_range=(-180, 180),
        tilt_range=(-90, 90),
        mounting="floor",
        pan_invert=True
    )
    
    # Serializar
    data = original.to_dict()
    
    # Deserializar
    restored = Fixture.from_dict(data)
    
    # Verificar
    assert restored.name == original.name
    assert restored.position == original.position
    assert restored.pan_range == original.pan_range
    assert restored.mounting == original.mounting
    assert restored.pan_invert == original.pan_invert
    
    print("✅ Test fixture_serialization passed")


def test_manager_add_remove():
    """Test: agregar y eliminar fixtures"""
    manager = FixtureManager()
    
    fixture1 = Fixture(
        name="F1",
        position=(5, 9, 3),
        pan_range=(-270, 270),
        tilt_range=(-135, 135)
    )
    
    fixture2 = Fixture(
        name="F2",
        position=(3, 9, 3),
        pan_range=(-270, 270),
        tilt_range=(-135, 135)
    )
    
    # Agregar
    id1 = manager.add_fixture(fixture1)
    id2 = manager.add_fixture(fixture2)
    
    assert manager.count() == 2
    
    # Remover
    removed = manager.remove_fixture(id1)
    assert removed == True
    assert manager.count() == 1
    
    # Remover ID inexistente
    removed = manager.remove_fixture("fake-id")
    assert removed == False
    
    print("✅ Test manager_add_remove passed")


def test_manager_update_all():
    """Test: actualizar todos los fixtures"""
    manager = FixtureManager()
    
    # Agregar 3 fixtures
    for i in range(3):
        fixture = Fixture(
            name=f"Fixture {i}",
            position=(i*2, 9, 3),
            pan_range=(-270, 270),
            tilt_range=(-135, 135)
        )
        manager.add_fixture(fixture)
    
    # Actualizar todos
    target = (5, 5, 1)
    manager.update_all_fixtures(target)
    
    # Verificar que todos se actualizaron
    for fixture in manager.get_all_fixtures():
        # Cada fixture debe tener pan/tilt calculado
        assert fixture.current_pan != 0 or fixture.current_tilt != 0
    
    print("✅ Test manager_update_all passed")


def test_manager_serialization():
    """Test: serialización del manager completo"""
    manager = FixtureManager()
    
    # Agregar fixtures
    for i in range(2):
        fixture = Fixture.from_preset(
            "Generic Moving Head",
            f"Fixture {i}",
            (i*3, 9, 3)
        )
        manager.add_fixture(fixture)
    
    # Serializar
    data = manager.to_dict()
    
    # Deserializar
    restored = FixtureManager.from_dict(data)
    
    # Verificar
    assert restored.count() == manager.count()
    
    print("✅ Test manager_serialization passed")


def test_get_available_presets():
    """Test: obtener lista de presets"""
    presets = get_available_presets()
    
    assert "Generic Moving Head" in presets
    assert "Generic LED Par" in presets
    assert len(presets) >= 3
    
    print("✅ Test get_available_presets passed")


def run_all_tests():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("FIXTURE MANAGER - Running Tests")
    print("=" * 60)
    
    try:
        test_fixture_creation()
        test_fixture_validation()
        test_fixture_from_preset()
        test_fixture_point_at()
        test_fixture_clamping()
        test_fixture_serialization()
        test_manager_add_remove()
        test_manager_update_all()
        test_manager_serialization()
        test_get_available_presets()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    # Ejecutar tests
    run_all_tests()
    
    # Demo
    print("\n" + "=" * 60)
    print("DEMO - Fixture Manager Usage")
    print("=" * 60)
    
    manager = FixtureManager()
    
    # Crear fixture desde preset
    fixture = Fixture.from_preset(
        "Generic Moving Head",
        "Front Light",
        position=(5, 9, 3.5)
    )
    
    manager.add_fixture(fixture)
    
    print(f"\nManager: {manager}")
    print(f"Fixture: {fixture}")
    
    # Simular pointer en centro
    print("\nPointer at center (5, 5, 1):")
    manager.update_all_fixtures((5, 5, 1))
    print(f"  Pan: {fixture.current_pan:.1f}°")
    print(f"  Tilt: {fixture.current_tilt:.1f}°")
```

---

## CRITERIOS DE VALIDACIÓN

- [ ] Fixture class con todos los atributos
- [ ] Validación robusta (mounting, ranges, position)
- [ ] `point_at()` usa math_engine correctamente
- [ ] Clamping a rangos funciona
- [ ] Presets desde FIXTURE_PRESETS
- [ ] FixtureManager CRUD completo
- [ ] `update_all_fixtures()` funciona
- [ ] Serialización round-trip perfecta
- [ ] Todos los tests pasan (10/10)
- [ ] Imports correctos (uuid, dataclasses, math_engine)

---

## NOTAS IMPORTANTES

1. **Depende de math_engine.py**:
   - Asegúrate que math_engine.py esté en la misma carpeta
   - Import: `from math_engine import calculate_fixture_pan_tilt`

2. **Dataclass**:
   - Usa `@dataclass` para Fixture (menos boilerplate)
   - `field(default_factory=...)` para UUID

3. **Type hints**:
   - Usa `Tuple[float, float, float]` para posiciones
   - Usa `Optional[Fixture]` para get

4. **Validación**:
   - Valida en `__post_init__` del dataclass
   - Rechaza mountings inválidos
   - Verifica rangos (min < max)

---

## TIEMPO ESTIMADO

**15-25 minutos** (similar a venue_manager.py)

---

**ENTREGA**: Archivo `fixture_manager.py` completo, ejecutable, con 10 tests pasando.
