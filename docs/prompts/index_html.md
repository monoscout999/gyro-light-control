# PROMPT: Implementar index.html - Interfaz Desktop Principal

## CONTEXTO DEL PROYECTO

Estás implementando la interfaz HTML principal del visualizador desktop. Esta es la página que se abre en el navegador y contiene toda la UI: viewport 3D, panels de control, consola debug, etc.

Este archivo INTEGRA todos los módulos frontend.

---

## TU TAREA

Crear el archivo `index.html` con:
- Estructura HTML completa
- Layout según especificaciones (viewport 70% + panel 30%)
- Todos los elementos UI necesarios
- Imports de Three.js, scene3d.js, websocket_client.js
- Estilos Tailwind CSS (dark mode)
- JavaScript de integración básico

---

## LAYOUT REQUERIDO

```
┌────────────────────────────────────────────┐
│ TOOLBAR: [Calibrar][Reset][Guardar][Cargar]│
├──────────────────────┬─────────────────────┤
│                      │                     │
│  VIEWPORT 3D (70%)   │  PROPERTIES (30%)   │
│  #scene-container    │  #properties-panel  │
│                      │                     │
│                      │                     │
├──────────────────────┴─────────────────────┤
│ BOTTOM PANEL (250px fixed)                 │
│ ┌───────┬──────────┬──────────┐           │
│ │SENSOR │DEBUG INFO│ CONSOLE  │           │
│ └───────┴──────────┴──────────┘           │
└────────────────────────────────────────────┘
```

---

## HTML COMPLETO

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gyro Light Control - Visualizer</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Three.js -->
    <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
    
    <style>
        body {
            margin: 0;
            overflow: hidden;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
        }
        
        #scene-container {
            width: 100%;
            height: 100%;
        }
        
        #scene-container canvas {
            display: block;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #2d2d2d;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #4a4a4a;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #5a5a5a;
        }
        
        /* Progress bar styling */
        input[type="range"] {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 6px;
            background: #3a3a3a;
            outline: none;
            border-radius: 3px;
        }
        
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            background: #4a9eff;
            cursor: pointer;
            border-radius: 50%;
        }
    </style>
</head>
<body class="bg-gray-900 text-gray-200">
    
    <!-- MAIN LAYOUT -->
    <div class="flex flex-col h-screen">
        
        <!-- TOOLBAR -->
        <div class="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center gap-2">
            <h1 class="text-lg font-bold mr-4">Gyro Light Control</h1>
            
            <button id="btn-calibrate" 
                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium">
                Calibrar
            </button>
            
            <button id="btn-reset" 
                    class="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-sm font-medium">
                Reset
            </button>
            
            <button id="btn-save" 
                    class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm font-medium">
                Guardar
            </button>
            
            <button id="btn-load" 
                    class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded text-sm font-medium">
                Cargar
            </button>
            
            <div class="flex-1"></div>
            
            <!-- Connection status -->
            <div id="connection-status" class="flex items-center gap-2">
                <div id="status-indicator" class="w-3 h-3 rounded-full bg-red-500"></div>
                <span id="status-text" class="text-sm">Desconectado</span>
            </div>
        </div>
        
        <!-- MAIN CONTENT -->
        <div class="flex flex-1 overflow-hidden">
            
            <!-- VIEWPORT 3D (70%) -->
            <div class="flex-[7] bg-gray-900 relative">
                <div id="scene-container" class="w-full h-full"></div>
                
                <!-- FPS counter (overlay) -->
                <div class="absolute top-2 left-2 bg-black bg-opacity-50 px-2 py-1 rounded text-xs">
                    FPS: <span id="fps-counter">60</span>
                </div>
            </div>
            
            <!-- PROPERTIES PANEL (30%) -->
            <div class="flex-[3] bg-gray-800 border-l border-gray-700 overflow-y-auto">
                <div id="properties-panel" class="p-4">
                    <!-- Contenido dinámico según objeto seleccionado -->
                    <div id="properties-content">
                        <h2 class="text-lg font-bold mb-4">Propiedades</h2>
                        <p class="text-gray-400 text-sm">Selecciona un objeto en la escena</p>
                    </div>
                </div>
            </div>
            
        </div>
        
        <!-- BOTTOM PANEL (250px fixed) -->
        <div class="h-[250px] bg-gray-800 border-t border-gray-700 flex">
            
            <!-- SENSOR DATA (33%) -->
            <div class="flex-1 border-r border-gray-700 p-4 overflow-y-auto">
                <h3 class="text-sm font-bold mb-3">Datos del Sensor</h3>
                
                <!-- Alpha -->
                <div class="mb-3">
                    <label class="text-xs text-gray-400">Alpha (0-360°)</label>
                    <input type="range" id="alpha-slider" min="0" max="360" value="0" disabled>
                    <div class="text-right text-sm mt-1">
                        <span id="alpha-value">0.0</span>°
                    </div>
                </div>
                
                <!-- Beta -->
                <div class="mb-3">
                    <label class="text-xs text-gray-400">Beta (-180 a 180°)</label>
                    <input type="range" id="beta-slider" min="-180" max="180" value="0" disabled>
                    <div class="text-right text-sm mt-1">
                        <span id="beta-value">0.0</span>°
                    </div>
                </div>
                
                <!-- Gamma -->
                <div class="mb-3">
                    <label class="text-xs text-gray-400">Gamma (-90 a 90°)</label>
                    <input type="range" id="gamma-slider" min="-90" max="90" value="0" disabled>
                    <div class="text-right text-sm mt-1">
                        <span id="gamma-value">0.0</span>°
                    </div>
                </div>
            </div>
            
            <!-- DEBUG INFO (33%) -->
            <div class="flex-1 border-r border-gray-700 p-4 overflow-y-auto">
                <h3 class="text-sm font-bold mb-3">Info de Debug</h3>
                
                <div class="space-y-2 text-xs">
                    <div>
                        <span class="text-gray-400">Usuario:</span><br>
                        <span id="debug-user-pos" class="font-mono">(5.0, 5.0, 1.0)</span>
                    </div>
                    
                    <div>
                        <span class="text-gray-400">Pointer:</span><br>
                        <span id="debug-pointer-pos" class="font-mono">(--, --, --)</span>
                    </div>
                    
                    <div>
                        <span class="text-gray-400">Latencia:</span>
                        <span id="debug-latency" class="font-mono">-- ms</span>
                    </div>
                    
                    <div>
                        <span class="text-gray-400">Calibrado:</span>
                        <span id="debug-calibrated" class="font-mono">No</span>
                    </div>
                </div>
            </div>
            
            <!-- CONSOLE (33%) -->
            <div class="flex-1 p-4 flex flex-col">
                <div class="flex items-center justify-between mb-2">
                    <h3 class="text-sm font-bold">Consola</h3>
                    <div class="flex gap-1">
                        <button id="filter-info" class="px-2 py-1 text-xs bg-blue-600 rounded">Info</button>
                        <button id="filter-warn" class="px-2 py-1 text-xs bg-yellow-600 rounded">Warn</button>
                        <button id="filter-error" class="px-2 py-1 text-xs bg-red-600 rounded">Error</button>
                        <button id="console-clear" class="px-2 py-1 text-xs bg-gray-600 rounded">Clear</button>
                    </div>
                </div>
                
                <div id="console-output" class="flex-1 bg-black bg-opacity-30 rounded p-2 overflow-y-auto text-xs font-mono">
                    <!-- Log entries dinámicos -->
                </div>
            </div>
            
        </div>
        
    </div>
    
    <!-- SCRIPTS -->
    <script src="js/websocket_client.js"></script>
    <script src="js/scene3d.js"></script>
    <script src="js/main.js"></script>
    
