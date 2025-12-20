# PROMPT: Implementar websocket_client.js - Cliente WebSocket Frontend

## CONTEXTO DEL PROYECTO

Estás implementando el cliente WebSocket del frontend que se conecta al servidor Python. Este módulo gestiona la conexión, reconexiones automáticas, envío/recepción de mensajes, y emite events para que otros módulos reaccionen.

---

## TU TAREA

Crear el archivo `websocket_client.js` con:
- Conexión WebSocket al servidor
- Reconexión automática con backoff
- Sistema de eventos (EventEmitter pattern)
- Envío/recepción de mensajes JSON
- Heartbeat (ping/pong)
- Manejo de errores

---

## ESPECIFICACIONES

### Mensajes Enviados (Frontend → Backend)

```javascript
// Datos del sensor (desde mobile)
{
  type: 'sensor_data',
  alpha: 245.3,
  beta: -12.7,
  gamma: 3.2,
  timestamp: Date.now()
}

// Calibración
{
  type: 'calibrate',
  alpha: 180,
  beta: 0,
  gamma: 0
}

// Heartbeat
{
  type: 'ping'
}
```

### Mensajes Recibidos (Backend → Frontend)

```javascript
// Estado actualizado
{
  type: 'state_update',
  sensor: {...},
  pointer: {...},
  fixtures: [...]
}

// Resultado calibración
{
  type: 'calibration_result',
  success: true,
  message: '...'
}

// Conexión establecida
{
  type: 'connected',
  message: '...'
}

// Heartbeat response
{
  type: 'pong'
}
```

---

## CLASE WEBSOCKETCLIENT

```javascript
/**
 * WebSocketClient - Cliente WebSocket con reconexión automática
 * 
 * Patrón EventEmitter para notificar a otros módulos
 */
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        
        // Estado
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 2000;  // ms
        this.reconnectTimeout = null;
        
        // Heartbeat
        this.heartbeatInterval = null;
        this.heartbeatIntervalTime = 30000;  // 30s
        
        // Event callbacks
        this.eventListeners = {};
    }
    
    /**
     * Conectar al servidor WebSocket
     */
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.warn('WebSocket ya está conectado');
            return;
        }
        
        console.log(`Conectando a ${this.url}...`);
        
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => this.handleOpen();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onerror = (error) => this.handleError(error);
            this.ws.onclose = (event) => this.handleClose(event);
            
        } catch (error) {
            console.error('Error al crear WebSocket:', error);
            this.scheduleReconnect();
        }
    }
    
    /**
     * Desconectar del servidor
     */
    disconnect() {
        this.maxReconnectAttempts = 0;  // Deshabilitar reconexión
        
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        this.connected = false;
    }
    
    /**
     * Enviar mensaje al servidor
     */
    send(data) {
        if (!this.connected || !this.ws) {
            console.warn('No conectado, no se puede enviar:', data);
            return false;
        }
        
        try {
            this.ws.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Error al enviar mensaje:', error);
            return false;
        }
    }
    
    /**
     * Registrar listener para eventos
     * 
     * @param {String} event - Nombre del evento
     * @param {Function} callback - Función a llamar
     * 
     * Eventos disponibles:
     * - 'connected': Se conectó al servidor
     * - 'disconnected': Se desconectó
     * - 'state_update': Actualización de estado
     * - 'calibration_result': Resultado de calibración
     * - 'error': Error de WebSocket
     * - 'message': Cualquier mensaje (catch-all)
     */
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }
    
    /**
     * Emitir evento a listeners
     */
    emit(event, data) {
        const listeners = this.eventListeners[event];
        if (!listeners) return;
        
        listeners.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error en listener de '${event}':`, error);
            }
        });
    }
    
    // ========================================================================
    // HANDLERS INTERNOS
    // ========================================================================
    
    handleOpen() {
        console.log('✅ WebSocket conectado');
        
        this.connected = true;
        this.reconnectAttempts = 0;
        
        // Iniciar heartbeat
        this.startHeartbeat();
        
        // Emitir evento
        this.emit('connected', { url: this.url });
    }
    
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Emitir evento genérico
            this.emit('message', data);
            
            // Emitir evento específico según type
            if (data.type) {
                this.emit(data.type, data);
            }
            
        } catch (error) {
            console.error('Error al parsear mensaje:', error);
        }
    }
    
    handleError(error) {
        console.error('❌ WebSocket error:', error);
        this.emit('error', error);
    }
    
    handleClose(event) {
        console.log('WebSocket cerrado:', event.code, event.reason);
        
        this.connected = false;
        
        // Detener heartbeat
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        // Emitir evento
        this.emit('disconnected', { 
            code: event.code, 
            reason: event.reason 
        });
        
        // Intentar reconexión
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
        } else {
            console.error('Máximo de intentos de reconexión alcanzado');
        }
    }
    
    // ========================================================================
    // RECONEXIÓN
    // ========================================================================
    
    scheduleReconnect() {
        if (this.reconnectTimeout) {
            return;  // Ya hay una reconexión programada
        }
        
        this.reconnectAttempts++;
        
        // Exponential backoff
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
            30000  // Max 30s
        );
        
        console.log(
            `Intentando reconexión ${this.reconnectAttempts}/${this.maxReconnectAttempts} ` +
            `en ${(delay / 1000).toFixed(1)}s...`
        );
        
        this.reconnectTimeout = setTimeout(() => {
            this.reconnectTimeout = null;
            this.connect();
        }, delay);
    }
    
    // ========================================================================
    // HEARTBEAT
    // ========================================================================
    
    startHeartbeat() {
        if (this.heartbeatInterval) {
            return;  // Ya hay heartbeat activo
        }
        
        this.heartbeatInterval = setInterval(() => {
            if (this.connected) {
                this.send({ type: 'ping' });
            }
        }, this.heartbeatIntervalTime);
    }
    
    // ========================================================================
    // UTILIDADES
    // ========================================================================
    
    getState() {
        return {
            connected: this.connected,
            url: this.url,
            reconnectAttempts: this.reconnectAttempts,
            readyState: this.ws ? this.ws.readyState : null
        };
    }
}

