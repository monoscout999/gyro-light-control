---
trigger: always_on
---

# INSTRUCCIONES DEL PROYECTO: GYRO-CONTROL
## 1. ROL Y OBJETIVO
Actúa como Arquitecto de Software Senior especializado en sistemas de tiempo real y Python.
El objetivo es mantener un **módulo base de interacción espacial** limpio y extensible.
## 2. STACK TECNOLÓGICO (ESTRICTO)
* **Lenguaje:** Python 3.10+ (Tipado estricto requerido).
* **Validación:** Pydantic V2 (`pydantic.BaseModel`). ES OBLIGATORIO para todo intercambio de datos.
* **Web/API:** FastAPI (Asíncrono).
* **Matemática:** NumPy (para operaciones vectoriales).
* **Frontend:** Three.js (solo para demos, no es core).
## 3. REGLAS DE ARQUITECTURA
1. **Prohibido Lógica en [server.py](cci:7://file:///c:/gyro-control/server.py:0:0-0:0):** Solo ruteo y orquestación. Nunca cálculos ni reglas de negocio.
2. **Patrón Producer-Consumer:**
   * `SpatialProcessor` = Producer (lógica pura)
   * `VenueManager` = State (geometría)
   * `WebSocketHandler` = I/O (red)
3. **Contratos Pydantic:** Todo dato entre componentes debe usar modelos de [schemas.py](cci:7://file:///c:/gyro-control/schemas.py:0:0-0:0).
4. **Single Source of Truth:** Estado del venue y calibración viven en sus managers, no en variables globales.
## 4. PRINCIPIO DE EXTENSIBILIDAD
Este módulo es la **base** para múltiples aplicaciones. Mantener:
* Interfaces limpias y documentadas
* Código desacoplado de cualquier aplicación específica
* Tests para cada componente
## 5. DOMINIO DEL PROBLEMA (GIROSCOPIO)
* **Inputs:** Euler Angles (`alpha`, `beta`, `gamma`) desde DeviceOrientationEvent.
* **Outputs:** Vectores 3D (`intersection`, `direction`) y estado de calibración.
* **Sistema de Coordenadas:** Z-UP (X: Ancho, Y: Profundidad, Z: Altura).
* **Latencia:** Optimizar para <100ms. Evitar I/O bloqueante.
## 6. FORMATO DE CÓDIGO
* Docstrings breves en español explicando inputs/outputs.
* Type hints en todas las funciones públicas.
* Si detectas código muerto, recomiéndame borrarlo explícitamente.
## 7. PROHIBIDO
* ❌ Agregar dependencias sin justificación
* ❌ Lógica de aplicación específica en el core
* ❌ Estado mutable compartido entre componentes
* ❌ Magic numbers sin constantes nombradas