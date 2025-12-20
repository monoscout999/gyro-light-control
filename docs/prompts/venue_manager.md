# PROMPT: Implementar venue_manager.py - Gestor de Estado del Venue

## CONTEXTO DEL PROYECTO

Estás implementando el gestor de estado para el "venue" (espacio 3D donde ocurre todo) en un sistema de control de luces móviles. Este módulo gestiona las dimensiones del espacio, calcula posiciones clave y maneja la serialización para guardar/cargar escenas.

Este es un módulo **SIMPLE** comparado con math_engine.py - principalmente gestión de estado y validación.

---

## TU TAREA

Crear el archivo `venue_manager.py` que gestione:
- Dimensiones del venue (ancho, profundidad, altura)
- Posición del usuario (center del venue + altura ajustable)
- Cálculo de puntos clave (centro pared trasera, corners)
- Serialización/deserialización para save/load
- Validación de valores

---

## ESPECIFICACIONES TÉCNICAS

### Sistema de Coordenadas (recordatorio)
```
        Norte (+Y) ← pared trasera
           ↑
           |
Oeste ←----●---→ Este
(-X)    usuario   (+X)
           |
           ↓
        Sur (-Y)

Z = Vertical (↑ arriba)
```

### Defaults
- **Dimensiones venue**: 10m × 10m × 4m (ancho × profundidad × altura)
- **Grid size**: 1.0m
- **Usuario posición**: Centro XY del venue (width/2, depth/2)
- **Usuario altura**: 1.0m (ajustable 0.5m a 1.5m)

### Limitaciones
- Dimensiones mínimas: 2m × 2m × 2m
- Dimensiones máximas: 100m × 100m × 20m
- Grid size: 0.1m a 5.0m
- Altura usuario: 0.5m a 1.5m

---

## CLASE PRINCIPAL: VenueManager

```python
class VenueManager:
    """
    Gestiona el estado y configuración del venue (espacio 3D).
    
    Responsabilidades:
    - Almacenar dimensiones del venue
    - Calcular posiciones clave (centro pared trasera, corners, etc.)
    - Validar cambios de dimensiones
    - Serializar/deserializar estado para guardar/cargar
    - Gestionar posición del usuario
    """
    
    def __init__(
        self, 
        width: float = 10.0,
        depth: float = 10.0, 
        height: float = 4.0,
        grid_size: float = 1.0,
        user_height: float = 1.0
    ):
        """
        Inicializa el venue con dimensiones configurables.
        
        Args:
            width: Ancho del venue en metros (X axis)
            depth: Profundidad del venue en metros (Y axis)
            height: Altura del venue en metros (Z axis)
            grid_size: Tamaño de cuadrícula del grid en metros
            user_height: Altura del usuario desde el piso en metros
        """
        # Validar y asignar
        self.width = self._validate_dimension(width, "width")
        self.depth = self._validate_dimension(depth, "depth")
        self.height = self._validate_dimension(height, "height")
        self.grid_size = self._validate_grid_size(grid_size)
        self.user_height = self._validate_user_height(user_height)
```

---

## MÉTODOS REQUERIDOS

### 1. Validación

```python
def _validate_dimension(self, value: float, name: str) -> float:
    """
    Valida que una dimensión esté en rango permitido.
    
    Args:
        value: Valor a validar
        name: Nombre de la dimensión (para mensaje de error)
        
    Returns:
        Valor validado
        
    Raises:
        ValueError: Si el valor está fuera de rango
        
    Rango: 2.0m a 100.0m
    """
    MIN_DIM = 2.0
    MAX_DIM = 100.0
    
    if not MIN_DIM <= value <= MAX_DIM:
        raise ValueError(
            f"{name} must be between {MIN_DIM}m and {MAX_DIM}m, "
            f"got {value}m"
        )
    return float(value)


def _validate_grid_size(self, value: float) -> float:
    """
    Valida que el tamaño de grid esté en rango permitido.
    
    Rango: 0.1m a 5.0m
    """
    MIN_GRID = 0.1
    MAX_GRID = 5.0
    
    if not MIN_GRID <= value <= MAX_GRID:
        raise ValueError(
            f"Grid size must be between {MIN_GRID}m and {MAX_GRID}m, "
            f"got {value}m"
        )
    return float(value)


def _validate_user_height(self, value: float) -> float:
    """
    Valida que la altura del usuario esté en rango permitido.
    
    Rango: 0.5m a 1.5m
    """
    MIN_HEIGHT = 0.5
    MAX_HEIGHT = 1.5
    
    if not MIN_HEIGHT <= value <= MAX_HEIGHT:
        raise ValueError(
            f"User height must be between {MIN_HEIGHT}m and {MAX_HEIGHT}m, "
            f"got {value}m"
        )
    return float(value)
```