</body>
</html>
```

---

## JAVASCRIPT BÁSICO DE INTEGRACIÓN (main.js)

Este archivo conecta todo:

```javascript
/**
 * main.js - Integración principal
 * 
 * Conecta scene3d, websocket_client, y UI
 */

// Estado global
const app = {
    scene3d: null,
    wsClient: null,
    state: {
        connected: false,
        calibrated: false,
        lastSensorData: null,
        selectedObject: null
    }
};

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando Gyro Light Control Visualizer');
    
    // Inicializar escena 3D
    const container = document.getElementById('scene-container');
    app.scene3d = new Scene3D(container);
    
    // Callback de selección
    app.scene3d.onObjectSelected = (selection) => {
        console.log('Objeto seleccionado:', selection);
        app.state.selectedObject = selection;
        updatePropertiesPanel(selection);
    };
    
    // Inicializar WebSocket
    app.wsClient = new WebSocketClient('ws://localhost:8080/ws');
    
    // Event listeners de WebSocket
    app.wsClient.on('connected', () => {
        updateConnectionStatus(true);
        consoleLog('✅ Conectado al servidor', 'info');
    });
    
    app.wsClient.on('disconnected', () => {
        updateConnectionStatus(false);
        consoleLog('❌ Desconectado del servidor', 'error');
    });
    
    app.wsClient.on('state_update', (data) => {
        handleStateUpdate(data);
    });
    
    app.wsClient.on('calibration_result', (data) => {
        if (data.success) {
            app.state.calibrated = true;
            consoleLog('✅ Calibración exitosa', 'info');
        } else {
            consoleLog('❌ Calibración fallida', 'error');
        }
    });
    
    // Conectar
    app.wsClient.connect();
    
    // Toolbar buttons
    document.getElementById('btn-calibrate').onclick = handleCalibrate;
    document.getElementById('btn-reset').onclick = handleReset;
    document.getElementById('btn-save').onclick = handleSave;
    document.getElementById('btn-load').onclick = handleLoad;
    
    // Console filters
    document.getElementById('filter-info').onclick = () => toggleFilter('info');
    document.getElementById('filter-warn').onclick = () => toggleFilter('warn');
    document.getElementById('filter-error').onclick = () => toggleFilter('error');
    document.getElementById('console-clear').onclick = () => clearConsole();
    
    consoleLog('Sistema inicializado', 'info');
});

