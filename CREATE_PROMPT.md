# 🎯 CONFIGURACIÓN CLAUDE CODE

**Target:** Claude Code with Opus 4  
**Date:** December 17, 2024  
**Project:** Gyro Light Control - Real-time 3D lighting system

---

## ⚙️ CONFIGURACIÓN DEL AGENTE (OBLIGATORIO)

### Parámetros del Modelo
```json
{
  "model": "claude-opus-4",
  "temperature": 0.3,
  "max_tokens": 200000,
  "top_p": 1.0
}
```

**Justificación de parámetros:**
- **Opus 4:** Necesitás razonamiento profundo para debugging multi-agente
- **Temperature 0.3:** Bajo para código (consistencia > creatividad)
- **200K tokens:** Proyecto mediano, necesita contexto completo
- **top_p 1.0:** Default, no limitar vocabulario en código

---

### System Prompt / Rol del Agente

```markdown
ROL: Arquitecto Senior de Debugging para código multi-agente

PERSONALIDAD:
- Meticuloso y sistemático
- Desconfía de asunciones
- Valida antes de modificar
- Documenta cada decisión

RESPONSABILIDADES:
1. Auditar completitud de implementación
2. Identificar inconsistencias arquitectónicas
3. Proponer fixes conservadores (no refactors masivos)
4. Validar cada cambio con tests o logging

RESTRICCIONES:
- NUNCA modificar backend (100% validado)
- NUNCA hacer cambios sin explicar por qué
- NUNCA asumir que "debería funcionar" - verificar
- NUNCA hacer múltiples cambios a la vez

METODOLOGÍA:
1. Leer create_prompt.md COMPLETO sin resumir
2. Analizar archivos críticos: scene3d.js, main.js
3. Comparar contratos: backend output vs frontend input
4. Listar problemas por criticidad
5. Proponer fixes UNO A LA VEZ
6. Después de cada fix: validar + logging
```

---

### Estrategia de Trabajo (CRÍTICO)

**NO hagas todo de una vez. Seguí este workflow:**

#### Fase 1: AUDITORÍA (1 sesión, NO tocar código)
```
Outputs esperados:
- Lista de métodos faltantes en scene3d.js
- Lista de métodos incompletos
- Problemas de formato de datos
- Referencias inseguras (this.objects sin guards)
- Priorización 🔴🟠🟡⚪

Formato de reporte:
## MÉTODOS FALTANTES ❌
- method_name() - Llamado en main.js:123 - NO EXISTE
...

## MÉTODOS INCOMPLETOS ⚠️
- method_name() - Existe pero falta lógica X
...

Tiempo estimado: 20-30 minutos
```

#### Fase 2: QUICK WINS (1-3 sesiones)
```
Un fix a la vez. Después de cada fix:
1. Explicar QUÉ cambiaste y POR QUÉ
2. Agregar console.log para validar
3. Proponer test manual
4. Esperar confirmación antes de siguiente fix

Orden sugerido:
1. Guards de this.objects (bajo riesgo)
2. Try-catch en render loop (bajo riesgo)
3. Logging de formatos (debugging)
4. Métodos faltantes simples
5. Métodos complejos

Tiempo por fix: 5-10 minutos
```

#### Fase 3: FIXES COMPLEJOS (2-5 sesiones)
```
Para cada método complejo:
1. Analizar dependencias
2. Proponer implementación con comentarios
3. Explicar edge cases
4. Agregar validación de inputs
5. Proponer test case manual

Esperar validación en cada paso.

Tiempo por método: 15-30 minutos
```

#### Fase 4: TESTS (1-2 sesiones)
```
Agregar tests básicos con Jest/Vitest:
- scene3d.js métodos críticos
- Conversión de formatos en main.js
- WebSocket message handling

Tiempo: 30-60 minutos
```

---

### Checkpoints de Validación

Después de CADA cambio, verificar:

```javascript
// 1. Sintaxis OK
npm run lint || console.log('Check syntax manually')

// 2. Console logs
// Debe mostrar datos esperados, no undefined/null

// 3. Three.js revision
console.log(THREE.REVISION) // Debe ser "128"

// 4. WebSocket conectado
// En DevTools → Network → WS → Status "101"

// 5. Sin errores en console
// F12 → Console → No debe haber errores rojos
```