// Export para usar en HTML
window.WebSocketClient = WebSocketClient;
```

---

## USO DEL CLIENTE

```javascript
// En main.js o index.html

// 1. Crear cliente
const wsClient = new WebSocketClient('ws://localhost:8080/ws');

// 2. Registrar listeners
wsClient.on('connected', () => {
    console.log('Conectado!');
    updateUI('connected');
});

wsClient.on('disconnected', () => {
    console.log('Desconectado');
    updateUI('disconnected');
});

wsClient.on('state_update', (data) => {
    console.log('Estado actualizado:', data);
    // Actualizar escena 3D, sliders, etc.
    scene3d.updatePointer(data.pointer.direction, data.pointer.intersection);
    updateSensorSliders(data.sensor);
});

wsClient.on('calibration_result', (data) => {
    if (data.success) {
        alert('Calibración exitosa!');
    } else {
        alert('Calibración fallida');
    }
});

wsClient.on('error', (error) => {
    console.error('Error de WebSocket:', error);
});

// 3. Conectar
wsClient.connect();

// 4. Enviar mensajes
wsClient.send({
    type: 'sensor_data',
    alpha: 180,
    beta: 0,
    gamma: 0,
    timestamp: Date.now()
});

// 5. Desconectar (cuando sea necesario)
// wsClient.disconnect();
```

---

## TESTS (SIMPLES)

```javascript
// Tests básicos para verificar funcionamiento

function testWebSocketClient() {
    console.log('=== Test WebSocketClient ===');
    
    // Test 1: Crear cliente
    const client = new WebSocketClient('ws://localhost:8080/ws');
    console.log('✅ Cliente creado');
    
    // Test 2: Registrar listener
    let eventReceived = false;
    client.on('connected', () => {
        eventReceived = true;
        console.log('✅ Evento recibido');
    });
    
    // Test 3: Emit manual
    client.emit('connected', {});
    console.assert(eventReceived, 'Evento debe haberse recibido');
    
    // Test 4: Get state
    const state = client.getState();
    console.assert(state.hasOwnProperty('connected'), 'State debe tener connected');
    console.log('✅ State OK');
    
    console.log('=== Tests pasados ===');
}

// Ejecutar tests
// testWebSocketClient();
```

---

## CRITERIOS DE VALIDACIÓN

- [ ] WebSocket conecta al servidor
- [ ] Reconexión automática funciona
- [ ] Eventos se emiten correctamente
- [ ] Mensajes JSON se envían/reciben
- [ ] Heartbeat funciona
- [ ] Manejo de errores robusto
- [ ] Exponential backoff en reconexión
- [ ] Disconnect limpia recursos

---

## NOTAS IMPORTANTES

1. **Reconexión automática**:
   - Máximo 10 intentos por default
   - Exponential backoff (2s, 4s, 8s, 16s, 30s max)
   - Se resetea al conectar exitosamente

2. **Heartbeat**:
   - Ping cada 30 segundos
   - Mantiene conexión viva
   - Detecta desconexiones

3. **Event system**:
   - EventEmitter pattern simple
   - Múltiples listeners por evento
   - Try-catch en callbacks

4. **Browser WebSocket**:
   - Usa WebSocket nativo del browser
   - No requiere librerías externas
   - Compatible con todos los browsers modernos

---

## TIEMPO ESTIMADO

**15-20 minutos** (módulo simple)

---

**ENTREGA**: Archivo `websocket_client.js` completo, funcional, con reconexión y events.