// Handlers
function handleStateUpdate(data) {
    // Actualizar sliders de sensor
    if (data.sensor) {
        updateSensorSliders(data.sensor);
        app.state.lastSensorData = data.sensor;
    }
    
    // Actualizar pointer en 3D
    if (data.pointer) {
        app.scene3d.updatePointer(
            data.pointer.direction,
            data.pointer.intersection
        );
        
        // Debug info
        document.getElementById('debug-pointer-pos').textContent = 
            `(${data.pointer.intersection[0].toFixed(1)}, ${data.pointer.intersection[1].toFixed(1)}, ${data.pointer.intersection[2].toFixed(1)})`;
    }
    
    // Actualizar fixtures
    if (data.fixtures) {
        data.fixtures.forEach(fixture => {
            app.scene3d.updateFixture(fixture.id, fixture.pan, fixture.tilt);
        });
    }
    
    // Estado de calibración
    if (data.calibrated !== undefined) {
        app.state.calibrated = data.calibrated;
        document.getElementById('debug-calibrated').textContent = 
            data.calibrated ? 'Sí' : 'No';
    }
}

function updateSensorSliders(sensor) {
    document.getElementById('alpha-slider').value = sensor.alpha;
    document.getElementById('alpha-value').textContent = sensor.alpha.toFixed(1);
    
    document.getElementById('beta-slider').value = sensor.beta;
    document.getElementById('beta-value').textContent = sensor.beta.toFixed(1);
    
    document.getElementById('gamma-slider').value = sensor.gamma;
    document.getElementById('gamma-value').textContent = sensor.gamma.toFixed(1);
}

function handleCalibrate() {
    if (!app.state.lastSensorData) {
        consoleLog('⚠️ No hay datos del sensor para calibrar', 'warn');
        return;
    }
    
    app.wsClient.send({
        type: 'calibrate',
        ...app.state.lastSensorData
    });
    
    consoleLog('Calibrando...', 'info');
}

function handleReset() {
    app.scene3d.resetCamera();
    consoleLog('Cámara reseteada', 'info');
}

function handleSave() {
    // TODO: Implementar guardar escena
    consoleLog('⚠️ Función guardar no implementada aún', 'warn');
}

function handleLoad() {
    // TODO: Implementar cargar escena
    consoleLog('⚠️ Función cargar no implementada aún', 'warn');
}

// UI Utilities
function updateConnectionStatus(connected) {
    app.state.connected = connected;
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    
    if (connected) {
        indicator.className = 'w-3 h-3 rounded-full bg-green-500';
        text.textContent = 'Conectado';
    } else {
        indicator.className = 'w-3 h-3 rounded-full bg-red-500';
        text.textContent = 'Desconectado';
    }
}

function updatePropertiesPanel(selection) {
    const panel = document.getElementById('properties-content');
    
    if (!selection) {
        panel.innerHTML = `
            <h2 class="text-lg font-bold mb-4">Propiedades</h2>
            <p class="text-gray-400 text-sm">Selecciona un objeto en la escena</p>
        `;
        return;
    }
    
    // TODO: Renderizar propiedades según tipo de objeto
    panel.innerHTML = `
        <h2 class="text-lg font-bold mb-4">${selection.type}</h2>
        <p class="text-sm">ID: ${selection.id || 'N/A'}</p>
    `;
}

function consoleLog(message, type = 'info') {
    const output = document.getElementById('console-output');
    const time = new Date().toLocaleTimeString();
    
    const colors = {
        info: 'text-blue-400',
        warn: 'text-yellow-400',
        error: 'text-red-400'
    };
    
    const entry = document.createElement('div');
    entry.className = `console-entry console-${type} ${colors[type]}`;
    entry.innerHTML = `<span class="text-gray-500">[${time}]</span> ${message}`;
    
    output.appendChild(entry);
    output.scrollTop = output.scrollHeight;
    
    // Limitar a 100 mensajes
    while (output.children.length > 100) {
        output.removeChild(output.firstChild);
    }
}

function clearConsole() {
    document.getElementById('console-output').innerHTML = '';
}

function toggleFilter(type) {
    // TODO: Implementar filtros de consola
    console.log('Toggle filter:', type);
}
```

---

## CRITERIOS DE VALIDACIÓN

- [ ] HTML renderiza correctamente
- [ ] Layout responsive (70%/30%)
- [ ] Tailwind CSS carga y aplica estilos
- [ ] Three.js carga sin errores
- [ ] scene3d.js se inicializa
- [ ] WebSocket conecta al servidor
- [ ] Sliders muestran valores
- [ ] Consola funciona
- [ ] Botones responden
- [ ] Connection status actualiza

---

## NOTAS IMPORTANTES

1. **CDN Dependencies**:
   - Tailwind CSS
   - Three.js + OrbitControls
   - Todo desde CDN (sin npm)

2. **Dark Mode**:
   - Colores oscuros por default
   - Fondo #1a1a1a

3. **Responsive**:
   - Flex layout
   - Escala con ventana

4. **TODO**:
   - Guardar/Cargar escenas
   - Filtros de consola
   - Panel propiedades completo

---

## TIEMPO ESTIMADO

**20-30 minutos**

---

**ENTREGA**: `index.html` + `main.js` completos, página carga sin errores, UI funcional.