### 2. Setters con validación

```python
def set_dimensions(
    self, 
    width: float, 
    depth: float, 
    height: float
) -> None:
    """
    Actualiza las dimensiones del venue.
    
    Args:
        width: Nuevo ancho en metros
        depth: Nueva profundidad en metros
        height: Nueva altura en metros
        
    Raises:
        ValueError: Si algún valor está fuera de rango
    """
    self.width = self._validate_dimension(width, "width")
    self.depth = self._validate_dimension(depth, "depth")
    self.height = self._validate_dimension(height, "height")


def set_grid_size(self, grid_size: float) -> None:
    """Actualiza el tamaño del grid."""
    self.grid_size = self._validate_grid_size(grid_size)


def set_user_height(self, height: float) -> None:
    """Actualiza la altura del usuario."""
    self.user_height = self._validate_user_height(height)
```

### 3. Cálculos de posiciones clave

```python
def get_user_position(self) -> tuple:
    """
    Retorna la posición del usuario (centro del venue + altura).
    
    Returns:
        Tupla (x, y, z) en metros
        
    El usuario siempre está en el centro XY del venue.
    """
    x = self.width / 2
    y = self.depth / 2
    z = self.user_height
    return (x, y, z)


def get_back_wall_center(self) -> tuple:
    """
    Retorna el centro de la pared trasera (target de calibración).
    
    Returns:
        Tupla (x, y, z) en metros
        
    La pared trasera es la pared en Y máximo (norte).
    Su centro está a media altura del venue.
    """
    x = self.width / 2
    y = self.depth  # Pared trasera = Y máximo
    z = self.height / 2
    return (x, y, z)


def get_bounds(self) -> dict:
    """
    Retorna las esquinas min/max del venue (para ray intersection).
    
    Returns:
        Dict con keys 'min' y 'max', cada uno tupla (x, y, z)
        
    Ejemplo:
        {
            'min': (0, 0, 0),
            'max': (10, 10, 4)
        }
    """
    return {
        'min': (0.0, 0.0, 0.0),
        'max': (self.width, self.depth, self.height)
    }


def get_corners(self) -> list:
    """
    Retorna las 8 esquinas del venue.
    
    Returns:
        Lista de 8 tuplas (x, y, z)
        
    Orden: inferior (z=0) primero, superior (z=height) después
    """
    corners = []
    
    # Inferior (floor level, z=0)
    for x in [0, self.width]:
        for y in [0, self.depth]:
            corners.append((x, y, 0))
    
    # Superior (ceiling level, z=height)
    for x in [0, self.width]:
        for y in [0, self.depth]:
            corners.append((x, y, self.height))
    
    return corners
```

### 4. Serialización

```python
def to_dict(self) -> dict:
    """
    Serializa el estado del venue a diccionario (para guardar JSON).
    
    Returns:
        Dict con toda la configuración del venue
    """
    return {
        'dimensions': {
            'width': self.width,
            'depth': self.depth,
            'height': self.height
        },
        'grid_size': self.grid_size,
        'user_height': self.user_height
    }


@classmethod
def from_dict(cls, data: dict) -> 'VenueManager':
    """
    Crea una instancia desde diccionario (para cargar JSON).
    
    Args:
        data: Dict con configuración del venue
        
    Returns:
        Nueva instancia de VenueManager
        
    Ejemplo de data:
        {
            'dimensions': {'width': 10, 'depth': 10, 'height': 4},
            'grid_size': 1.0,
            'user_height': 1.0
        }
    """
    dims = data.get('dimensions', {})
    
    return cls(
        width=dims.get('width', 10.0),
        depth=dims.get('depth', 10.0),
        height=dims.get('height', 4.0),
        grid_size=data.get('grid_size', 1.0),
        user_height=data.get('user_height', 1.0)
    )
```

### 5. Utilidades

```python
def __repr__(self) -> str:
    """Representación string del venue."""
    return (
        f"VenueManager("
        f"dimensions={self.width}x{self.depth}x{self.height}m, "
        f"grid={self.grid_size}m, "
        f"user_height={self.user_height}m)"
    )


def get_info(self) -> dict:
    """
    Retorna información completa del venue para debugging.
    
    Returns:
        Dict con toda la info útil
    """
    return {
        'dimensions': {
            'width': self.width,
            'depth': self.depth,
            'height': self.height,
            'volume': self.width * self.depth * self.height
        },
        'grid_size': self.grid_size,
        'user': {
            'position': self.get_user_position(),
            'height': self.user_height
        },
        'key_points': {
            'back_wall_center': self.get_back_wall_center(),
            'bounds': self.get_bounds()
        }
    }
```

