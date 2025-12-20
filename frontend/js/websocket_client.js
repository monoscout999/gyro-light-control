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
     * Eliminar listener para eventos
     * 
     * @param {String} event - Nombre del evento
     * @param {Function} callback - Función a eliminar (opcional, si no se pasa elimina todos)
     */
    off(event, callback) {
        if (!this.eventListeners[event]) {
            return;
        }

        if (!callback) {
            // Eliminar todos los listeners de este evento
            delete this.eventListeners[event];
        } else {
            // Eliminar solo el callback específico
            this.eventListeners[event] = this.eventListeners[event].filter(
                cb => cb !== callback
            );
        }
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
            readyState: this.ws ? this.ws.readyState : null,
            readyStateText: this.ws ? this.getReadyStateText() : 'NONE'
        };
    }

    getReadyStateText() {
        if (!this.ws) return 'NONE';

        switch (this.ws.readyState) {
            case WebSocket.CONNECTING: return 'CONNECTING';
            case WebSocket.OPEN: return 'OPEN';
            case WebSocket.CLOSING: return 'CLOSING';
            case WebSocket.CLOSED: return 'CLOSED';
            default: return 'UNKNOWN';
        }
    }
}

// ============================================================================
// TESTS
// ============================================================================

/**
 * Tests básicos para verificar funcionamiento
 */
function testWebSocketClient() {
    console.log('=== Test WebSocketClient ===');

    // Test 1: Crear cliente
    const client = new WebSocketClient('ws://localhost:8080/ws');
    console.assert(client.url === 'ws://localhost:8080/ws', 'URL debe ser correcta');
    console.log('✅ Cliente creado');

    // Test 2: Registrar listener
    let eventReceived = false;
    let eventData = null;
    client.on('connected', (data) => {
        eventReceived = true;
        eventData = data;
    });

    // Test 3: Emit manual
    client.emit('connected', { test: true });
    console.assert(eventReceived, 'Evento debe haberse recibido');
    console.assert(eventData.test === true, 'Data debe ser correcta');
    console.log('✅ Evento recibido');

    // Test 4: Múltiples listeners
    let count = 0;
    client.on('test', () => count++);
    client.on('test', () => count++);
    client.emit('test', {});
    console.assert(count === 2, 'Deben ejecutarse ambos listeners');
    console.log('✅ Múltiples listeners OK');

    // Test 5: Remove listener
    const callback = () => count++;
    client.on('remove_test', callback);
    client.off('remove_test', callback);
    client.emit('remove_test', {});
    console.assert(count === 2, 'Listener removido no debe ejecutarse');
    console.log('✅ Remove listener OK');

    // Test 6: Get state
    const state = client.getState();
    console.assert(state.hasOwnProperty('connected'), 'State debe tener connected');
    console.assert(state.hasOwnProperty('url'), 'State debe tener url');
    console.assert(state.hasOwnProperty('reconnectAttempts'), 'State debe tener reconnectAttempts');
    console.log('✅ State OK');

    // Test 7: Error handling en listeners
    client.on('error_test', () => {
        throw new Error('Test error');
    });
    try {
        client.emit('error_test', {});
        console.log('✅ Error handling OK (error atrapado)');
    } catch (e) {
        console.error('❌ Error no fue atrapado');
    }

    // Test 8: Send sin conexión
    const result = client.send({ type: 'test' });
    console.assert(result === false, 'Send debe retornar false sin conexión');
    console.log('✅ Send sin conexión OK');

    console.log('=== Tests pasados ===');
}

// Export para usar en HTML
if (typeof window !== 'undefined') {
    window.WebSocketClient = WebSocketClient;
    window.testWebSocketClient = testWebSocketClient;
}

// Export para Node.js (testing)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WebSocketClient, testWebSocketClient };
}