---

### Criterios de Éxito

**Auditoría completa cuando:**
- ✅ Todos los métodos listados (faltantes vs incompletos vs OK)
- ✅ Todos los formatos de datos documentados
- ✅ Todas las referencias inseguras identificadas
- ✅ Priorización clara con 🔴🟠🟡⚪

**Quick Wins completos cuando:**
- ✅ Guards agregados (sin errores TypeError)
- ✅ Try-catch en render loop
- ✅ Logging extensivo agregado
- ✅ Console muestra datos esperados

**Fixes complejos completos cuando:**
- ✅ Métodos implementados correctamente
- ✅ Edge cases manejados
- ✅ Inputs validados
- ✅ Funcionamiento verificado manualmente

**Tests agregados cuando:**
- ✅ Al menos 5 tests pasando
- ✅ Métodos críticos cubiertos
- ✅ CI/CD configurado (opcional)

---

### Formato de Comunicación

**Siempre estructurá tus respuestas así:**

```markdown
## 🔍 ANÁLISIS
[Qué encontraste]

## 💡 PROPUESTA
[Qué querés cambiar y POR QUÉ]

## ⚠️ RIESGOS
[Qué podría romperse]

## ✅ VALIDACIÓN
[Cómo verificar que funcionó]

## 📝 CÓDIGO
[El cambio específico]
```

---

### Comandos de Inicialización

**Copiar y pegar en tu terminal:**

```bash
# 1. Navegar al proyecto
cd /path/to/gyro-light-control

# 2. Verificar archivos críticos
ls -la frontend/js/scene3d.js
ls -la frontend/js/main.js

# 3. Iniciar Claude Code con configuración
export ANTHROPIC_MODEL="claude-opus-4"
export ANTHROPIC_TEMPERATURE="0.3"
export ANTHROPIC_MAX_TOKENS="200000"

claude-code --model claude-opus-4

# 4. Verificar configuración
# En Claude Code, preguntar:
# "¿Qué modelo estás usando y con qué temperatura?"
```

---

## 🎯 OBJETIVO PRINCIPAL

Este proyecto fue construido por **MÚLTIPLES AGENTES** sin coordinación perfecta.

**Estado actual:**
- Backend: 100% funcional ✅ (36/36 tests passing)
- Frontend: 70% funcional, 30% broken ⚠️
- Integration: Parcialmente funcional, requiere auditoría completa

---

## ENFOQUE REQUERIDO

### 1️⃣ PRIMERO: Auditoría completa (NO tocar código aún)
- Analizar scene3d.js línea por línea
- Listar TODOS los métodos llamados desde main.js
- Verificar existencia y completitud de cada método
- Identificar referencias a objetos que podrían no existir

### 2️⃣ SEGUNDO: Reporte de problemas
- Métodos faltantes vs métodos incompletos
- Inconsistencias de formato de datos
- Errores silenciosos que solo fallan en runtime
- Priorizar por criticidad

### 3️⃣ TERCERO: Plan de fixes incrementales
- Empezar por Quick Wins (<30min cada uno)
- Agregar tests para cada fix
- Validar que no rompemos backend funcionante

---

## 🚨 RED FLAGS ESPECÍFICOS A BUSCAR

### En scene3d.js:
- ❌ Métodos llamados desde main.js pero que NO EXISTEN
- ⚠️ Métodos que existen pero tienen lógica incompleta
- 💀 Referencias a `this.objects.X` sin validar existencia
- 🔥 Errores de formato: backend envía array, frontend espera object

### En main.js:
- ❌ Conversiones de formato incorrectas (pointer, fixtures)
- ⚠️ Falta de try-catch en handlers críticos
- 💀 Asunciones sobre estructura de datos del backend

### General:
- ❌ Sin tests frontend (0% coverage)
- ⚠️ Dependencia global de THREE.js (r128, namespace deprecated)
- 💀 Line endings CRLF en todos los archivos frontend

---

## ⛔ ARCHIVOS INMUTABLES (NO MODIFICAR)

