/**
 * Main.js - Integración principal del visualizador 3D
 * 
 * Integra:
 * - Scene3D (visualización 3D)
 * - WebSocketClient (comunicación con servidor)
 * - UI (panel de propiedades, sliders, console)
 */

// ============================================================================
// ESTADO GLOBAL
// ============================================================================

let scene3d = null;
let wsClient = null;
let lastUpdateTime = Date.now();
let frameCount = 0;

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Inicializando Gyro Light Control Visualizer...');

    initScene3D();
    initWebSocket();
    initUI();

    // Iniciar loop de renderizado
    animate();

    console.log('✅ Aplicación inicializada');
});

// ============================================================================
// SCENE 3D
// ============================================================================

function initScene3D() {
    const container = document.getElementById('scene-container');

    if (!container) {
        console.error('No se encontró #scene-container');
        return;
    }

    try {
        // Crear instancia de Scene3D (asume que ya está cargado desde scene3d.js)
        scene3d = new Scene3D(container);
        console.log('✅ Scene3D inicializado');

        // Escuchar eventos de selección de objetos
        scene3d.onObjectSelected = (selection) => {
            console.log('Objeto seleccionado:', selection);
            updatePropertiesPanel(selection);
        };

    } catch (error) {
        console.error('Error al inicializar Scene3D:', error);
        logToConsole('error', `Error al inicializar 3D: ${error.message}`);
    }
}

// ============================================================================
// WEBSOCKET
// ============================================================================

function initWebSocket() {
    // Determinar URL del WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws`;

    console.log(`Conectando a WebSocket: ${wsUrl}`);

    try {
        wsClient = new WebSocketClient(wsUrl);

        // Event listeners
        wsClient.on('connected', handleConnected);
        wsClient.on('disconnected', handleDisconnected);
        wsClient.on('state_update', handleStateUpdate);
        wsClient.on('calibration_result', handleCalibrationResult);
        wsClient.on('error', handleWSError);

        // Conectar
        wsClient.connect();

    } catch (error) {
        console.error('Error al inicializar WebSocket:', error);
        logToConsole('error', `Error WebSocket: ${error.message}`);
    }
}

async function handleConnected(data) {
    console.log('WebSocket conectado:', data);
    updateConnectionStatus(true);
    logToConsole('info', 'Conectado al servidor');
}

function handleDisconnected(data) {
    console.log('WebSocket desconectado:', data);
    updateConnectionStatus(false);
    logToConsole('warn', 'Desconectado del servidor');
}

function handleStateUpdate(data) {
    // Actualizar sensor data
    if (data.sensor) {
        updateSensorUI(data.sensor);
    }

    // Verificación robusta de Scene3D
    const isScene3DReady = scene3d && typeof scene3d.updatePointer === 'function';

    // Actualizar pointer en 3D
    if (data.pointer && isScene3DReady) {
        let intersection = null;

        if (Array.isArray(data.pointer)) {
            intersection = {
                point: new THREE.Vector3(data.pointer[0], data.pointer[1], data.pointer[2])
            };
        } else if (data.pointer.intersection && Array.isArray(data.pointer.intersection)) {
            const pos = data.pointer.intersection;
            intersection = {
                point: new THREE.Vector3(pos[0], pos[1], pos[2])
            };
        } else if (data.pointer.position && Array.isArray(data.pointer.position)) {
            const pos = data.pointer.position;
            intersection = {
                point: new THREE.Vector3(pos[0], pos[1], pos[2])
            };
        } else if (typeof data.pointer.x === 'number') {
            intersection = {
                point: new THREE.Vector3(data.pointer.x, data.pointer.y, data.pointer.z)
            };
        }

        if (intersection) {
            scene3d.updatePointer(intersection);
        }
    }

    // Actualizar debug info
    if (data.debug) {
        updateDebugUI(data.debug);
    }
}

function handleCalibrationResult(data) {
    console.log('Calibración completada:', data);
    logToConsole('info', `Calibración: ${data.success ? 'OK' : 'FALLO'}`);

    if (data.success) {
        alert('Calibración completada exitosamente');
    } else {
        alert('Error en calibración: ' + (data.error || 'Desconocido'));
    }
}

