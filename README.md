# 🎯 Gyro Control

**Módulo base de interacción espacial teléfono ↔ entorno 3D.**

Este es el core reutilizable para múltiples aplicaciones que necesiten trackear orientación de dispositivos móviles en un espacio 3D virtual.

---

## 🚀 Quick Start

```bash
python server.py

# Desktop: http://localhost:8080
# Mobile:  http://[TU_IP]:8080/mobile.html
```

---

## 💡 ¿Qué hace este módulo?

1. **Recibe** datos de giroscopio del móvil (alpha, beta, gamma)
2. **Calcula** dirección 3D e intersección con el espacio virtual
3. **Transmite** la posición en tiempo real a clientes conectados

**Aplicaciones posibles:**
- Control de iluminación escénica
- Puntero 3D para presentaciones
- Control de cámaras virtuales
- Interacción con mappings de video
- Cualquier cosa que necesite "apuntar" a un espacio 3D

---

## 📐 Arquitectura

```
Mobile (Gyroscope)
    ↓ WebSocket
Server (FastAPI)
    ├── SpatialProcessor   → Lógica espacial
    ├── VenueManager       → Estado del espacio 3D  
    └── WebSocketHandler   → Comunicación de red
    ↓ Broadcast
Clientes (Three.js / Tu App)
```

**Patrón:** Producer-Consumer con modelos Pydantic como contratos de datos.

---

## 📁 Estructura

```
gyro-control/
├── server.py              # Orquestador (solo ruteo)
├── spatial_processor.py   # Lógica espacial
├── math_engine.py         # Matemática pura
├── venue_manager.py       # Estado del venue
├── websocket_handler.py   # Comunicación
├── schemas.py             # Contratos Pydantic
├── frontend/              # Interfaces de ejemplo
└── docs/                  # Documentación histórica
```

---

## 🔧 Stack

| Capa | Tecnología |
|------|------------|
| API | FastAPI + WebSocket |
| Validación | Pydantic V2 |
| Matemática | NumPy |
| Frontend demo | Three.js r128 |

---

## ⚠️ Notas Técnicas

- **Coordenadas:** Z-UP (X=ancho, Y=profundidad, Z=altura)
- **Calibración:** Scalar Yaw Offset (no matricial)
- **Input:** alpha (0-360°), beta (±180°), gamma (±90°)
- **Output:** intersection [x,y,z], direction [x,y,z], calibrated bool

---

## 🧪 Tests

```bash
python test_integration.py
python schemas.py  # Tests de validación
```

---

*Módulo base para aplicaciones de interacción espacial.*