Estos están 100% validados y funcionando:

```
✅ math_engine.py        - 8/8 tests passing
✅ venue_manager.py      - 10/10 tests passing
✅ fixture_manager.py    - 10/10 tests passing
✅ websocket_handler.py  - 8/8 tests passing
✅ server.py             - Integration validated
```

**REGLA DE ORO:**  
Si creés que hay un bug en backend, PRIMERO verificá que el problema no esté en el frontend interpretando mal los datos.

---

# 📋 PROJECT OVERVIEW

## Descripción Técnica

**Gyro Light Control** - Sistema de control de iluminación escénica en tiempo real usando giroscopio de dispositivo móvil.

### Flujo de datos:
```
Mobile (Gyroscope) 
    ↓ WebSocket
Python Backend (FastAPI)
    ↓ Math Engine (Ray tracing, Euler conversion)
    ↓ WebSocket Broadcast
Desktop (Three.js 3D Visualization)
```

### Concepto:
- Móvil envía orientación (alpha/beta/gamma)
- Backend calcula intersección ray-box con venue
- Frontend visualiza en 3D: venue, usuario, ray pointer, fixtures
- Fixtures (moving heads) siguen automáticamente el pointer

---

## Stack Tecnológico

### Backend (Python)
- **FastAPI** - WebSocket + REST API
- **NumPy** - Cálculos matemáticos
- **Uvicorn** - ASGI server
- **Python 3.10+**

### Frontend (JavaScript)
- **Three.js r128** ⚠️ CRITICAL: Usando r128, NO r160+
  - CDN: `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`
  - OrbitControls: `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js`
  - **Razón:** Versiones posteriores deprecaron global namespace `THREE`
- **Native WebSocket API**
- **Tailwind CSS** (CDN)
- **Vanilla JavaScript** - Sin frameworks

---

## Estructura del Proyecto

```
/gyro-light-control/
├── Backend (Python - Root Directory)
│   ├── math_engine.py          ✅ 8/8 tests
│   ├── venue_manager.py        ✅ 10/10 tests
│   ├── fixture_manager.py      ✅ 10/10 tests
│   ├── websocket_handler.py    ✅ 8/8 tests
│   └── server.py               ✅ Integration OK
│
└── Frontend
    ├── index.html              [Desktop UI]
    ├── mobile.html             [Mobile sensor UI]
    └── js/
        ├── scene3d.js          ⚠️ PROBLEMAS AQUÍ
        ├── main.js             ⚠️ Format conversion issues
        ├── websocket_client.js ✅ OK
        └── mobile_sensor.js    ✅ OK
```

---

# 🔴 PROBLEMAS ACTUALES - PRIORIDAD

## CRÍTICO 🔴 (Requiere fix inmediato)

### 1. scene3d.js incompleto
**Síntoma:** Métodos llamados desde main.js que no existen o están rotos  
**Impacto:** Runtime errors, visualización broken  
**Métodos sospechosos:**
- `updatePointer()` - ✅ FIXED (pero verificar formato)
- `updateFixtures()` - ✅ ADDED (verificar implementación)
- `render()` - ✅ ADDED (verificar si funciona)
- `resize()` - ✅ ADDED (verificar event listener)
- `createFixture()` - ⚠️ Verificar si implementación completa
- `updateFixture()` - ⚠️ Verificar si actualiza correctamente
- `removeFixture()` - ⚠️ Verificar cleanup

**Acción:** Auditar scene3d.js completo contra main.js

### 2. Contratos de datos inconsistentes
**Problema:** Backend envía formato X, frontend espera formato Y

**Backend envía:**
```json
{
  "type": "state_update",
  "pointer": {
    "position": [5.2, 8.3, 2.1],  // Array
    "normal": [0, 0, 1]
  },
  "fixtures": [
    {"id": "uuid", "pan": 125.3, "tilt": -45.7}
  ]
}
```

**Frontend espera:**
```javascript
// updatePointer() necesita:
{
  point: THREE.Vector3(x, y, z)
}

// createFixture() necesita verificación de formato
```

**Acción:** Validar conversión de formatos en main.js `handleStateUpdate()`

