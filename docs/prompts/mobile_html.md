# PROMPT: Implementar mobile.html - Interfaz Móvil para Sensor

## CONTEXTO DEL PROYECTO

Estás implementando la interfaz móvil que accede al giroscopio del celular y envía los datos al servidor. Esta es una página web simple que se abre en el navegador del celular y permite enviar datos del sensor en tiempo real.

---

## TU TAREA

Crear el archivo `mobile.html` con:
- Acceso a DeviceOrientation API (giroscopio)
- UI minimalista con botones grandes
- Indicadores visuales de alpha, beta, gamma
- Botón de calibración
- Conexión WebSocket al servidor
- Envío automático de datos (30 FPS)

---

## ESPECIFICACIONES

### DeviceOrientation API

```javascript
// Evento del navegador
window.addEventListener('deviceorientation', (event) => {
    const alpha = event.alpha;  // 0-360° (compass)
    const beta = event.beta;    // -180 a 180° (pitch)
    const gamma = event.gamma;  // -90 a 90° (roll)
    
    // Enviar al servidor
});
```

### UI Mínima

```
┌─────────────────────────┐
│   GYRO LIGHT CONTROL    │
├─────────────────────────┤
│                         │
│   ● CONECTADO           │
│                         │
│   α: 245.3°             │
│   β: -12.7°             │
│   γ: 3.2°               │
│                         │
│   [ CALIBRAR ]          │
│                         │
└─────────────────────────┘
```

---