function handleWSError(error) {
    console.error('WebSocket error:', error);

    // Determinar tipo de error y mensaje apropiado
    let errorMsg = 'Error de conexión';
    if (error) {
        if (error.code === 1006) {
            errorMsg = 'Conexión cerrada inesperadamente (servidor caído?)';
        } else if (error.code === 1015) {
            errorMsg = 'Error de certificado TLS';
        } else if (error.message) {
            errorMsg = `Error: ${error.message}`;
        }
    }

    logToConsole('error', errorMsg);
    updateConnectionStatus(false);
}

// ============================================================================
// UI - CONNECTION STATUS
// ============================================================================

function updateConnectionStatus(connected) {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');

    if (indicator) {
        indicator.className = connected
            ? 'w-3 h-3 rounded-full bg-green-500'
            : 'w-3 h-3 rounded-full bg-red-500';
    }

    if (text) {
        text.textContent = connected ? 'Conectado' : 'Desconectado';
    }
}

// ============================================================================
// UI - SENSOR DATA
// ============================================================================

function updateSensorUI(sensor) {
    // Alpha
    const alphaSlider = document.getElementById('alpha-slider');
    const alphaValue = document.getElementById('alpha-value');
    if (alphaSlider && alphaValue) {
        alphaSlider.value = sensor.alpha || 0;
        alphaValue.textContent = (sensor.alpha || 0).toFixed(1);
    }

    // Beta
    const betaSlider = document.getElementById('beta-slider');
    const betaValue = document.getElementById('beta-value');
    if (betaSlider && betaValue) {
        betaSlider.value = sensor.beta || 0;
        betaValue.textContent = (sensor.beta || 0).toFixed(1);
    }

    // Gamma
    const gammaSlider = document.getElementById('gamma-slider');
    const gammaValue = document.getElementById('gamma-value');
    if (gammaSlider && gammaValue) {
        gammaSlider.value = sensor.gamma || 0;
        gammaValue.textContent = (sensor.gamma || 0).toFixed(1);
    }
}

// ============================================================================
// UI - DEBUG INFO
// ============================================================================

function updateDebugUI(debug) {
    // Helper para formatear posición con validación
    const formatPos = (pos) => {
        if (!pos || typeof pos.x !== 'number' || typeof pos.y !== 'number' || typeof pos.z !== 'number') {
            return '(--, --, --)';
        }
        return `(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`;
    };

    // User position
    const userPos = document.getElementById('debug-user-pos');
    if (userPos) {
        userPos.textContent = formatPos(debug.user_position);
    }

    // Pointer position
    const pointerPos = document.getElementById('debug-pointer-pos');
    if (pointerPos) {
        pointerPos.textContent = formatPos(debug.pointer_position);
    }

    // Latency
    const latency = document.getElementById('debug-latency');
    if (latency && typeof debug.latency === 'number') {
        latency.textContent = `${debug.latency.toFixed(0)} ms`;
    }

    // Calibrated
    const calibrated = document.getElementById('debug-calibrated');
    if (calibrated && debug.calibrated !== undefined) {
        calibrated.textContent = debug.calibrated ? 'Sí' : 'No';
    }
}

// ============================================================================
// UI - PROPERTIES PANEL
// ============================================================================