### 3. Referencias inseguras a this.objects
**Problema:** Código asume que `this.objects.pointerRay` existe sin validar  
**Impacto:** TypeError en runtime si objeto no inicializado  
**Acción:** Agregar guards: `if (this.objects?.pointerRay)`

---

## ALTO 🟠 (Bloquea desarrollo)

### 4. Sin tests frontend (0% coverage)
**Problema:** Imposible saber qué funciona hasta que falla en runtime  
**Acción:** Agregar Jest/Vitest para scene3d.js

### 5. Dependencia global de THREE.js
**Problema:** r128 usa global namespace, versiones modernas usan ES modules  
**Impacto:** Dificulta actualización futura  
**Acción:** Planear migración a ES6 modules + Vite

### 6. Sin error boundaries
**Problema:** Un error en render loop crashea toda la app  
**Acción:** Wrap render loop y WebSocket handlers en try-catch

---

## MEDIO 🟡 (Deuda técnica)

7. Sin TypeScript - No hay type safety
8. Sin bundler - Archivos raw servidos via CDN
9. Sin CI/CD - Testing manual
10. Line endings CRLF - Complica edición con str_replace

---

## BAJO ⚪ (Futuro)

11. Sin Docker
12. Sin HTTPS/WSS
13. Sin autenticación
14. Sin rate limiting

---

# ⚡ QUICK WINS (Fix <30min cada uno)

Estos fixes son de bajo riesgo y alto impacto:

- [ ] **Wrap render loop en try-catch**
  ```javascript
  animate() {
    try {
      requestAnimationFrame(this.animate.bind(this));
      this.renderer.render(this.scene, this.camera);
    } catch (error) {
      console.error('Render error:', error);
    }
  }
  ```

- [ ] **Agregar guards a this.objects**
  ```javascript
  updatePointer(intersection) {
    if (!this.objects?.pointerRay) return;
    // ... resto del código
  }
  ```

- [ ] **Logging de formatos recibidos**
  ```javascript
  handleStateUpdate(data) {
    console.log('Received data format:', {
      pointer: typeof data.pointer,
      fixtures: Array.isArray(data.fixtures)
    });
    // ... procesamiento
  }
  ```

- [ ] **Validar existencia de métodos antes de llamar**
  ```javascript
  if (scene3d && typeof scene3d.updatePointer === 'function') {
    scene3d.updatePointer(intersection);
  }
  ```

- [ ] **Agregar método dispose() para cleanup**
  ```javascript
  dispose() {
    this.renderer?.dispose();
    this.controls?.dispose();
    // ... cleanup de geometries y materials
  }
  ```

---

# 🔧 BACKEND MODULES (REFERENCIA)

## math_engine.py ✅
**Status:** IMMUTABLE - 8/8 tests passing

**Funciones críticas:**
```python
euler_to_direction_vector(alpha, beta, gamma) -> np.ndarray
ray_box_intersection(ray_origin, ray_direction, box_min, box_max) -> Optional[np.ndarray]
calculate_fixture_pan_tilt(fixture_pos, target_pos, mounting, pan_inv, tilt_inv) -> Tuple[float, float]
```

**⚠️ CRITICAL:** Sistema de coordenadas **Z-UP** (no Y-up)
```
     Z (UP)
     ↑
     |
     |___→ X
    /
   ↙ Y (Depth)
```

---

## venue_manager.py ✅
**Status:** IMMUTABLE - 10/10 tests passing

**Defaults:**
- Venue: 10m × 10m × 4m
- User position: (5, 5, 1) - centro del venue, 1m sobre el piso
- +Y axis = back wall

---

## fixture_manager.py ✅
**Status:** IMMUTABLE - 10/10 tests passing

**Presets disponibles:**
- Generic Moving Head: pan (-270°, 270°), tilt (-135°, 135°)
- Generic LED Par: pan fijo, tilt (-90°, 90°)
- Generic Wash Light: pan (-180°, 180°), tilt (-110°, 110°)

---

## websocket_handler.py ✅
**Status:** IMMUTABLE - 8/8 tests passing