## HTML COMPLETO

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <title>Gyro Light Control - Mobile</title>
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            -webkit-user-select: none;
            user-select: none;
        }
        
        .header {
            background: #2d2d2d;
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #4a9eff;
        }
        
        .header h1 {
            font-size: 20px;
            font-weight: bold;
        }
        
        .status {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
            font-size: 14px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ef4444;
            transition: background 0.3s;
        }
        
        .status-indicator.connected {
            background: #4ade80;
        }
        
        .content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .sensor-display {
            width: 100%;
            max-width: 400px;
            background: #2d2d2d;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
        }
        
        .sensor-value {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #3a3a3a;
            font-size: 24px;
        }
        
        .sensor-value:last-child {
            border-bottom: none;
        }
        
        .sensor-label {
            font-weight: bold;
            color: #4a9eff;
        }
        
        .sensor-number {
            font-family: 'Courier New', monospace;
            color: #e0e0e0;
        }
        
        .button-group {
            width: 100%;
            max-width: 400px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        button {
            padding: 20px;
            font-size: 18px;
            font-weight: bold;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            -webkit-tap-highlight-color: transparent;
        }
        
        button:active {
            transform: scale(0.95);
        }
        
        .btn-calibrate {
            background: #4a9eff;
            color: white;
        }
        
        .btn-calibrate:disabled {
            background: #3a3a3a;
            color: #6a6a6a;
        }
        
        .btn-permission {
            background: #4ade80;
            color: #1a1a1a;
        }
        
        .permission-warning {
            background: #fbbf24;
            color: #1a1a1a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 14px;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    
    <!-- HEADER -->
    <div class="header">
        <h1>GYRO LIGHT CONTROL</h1>
        <div class="status">
            <div id="status-indicator" class="status-indicator"></div>
            <span id="status-text">Desconectado</span>
        </div>
    </div>
    
    <!-- CONTENT -->
    <div class="content">
        
        <!-- Permission warning -->
        <div id="permission-warning" class="permission-warning hidden">
            Este dispositivo requiere permiso para acceder al giroscopio.
            Por favor, toca el botón de abajo.
        </div>
        
        <!-- Sensor display -->
        <div class="sensor-display">
            <div class="sensor-value">
                <span class="sensor-label">α (Alpha)</span>
                <span id="alpha-value" class="sensor-number">0.0°</span>
            </div>
            <div class="sensor-value">
                <span class="sensor-label">β (Beta)</span>
                <span id="beta-value" class="sensor-number">0.0°</span>
            </div>
            <div class="sensor-value">
                <span class="sensor-label">γ (Gamma)</span>
                <span id="gamma-value" class="sensor-number">0.0°</span>
            </div>
        </div>
        
        <!-- Buttons -->
        <div class="button-group">
            <button id="btn-permission" class="btn-permission hidden">
                Activar Sensor
            </button>
            
            <button id="btn-calibrate" class="btn-calibrate" disabled>
                CALIBRAR
            </button>
        </div>
        
    </div>
    
    <!-- SCRIPTS -->
    <script>
        // Estado global
        const app = {
            wsClient: null,
            connected: false,
            sensorActive: false,
            lastSensorData: { alpha: 0, beta: 0, gamma: 0 },
            sendInterval: null
        };
        
        // ====================================================================
        // WEBSOCKET
        // ====================================================================
        
        class SimpleWebSocket {
            constructor(url) {
                this.url = url;
                this.ws = null;
                this.connected = false;
                this.onConnected = null;
                this.onDisconnected = null;
            }
            
            connect() {
                this.ws = new WebSocket(this.url);
                
                this.ws.onopen = () => {
                    this.connected = true;
                    console.log('WebSocket conectado');
                    if (this.onConnected) this.onConnected();
                };
                
                this.ws.onclose = () => {
                    this.connected = false;
                    console.log('WebSocket desconectado');
                    if (this.onDisconnected) this.onDisconnected();
                    
                    // Reconectar después de 3 segundos
                    setTimeout(() => this.connect(), 3000);
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };
            }
            
            send(data) {
                if (this.connected && this.ws) {
                    this.ws.send(JSON.stringify(data));
                }
            }
        }
        
        // ====================================================================
        // SENSOR
        // ====================================================================
        
        function initSensor() {
            // Detectar si necesita permiso (iOS 13+)
            if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                document.getElementById('permission-warning').classList.remove('hidden');
                document.getElementById('btn-permission').classList.remove('hidden');
                return;
            }
            
            // Directamente activar sensor
            activateSensor();
        }
        
        async function requestPermission() {
            try {
                const permission = await DeviceOrientationEvent.requestPermission();
                
                if (permission === 'granted') {
                    document.getElementById('permission-warning').classList.add('hidden');
                    document.getElementById('btn-permission').classList.add('hidden');
                    activateSensor();
                } else {
                    alert('Permiso denegado. No se puede acceder al giroscopio.');
                }
            } catch (error) {
                console.error('Error al pedir permiso:', error);
                alert('Error al pedir permiso: ' + error.message);
            }
        }
        
        function activateSensor() {
            window.addEventListener('deviceorientation', handleOrientation, true);
            app.sensorActive = true;
            
            // Habilitar botón de calibración
            document.getElementById('btn-calibrate').disabled = false;
            
            // Iniciar envío periódico
            app.sendInterval = setInterval(sendSensorData, 33);  // ~30 FPS
            
            console.log('Sensor activado');
        }
        
        function handleOrientation(event) {
            // Capturar datos del sensor
            app.lastSensorData = {
                alpha: event.alpha || 0,
                beta: event.beta || 0,
                gamma: event.gamma || 0
            };
            
            // Actualizar UI
            updateSensorDisplay(app.lastSensorData);
        }
        
        function updateSensorDisplay(data) {
            document.getElementById('alpha-value').textContent = data.alpha.toFixed(1) + '°';
            document.getElementById('beta-value').textContent = data.beta.toFixed(1) + '°';
            document.getElementById('gamma-value').textContent = data.gamma.toFixed(1) + '°';
        }
        
        function sendSensorData() {
            if (!app.connected || !app.sensorActive) return;
            
            app.wsClient.send({
                type: 'sensor_data',
                alpha: app.lastSensorData.alpha,
                beta: app.lastSensorData.beta,
                gamma: app.lastSensorData.gamma,
                timestamp: Date.now()
            });
        }
        
        // ====================================================================
        // CALIBRACIÓN
        // ====================================================================
        
        function calibrate() {
            if (!app.connected) {
                alert('No conectado al servidor');
                return;
            }
            
            app.wsClient.send({
                type: 'calibrate',
                alpha: app.lastSensorData.alpha,
                beta: app.lastSensorData.beta,
                gamma: app.lastSensorData.gamma
            });
            
            // Feedback visual
            const btn = document.getElementById('btn-calibrate');
            btn.textContent = '✓ CALIBRADO';
            btn.style.background = '#4ade80';
            
            setTimeout(() => {
                btn.textContent = 'CALIBRAR';
                btn.style.background = '#4a9eff';
            }, 2000);
        }
        
        // ====================================================================
        // UI
        // ====================================================================
        
        function updateConnectionStatus(connected) {
            app.connected = connected;
            
            const indicator = document.getElementById('status-indicator');
            const text = document.getElementById('status-text');
            
            if (connected) {
                indicator.classList.add('connected');
                text.textContent = 'Conectado';
            } else {
                indicator.classList.remove('connected');
                text.textContent = 'Desconectado';
            }
        }
        
        // ====================================================================
        // INICIALIZACIÓN
        // ====================================================================
        
        window.addEventListener('DOMContentLoaded', () => {
            console.log('Mobile interface iniciada');
            
            // Obtener IP del servidor desde URL o usar default
            const urlParams = new URLSearchParams(window.location.search);
            const serverIP = urlParams.get('server') || 'localhost';
            const wsUrl = `ws://${serverIP}:8080/ws`;
            
            console.log('Conectando a:', wsUrl);
            
            // Inicializar WebSocket
            app.wsClient = new SimpleWebSocket(wsUrl);
            app.wsClient.onConnected = () => updateConnectionStatus(true);
            app.wsClient.onDisconnected = () => updateConnectionStatus(false);
            app.wsClient.connect();
            
            // Inicializar sensor
            initSensor();
            
            // Event listeners
            document.getElementById('btn-permission').onclick = requestPermission;
            document.getElementById('btn-calibrate').onclick = calibrate;
        });
        
        // Evitar que la pantalla se apague
        if ('wakeLock' in navigator) {
            navigator.wakeLock.request('screen').catch(err => {
                console.log('WakeLock no disponible:', err);
            });
        }
    </script>
    
</body>
</html>
```

---

## USO

### Desde el celular:

1. **Conectar celular y PC a misma red WiFi**

2. **Obtener IP del servidor:**
   ```bash
   # En PC con servidor corriendo
   ipconfig  # Windows
   ifconfig  # Mac/Linux
   # Ejemplo: 192.168.1.10
   ```

3. **Abrir en navegador del celular:**
   ```
   http://192.168.1.10:8080/mobile.html
   
   # O con parámetro:
   http://192.168.1.10:8080/mobile.html?server=192.168.1.10
   ```

4. **iOS: Dar permiso al sensor**
   - Tocar "Activar Sensor"
   - Permitir acceso

5. **Android: Funciona automáticamente**

6. **Calibrar:**
   - Apuntar al centro de pared trasera
   - Pantalla hacia arriba
   - Tocar "CALIBRAR"

---

## CRITERIOS DE VALIDACIÓN

- [ ] HTML carga en navegador móvil
- [ ] Detecta necesidad de permiso (iOS)
- [ ] Accede a DeviceOrientation API
- [ ] Muestra valores de alpha, beta, gamma
- [ ] Conecta al servidor vía WebSocket
- [ ] Envía datos a 30 FPS
- [ ] Botón calibrar funciona
- [ ] UI responsive en móvil
- [ ] Reconexión automática funciona
- [ ] Pantalla no se apaga (wakeLock)

---

## NOTAS IMPORTANTES

1. **iOS vs Android**:
   - iOS 13+: Requiere permiso explícito
   - Android: Funciona directamente

2. **HTTPS en producción**:
   - DeviceOrientation requiere HTTPS en producción
   - En desarrollo (localhost) funciona con HTTP

3. **Misma red**:
   - Celular y servidor deben estar en misma WiFi
   - O usar túnel (ngrok, localtunnel)

4. **WakeLock**:
   - Evita que pantalla se apague
   - Útil para uso prolongado

5. **Orientación**:
   - Landscape o portrait funciona
   - Valores se adaptan automáticamente

---

## TIEMPO ESTIMADO

**15-20 minutos**

---

**ENTREGA**: Archivo `mobile.html` completo, funcional en navegador móvil, enviando datos del sensor.