function updatePropertiesPanel(selection) {
    const panel = document.getElementById('properties-content');
    if (!panel) return;

    if (!selection) {
        panel.innerHTML = `
            <h2 class="text-lg font-bold mb-4">Propiedades</h2>
            <p class="text-gray-400 text-sm">Selecciona un objeto en la escena</p>
        `;
        return;
    }

    // Generar HTML según tipo de objeto
    let html = `<h2 class="text-lg font-bold mb-4">${selection.type || 'Objeto'}</h2>`;

    if (selection.type === 'venue' && scene3d) {
        // Usar venueSize de scene3d
        const size = scene3d.venueSize || { width: 10, depth: 10, height: 4 };
        html += `
            <div class="space-y-3">
                <div>
                    <label class="text-xs text-gray-400">Dimensiones</label>
                    <div class="text-sm font-mono">
                        ${size.width.toFixed(1)} x ${size.depth.toFixed(1)} x ${size.height.toFixed(1)} m
                    </div>
                </div>
            </div>
        `;
    } else if (selection.type === 'user' && selection.object) {
        // Mostrar info del usuario
        const pos = selection.object.position || { x: 0, y: 0, z: 0 };
        html += `
            <div class="space-y-3">
                <div>
                    <label class="text-xs text-gray-400">Posición</label>
                    <div class="text-sm font-mono">
                        (${pos.x.toFixed(2)}, ${pos.y.toFixed(2)}, ${pos.z.toFixed(2)})
                    </div>
                </div>
            </div>
        `;
    }

    panel.innerHTML = html;
}

// ============================================================================
// UI - CONSOLE
// ============================================================================

function logToConsole(level, message) {
    const consoleOutput = document.getElementById('console-output');
    if (!consoleOutput) return;

    const timestamp = new Date().toLocaleTimeString();
    const colors = {
        info: 'text-blue-400',
        warn: 'text-yellow-400',
        error: 'text-red-400'
    };

    const entry = document.createElement('div');
    entry.className = colors[level] || 'text-gray-400';
    entry.textContent = `[${timestamp}] ${message}`;

    consoleOutput.appendChild(entry);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

// ============================================================================
// UI - TOOLBAR BUTTONS
// ============================================================================

function initUI() {
    // Calibrate button
    const btnCalibrate = document.getElementById('btn-calibrate');
    if (btnCalibrate) {
        btnCalibrate.addEventListener('click', () => {
            if (wsClient && wsClient.connected) {
                wsClient.send({ type: 'calibrate_request' });
                logToConsole('info', 'Solicitando calibración...');
            } else {
                alert('No conectado al servidor');
            }
        });
    }

    // Reset button
    const btnReset = document.getElementById('btn-reset');
    if (btnReset) {
        btnReset.addEventListener('click', () => {
            if (confirm('¿Resetear escena?')) {
                if (wsClient && wsClient.connected) {
                    wsClient.send({ type: 'reset_request' });
                    logToConsole('info', 'Reseteando escena...');
                }
            }
        });
    }

    // Console clear button
    const btnClear = document.getElementById('console-clear');
    if (btnClear) {
        btnClear.addEventListener('click', () => {
            const consoleOutput = document.getElementById('console-output');
            if (consoleOutput) {
                consoleOutput.innerHTML = '';
            }
        });
    }

    console.log('✅ UI inicializada');
}

// ============================================================================
// ANIMATION LOOP
// ============================================================================

function animate() {
    requestAnimationFrame(animate);

    // Renderizar escena
    if (scene3d) {
        scene3d.render();
    }

    // Actualizar FPS counter
    frameCount++;
    const now = Date.now();
    if (now - lastUpdateTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / (now - lastUpdateTime));
        const fpsCounter = document.getElementById('fps-counter');
        if (fpsCounter) {
            fpsCounter.textContent = fps;
        }

        frameCount = 0;
        lastUpdateTime = now;
    }
}

// ============================================================================
// WINDOW RESIZE
// ============================================================================

function handleWindowResize() {
    if (scene3d) {
        scene3d.resize();
    }
}

window.addEventListener('resize', handleWindowResize);

// ============================================================================
// CLEANUP (llamar antes de destruir la aplicación)
// ============================================================================

function cleanup() {
    console.log('🧹 Limpiando recursos...');

    // Remover listener de resize
    window.removeEventListener('resize', handleWindowResize);

    // Desconectar WebSocket
    if (wsClient) {
        wsClient.disconnect();
        wsClient = null;
    }

    // Disponer Scene3D
    if (scene3d) {
        scene3d.dispose();
        scene3d = null;
    }

    console.log('✅ Recursos liberados');
}

// Limpiar al cerrar/recargar la página
window.addEventListener('beforeunload', cleanup);