**Features críticas:**
- LatencyBuffer: suaviza datos (3 samples)
- **Alpha wraparound interpolation** ⚠️ (359° → 1° va por 0°, no 180°)
- Broadcast automático a todos los clientes

---

## server.py ✅
**Status:** IMMUTABLE - Integration validated

**Endpoints:**
```python
GET  /              # index.html
GET  /mobile.html   # mobile interface
WS   /ws            # WebSocket endpoint
GET  /api/venue     # Venue info
POST /api/calibrate # Calibrate sensor
POST /api/reset     # Reset state
```

**Puerto:** 8080

---

# 📡 CONTRATOS DE DATOS

## Mobile → Server
```json
{
  "type": "sensor_data",
  "alpha": 245.3,    // Compass heading (0-360)
  "beta": -12.7,     // Tilt forward/back (-180 to 180)
  "gamma": 3.2,      // Roll left/right (-90 to 90)
  "timestamp": 1702650123456
}
```

## Server → Desktop (Broadcast)
```json
{
  "type": "state_update",
  "sensor": {"alpha": 245.3, "beta": -12.7, "gamma": 3.2},
  "pointer": {
    "position": [5.2, 8.3, 2.1],  // [x, y, z] coordinates
    "normal": [0, 0, 1]            // Wall normal vector
  },
  "fixtures": [
    {
      "id": "uuid-string",
      "pan": 125.3,       // Pan angle in degrees
      "tilt": -45.7,      // Tilt angle in degrees
      "intensity": 0.8    // 0.0 to 1.0
    }
  ],
  "debug": {
    "user_position": {"x": 5, "y": 5, "z": 1},
    "pointer_position": {"x": 5.2, "y": 8.3, "z": 2.1},
    "latency": 12,       // ms
    "calibrated": true
  },
  "timestamp": 1702650123500
}
```

---

# ⚠️ WARNINGS CRÍTICOS

## 1. Sistema de coordenadas Z-UP
**CRITICAL:** Este proyecto usa **Z como UP**, no Y

**Impacto:** Si portás código asumiendo Y-up, TODO se rompe.

**User position:** (5, 5, 1) = centro X, centro Y, 1m altura Z

---

## 2. Alpha Wraparound
**Alpha** es compass heading: 0° = North, 90° = East, 180° = South, 270° = West

**Problema:** 359° → 1° debe interpolar por 0°, NO por 180°

**Implementado en:** `LatencyBuffer` en websocket_handler.py

**Impacto:** Si removés esto, pointer "flipea" al cruzar North

---

## 3. Three.js r128 Locked
**NO actualizar a r169+** sin migrar completamente a ES modules

**Razón:** r128 usa global `THREE`, versiones modernas NO

**CDN actual:**
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
```

---

## 4. Calibration System
**Mobile sensor** necesita calibración para mapear orientación a venue ray

**Flujo UI:**
1. Usuario apunta teléfono hacia pantalla
2. Click "Calibrate"
3. Backend guarda (alpha, beta, gamma) actual como referencia
4. Todos los sensor readings futuros se transforman por matriz inversa

**Implementado en:** math_engine.py `get_calibration_matrix()`

---

## 5. File Structure Quirk
**Backend files están en ROOT**, no en `/backend/`

**Razón:** Facilita testing durante desarrollo:
```bash
python math_engine.py  # Runs tests directly
```

**Si reorganizás:** Actualizar todos los imports

---

## 6. Line Endings CRLF
**Todos los archivos frontend usan Windows line endings (CRLF)**

**Impacto:** Problemas con `str_replace` tool

**Solución al editar:**
```python
content.replace('\r\n', '\n')  # Normalizar
# ... editar ...
content.replace('\n', '\r\n')  # Restaurar
```

---

# 🧪 TEST COVERAGE

## Backend: 100% ✅
```
math_engine.py        8/8   ✅
venue_manager.py     10/10  ✅
fixture_manager.py   10/10  ✅
websocket_handler.py  8/8   ✅
server.py            Integration ✅
─────────────────────────────
TOTAL                36/36  ✅
```

## Frontend: 0% ❌
```
scene3d.js           0 tests ❌
main.js              0 tests ❌
websocket_client.js  0 tests ❌
mobile_sensor.js     0 tests ❌
─────────────────────────────
TOTAL                0 tests ❌
```

**Recomendación:** Agregar Jest o Vitest URGENTE

---

# 🐛 DEBUGGING GUIDE

## Start Server
```bash
cd /path/to/gyro-light-control
python server.py
```

**Expected:**
```
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## Run Backend Tests
```bash
python math_engine.py
python venue_manager.py
python fixture_manager.py
python websocket_handler.py
```