---

## ESTRUCTURA COMPLETA DEL ARCHIVO

```python
"""
Venue Manager Module - Gyro Light Control Visualizer
====================================================

MÓDULO: venue_manager
VERSIÓN: 1.0
ESTADO: [EN_DESARROLLO]

RESPONSABILIDAD:
Gestión del estado del venue (espacio 3D donde ocurre todo).

HACE:
- Almacenar dimensiones del venue
- Calcular posiciones clave (usuario, pared trasera, corners)
- Validar cambios de dimensiones
- Serializar/deserializar para guardar/cargar escenas

NO HACE:
- ❌ Renderizado 3D
- ❌ Matemáticas complejas
- ❌ Comunicación de red

DEPENDENCIAS: Ninguna (Python stdlib only)
"""

from typing import Dict, List, Tuple


class VenueManager:
    """Gestor del estado del venue."""
    
    # Constantes
    MIN_DIMENSION = 2.0
    MAX_DIMENSION = 100.0
    MIN_GRID_SIZE = 0.1
    MAX_GRID_SIZE = 5.0
    MIN_USER_HEIGHT = 0.5
    MAX_USER_HEIGHT = 1.5
    
    def __init__(
        self, 
        width: float = 10.0,
        depth: float = 10.0, 
        height: float = 4.0,
        grid_size: float = 1.0,
        user_height: float = 1.0
    ):
        # Implementar aquí
        pass
    
    # Métodos de validación
    def _validate_dimension(self, value: float, name: str) -> float:
        pass
    
    def _validate_grid_size(self, value: float) -> float:
        pass
    
    def _validate_user_height(self, value: float) -> float:
        pass
    
    # Setters
    def set_dimensions(self, width: float, depth: float, height: float) -> None:
        pass
    
    def set_grid_size(self, grid_size: float) -> None:
        pass
    
    def set_user_height(self, height: float) -> None:
        pass
    
    # Cálculos de posiciones
    def get_user_position(self) -> Tuple[float, float, float]:
        pass
    
    def get_back_wall_center(self) -> Tuple[float, float, float]:
        pass
    
    def get_bounds(self) -> Dict[str, Tuple[float, float, float]]:
        pass
    
    def get_corners(self) -> List[Tuple[float, float, float]]:
        pass
    
    # Serialización
    def to_dict(self) -> dict:
        pass
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VenueManager':
        pass
    
    # Utilidades
    def __repr__(self) -> str:
        pass
    
    def get_info(self) -> dict:
        pass


# ============================================================================
# TESTS
# ============================================================================

def test_default_initialization():
    """Test: inicialización con valores default"""
    venue = VenueManager()
    
    assert venue.width == 10.0
    assert venue.depth == 10.0
    assert venue.height == 4.0
    assert venue.grid_size == 1.0
    assert venue.user_height == 1.0
    
    print("✅ Test default_initialization passed")


def test_custom_initialization():
    """Test: inicialización con valores custom"""
    venue = VenueManager(
        width=15.0,
        depth=20.0,
        height=5.0,
        grid_size=0.5,
        user_height=1.2
    )
    
    assert venue.width == 15.0
    assert venue.depth == 20.0
    assert venue.height == 5.0
    assert venue.grid_size == 0.5
    assert venue.user_height == 1.2
    
    print("✅ Test custom_initialization passed")


def test_validation_rejects_invalid():
    """Test: validación rechaza valores inválidos"""
    
    # Dimensiones muy pequeñas
    try:
        venue = VenueManager(width=1.0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    # Dimensiones muy grandes
    try:
        venue = VenueManager(width=200.0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    # Grid size inválido
    try:
        venue = VenueManager(grid_size=10.0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    # User height inválido
    try:
        venue = VenueManager(user_height=2.0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("✅ Test validation_rejects_invalid passed")


def test_user_position():
    """Test: posición del usuario en centro del venue"""
    venue = VenueManager(width=10.0, depth=10.0, user_height=1.0)
    
    user_pos = venue.get_user_position()
    
    assert user_pos == (5.0, 5.0, 1.0), \
        f"Expected (5, 5, 1), got {user_pos}"
    
    print("✅ Test user_position passed")


def test_back_wall_center():
    """Test: centro de pared trasera"""
    venue = VenueManager(width=10.0, depth=10.0, height=4.0)
    
    back_wall = venue.get_back_wall_center()
    
    assert back_wall == (5.0, 10.0, 2.0), \
        f"Expected (5, 10, 2), got {back_wall}"
    
    print("✅ Test back_wall_center passed")


def test_bounds():
    """Test: bounds del venue"""
    venue = VenueManager(width=10.0, depth=10.0, height=4.0)
    
    bounds = venue.get_bounds()
    
    assert bounds['min'] == (0.0, 0.0, 0.0)
    assert bounds['max'] == (10.0, 10.0, 4.0)
    
    print("✅ Test bounds passed")


def test_corners():
    """Test: 8 corners del venue"""
    venue = VenueManager(width=10.0, depth=10.0, height=4.0)
    
    corners = venue.get_corners()
    
    assert len(corners) == 8, f"Should have 8 corners, got {len(corners)}"
    
    # Verificar que tiene corners en floor (z=0)
    floor_corners = [c for c in corners if c[2] == 0]
    assert len(floor_corners) == 4
    
    # Verificar que tiene corners en ceiling (z=4)
    ceiling_corners = [c for c in corners if c[2] == 4.0]
    assert len(ceiling_corners) == 4
    
    print("✅ Test corners passed")


def test_serialization():
    """Test: to_dict y from_dict"""
    original = VenueManager(
        width=15.0,
        depth=12.0,
        height=5.0,
        grid_size=0.5,
        user_height=1.3
    )
    
    # Serializar
    data = original.to_dict()
    
    # Deserializar
    restored = VenueManager.from_dict(data)
    
    # Verificar que son iguales
    assert restored.width == original.width
    assert restored.depth == original.depth
    assert restored.height == original.height
    assert restored.grid_size == original.grid_size
    assert restored.user_height == original.user_height
    
    print("✅ Test serialization passed")


def test_set_dimensions():
    """Test: cambiar dimensiones después de inicialización"""
    venue = VenueManager()
    
    venue.set_dimensions(20.0, 15.0, 6.0)
    
    assert venue.width == 20.0
    assert venue.depth == 15.0
    assert venue.height == 6.0
    
    # User position debe actualizarse
    user_pos = venue.get_user_position()
    assert user_pos == (10.0, 7.5, 1.0)
    
    print("✅ Test set_dimensions passed")


def test_get_info():
    """Test: get_info retorna dict completo"""
    venue = VenueManager()
    
    info = venue.get_info()
    
    assert 'dimensions' in info
    assert 'grid_size' in info
    assert 'user' in info
    assert 'key_points' in info
    
    print("✅ Test get_info passed")


def run_all_tests():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("VENUE MANAGER - Running Tests")
    print("=" * 60)
    
    try:
        test_default_initialization()
        test_custom_initialization()
        test_validation_rejects_invalid()
        test_user_position()
        test_back_wall_center()
        test_bounds()
        test_corners()
        test_serialization()
        test_set_dimensions()
        test_get_info()
        
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
    
    # Demo de uso
    print("\n" + "=" * 60)
    print("DEMO - Venue Manager Usage")
    print("=" * 60)
    
    venue = VenueManager()
    print(f"\n{venue}")
    print(f"\nUser position: {venue.get_user_position()}")
    print(f"Back wall center: {venue.get_back_wall_center()}")
    print(f"Bounds: {venue.get_bounds()}")
```