## Access Frontend
```
Desktop: http://localhost:8080
Mobile:  http://[YOUR_PC_IP]:8080/mobile.html
```

## Debug Frontend
**Chrome DevTools:**
- F12 → Console: Errores
- F12 → Network → WS: WebSocket messages
- Console: `console.log(THREE.REVISION)` → Debe ser "128"

---

# 📝 RECOMENDACIONES FINALES

## Para la Auditoría (Claude Code):

1. **Empezá por scene3d.js:**
   - Listar TODOS los métodos
   - Comparar con llamadas desde main.js
   - Identificar faltantes vs incompletos

2. **Revisá main.js handleStateUpdate():**
   - Validar conversión de formatos
   - Agregar logging extensivo
   - Verificar guards de null/undefined

3. **Plan incremental:**
   - Quick Wins primero (guards, try-catch)
   - Luego métodos faltantes
   - Finalmente tests

4. **NO toques backend:**
   - Si algo parece mal, primero verificá frontend
   - Backend tiene 100% test coverage, frontend 0%

---

## Transcripts Disponibles (Contexto adicional)

```
/mnt/transcripts/2025-12-16-04-28-57-gyro-light-phase0-backend-completion.txt
/mnt/transcripts/2025-12-16-04-29-37-frontend-integration-debugging.txt
/mnt/transcripts/journal.txt
```

Contienen:
- Prompts originales de cada módulo
- Especificaciones técnicas completas
- Criterios de validación
- Test cases esperados

---

# 🎯 RESUMEN EJECUTIVO

**Este proyecto tiene:**
- ✅ Backend sólido - Arquitectura modular, 100% testeado
- ⚠️ Frontend frágil - Implementación incompleta, 0% tests
- 🔴 Integración quebrada - Problemas de formato y métodos faltantes

**La auditoría debe enfocarse en:**
1. Completar scene3d.js (verificar TODOS los métodos)
2. Agregar tests frontend
3. Estandarizar contratos de datos
4. Agregar error boundaries

**Riesgo más alto:**  
Scene3D tiene métodos que existen pero están rotos, y métodos que no existen. Sin tests, es imposible saber qué funciona hasta que falla en runtime.

---

**Development Approach:** Multi-agent con Claude como "Registrador"  
**Current Status:** Backend complete, Frontend 70% working, Integration broken  
**Last Debug:** December 17, 2024 - Fixed 6 critical errors  
**Next Step:** Complete audit with Claude Code + Opus

---

# 🚀 PRIMER COMANDO (COPIAR EXACTO)

Una vez iniciado Claude Code con Opus, usar ESTE prompt exacto:

```
CONTEXTO:
- Lee create_prompt.md COMPLETO sin resumir nada
- Proyecto con backend 100% funcional, frontend 70% broken
- Construido por múltiples agentes sin coordinación perfecta
- Archivos críticos: frontend/js/scene3d.js y frontend/js/main.js

ROL:
Sos un Arquitecto Senior de Debugging especializado en código multi-agente.
Trabajás de manera meticulosa, sistemática y conservadora.

TAREA FASE 1 - AUDITORÍA (NO TOCAR CÓDIGO):

1. Analizar scene3d.js completo:
   - Listar TODOS los métodos definidos
   - Para cada método, verificar si está completo o incompleto
   - Identificar métodos llamados desde main.js que NO EXISTEN

2. Analizar main.js handleStateUpdate():
   - Documentar formato de datos que RECIBE del backend
   - Documentar formato que NECESITA scene3d.js
   - Identificar conversiones faltantes o incorrectas

3. Buscar referencias inseguras:
   - Cualquier this.objects.X sin validación
   - Cualquier método llamado sin verificar existencia
   - Cualquier acceso a propiedades sin guard

OUTPUT ESPERADO:

## 🔴 MÉTODOS FALTANTES (Criticidad ALTA)
- método() - Llamado en main.js:línea - ❌ NO EXISTE

## 🟠 MÉTODOS INCOMPLETOS (Criticidad MEDIA)  
- método() - Existe pero falta: [lógica específica]

## 🟡 PROBLEMAS DE FORMATO (Criticidad MEDIA)
Backend envía: {...}
Frontend espera: {...}
Conversión actual: [descripción]
Problema: [qué falla]

## ⚪ REFERENCIAS INSEGURAS (Criticidad BAJA)
Línea X: this.objects.Y sin guard
Línea Z: método() llamado sin verificar existencia

RESTRICCIONES:
- NO propongas soluciones todavía
- NO modifiques código
- NO asumas nada, verificá todo
- NO resumas create_prompt.md

TIEMPO ESTIMADO: 20-30 minutos

¿Comenzamos con la auditoría?
```

---

# 📋 COMANDOS SIGUIENTES (Después de Auditoría)

## Fase 2 - Quick Win #1: Guards

```
Basado en tu auditoría, implementá el Quick Win #1:

TAREA:
Agregar guards a TODAS las referencias inseguras que identificaste.

FORMATO:
// ANTES
this.objects.pointerRay.visible = true;

// DESPUÉS
if (this.objects?.pointerRay) {
  this.objects.pointerRay.visible = true;
} else {
  console.warn('pointerRay not initialized');
}

VALIDACIÓN:
Después de cada cambio, verificar:
1. Sintaxis OK (sin errores)
2. Console.warn aparece si objeto no existe
3. No hay TypeError en runtime

HAZLO UNO POR UNO y confirmá después de cada guard agregado.
```

## Fase 3 - Quick Win #2: Try-Catch

```
Agregar try-catch al render loop:

UBICACIÓN: scene3d.js método animate()

CÓDIGO:
animate() {
  try {
    requestAnimationFrame(this.animate.bind(this));
    
    if (this.controls) {
      this.controls.update();
    }
    
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  } catch (error) {
    console.error('🔴 Render loop error:', error);
    console.error('Stack:', error.stack);
    // NO romper el loop, seguir renderizando
    requestAnimationFrame(this.animate.bind(this));
  }
}

VALIDACIÓN:
1. Forzar un error intencional (ej: this.camera = null)
2. Verificar que console.error aparece
3. Verificar que render loop NO se rompe
4. Restaurar código correcto
```

## Fase 4 - Métodos Faltantes

```
Basado en tu auditoría, implementar métodos faltantes UNO A LA VEZ.

Para CADA método:

1. ANÁLISIS:
   - ¿Qué debe hacer? (basado en cómo se llama)
   - ¿Qué parámetros recibe?
   - ¿Qué debe retornar?
   
2. PROPUESTA:
   - Código con comentarios
   - Edge cases manejados
   - Validación de inputs
   
3. VALIDACIÓN:
   - ¿Cómo testeo manualmente?
   - ¿Qué console.log agregar?
   - ¿Qué debería ver en pantalla?

ESPERAR CONFIRMACIÓN antes de siguiente método.
```

---

# ⚠️ ERRORES COMUNES A EVITAR

## ❌ NO HACER:

1. **No hacer refactor masivo**
   ```javascript
   // ❌ MAL: Cambiar toda la arquitectura
   class Scene3DRefactored extends EventEmitter { ... }
   
   // ✅ BIEN: Fixes quirúrgicos
   if (!this.objects?.pointerRay) return;
   ```

2. **No asumir formatos de datos**
   ```javascript
   // ❌ MAL: Asumir sin verificar
   const x = data.pointer.position[0];
   
   // ✅ BIEN: Validar primero
   if (!data.pointer?.position || !Array.isArray(data.pointer.position)) {
     console.error('Invalid pointer format:', data.pointer);
     return;
   }
   const x = data.pointer.position[0];
   ```

3. **No tocar backend**
   ```python
   # ❌ MAL: "Mejorar" math_engine.py
   def euler_to_direction_vector_optimized(...):
   
   # ✅ BIEN: Backend está validado, dejar como está
   ```