---

## CRITERIOS DE VALIDACIÓN

El módulo está listo para marcar como **[VALIDADO]** cuando:

- [ ] Todas las funciones implementadas
- [ ] Todos los tests pasan (10/10)
- [ ] Validación rechaza valores inválidos correctamente
- [ ] Serialización round-trip funciona (to_dict → from_dict)
- [ ] Sin dependencias externas (solo Python stdlib)
- [ ] Código documentado con docstrings
- [ ] Manejo de edge cases:
  - [ ] Valores límite (min/max)
  - [ ] Valores negativos
  - [ ] Valores muy grandes

---

## NOTAS IMPORTANTES

1. **Módulo simple**: 
   - No hay matemáticas complejas
   - Solo validación y cálculos básicos
   - Fácil de entender y mantener

2. **Sin dependencias**:
   - No necesita NumPy
   - Solo Python stdlib
   - Typing para type hints

3. **Validación robusta**:
   - Todos los setters validan
   - Mensajes de error claros
   - Valores fuera de rango = ValueError

4. **Serialización limpia**:
   - JSON-friendly (floats, dicts, listas)
   - Round-trip debe ser perfecto
   - Compatible con save/load de escenas

---

## ENTREGA

Genera el archivo `venue_manager.py` completo con:
1. Clase VenueManager implementada
2. Todos los métodos funcionando
3. 10 tests unitarios incluidos
4. Demo de uso al final
5. Documentación en docstrings
6. Ejecutable con `python venue_manager.py`

---

**Este módulo es MUCHO más simple que math_engine.py. Deberías terminarlo en 15-20 minutos.**