4. **No hacer múltiples cambios simultáneos**
   ```javascript
   // ❌ MAL: 10 cambios en un commit
   - Agregué guards
   - Refactoricé render loop  
   - Cambié formato de fixtures
   - Actualicé Three.js
   
   // ✅ BIEN: Un cambio, validar, siguiente
   - Agregué guard a pointerRay
   [validar]
   - Agregué guard a pointerDot
   [validar]
   ```

---

# 🎓 TIPS DE EXPERIMENTADO

## Debugging Multi-Agente

**Problema típico:** Cada agente asume que otro hizo X, nadie lo hizo.

**Solución:** 
- Verificar EXISTENCIA antes de FUNCIONALIDAD
- Agregar logging extensivo en cada frontera
- No confiar en nombres de métodos (verificar implementación)

## Formato de Datos

**Problema típico:** Backend envía `{x, y, z}`, frontend espera `[x, y, z]`

**Solución:**
- Loggear SIEMPRE el formato recibido
- Agregar conversión defensiva
- Documentar el contrato en comentarios

```javascript
// Backend envía: {position: [x, y, z]}
// Frontend necesita: THREE.Vector3(x, y, z)
function convertPointer(backendPointer) {
  console.log('Received pointer format:', backendPointer);
  
  if (!backendPointer?.position) {
    console.error('Missing pointer.position');
    return null;
  }
  
  const [x, y, z] = backendPointer.position;
  return new THREE.Vector3(x, y, z);
}
```

## Testing Sin Framework

**Problema típico:** Sin tests, solo sabes que falló cuando crashea.

**Solución provisional:**
```javascript
// Agregar método de auto-test en scene3d.js
selfTest() {
  const issues = [];
  
  if (!this.scene) issues.push('scene not initialized');
  if (!this.camera) issues.push('camera not initialized');
  if (!this.renderer) issues.push('renderer not initialized');
  if (!this.objects) issues.push('objects not initialized');
  
  if (this.objects) {
    if (!this.objects.venue) issues.push('venue not created');
    if (!this.objects.user) issues.push('user not created');
    if (!this.objects.pointerRay) issues.push('pointerRay not created');
  }
  
  console.log('Scene3D Self-Test:', issues.length === 0 ? '✅ PASS' : '❌ FAIL');
  issues.forEach(issue => console.error('  -', issue));
  
  return issues.length === 0;
}

// Llamar después de init():
scene3d.init();
scene3d.selfTest();
```

## Rollback Rápido

**Siempre tener plan B:**

```bash
# Antes de cada cambio
git add .
git commit -m "Before: Adding guards to scene3d"

# Si algo se rompe
git reset --hard HEAD

# Si funcionó
git commit -m "After: Guards added successfully"
```

---

# 📞 SOPORTE

Si Claude Code se traba o no sigue instrucciones:

1. **Reiniciar sesión:**
   ```bash
   # Salir de Claude Code
   exit
   
   # Volver a entrar
   claude-code --model claude-opus-4
   
   # Volver a dar el primer comando
   ```

2. **Reducir scope:**
   ```
   En lugar de: "Audita todo el proyecto"
   Usar: "Audita SOLO scene3d.js, lista métodos definidos"
   ```

3. **Ser más explícito:**
   ```
   ❌ "Arregla scene3d"
   ✅ "Lee scene3d.js líneas 200-250, 
       identifica métodos que usan this.objects,
       lista cuáles NO validan existencia"
   ```

4. **Pedir formato específico:**
   ```
   "Dame la respuesta EXACTAMENTE en este formato:
   
   ## MÉTODOS DEFINIDOS
   - método1() - Línea X - Estado: [Completo/Incompleto]
   ...
   "
   ```

---

**¿LISTO PARA EMPEZAR?**

Seguí el workflow:
1. Inicializar Claude Code con configuración
2. Usar primer comando exacto
3. Esperar auditoría completa
4. Implementar Quick Wins uno por uno
5. Validar después de cada cambio

**Tiempo total estimado: 2-4 horas**  
**Resultado esperado: Frontend 100% funcional con logging + tests básicos**
