# 🏗️ Module Architecture - Phase 0 Visualizer

**Document**: Module Structure and Dependencies  
**Version**: 1.0  
**Date**: 2024-12-15  
**Status**: APPROVED  

---

## 🎯 Architectural Principles

1. **Modularity**: Each module has single responsibility
2. **Isolation**: Modules don't directly depend on each other (use interfaces)
3. **Reusability**: `math_engine.py` must work in Phase 1 and 2 without changes
4. **Testability**: Each module independently testable
5. **Documentation**: Each module has clear inputs/outputs

---

## 📁 Directory Structure

```
/gyro-visualizer/
│
├── backend/
│   ├── __init__.py
│   ├── server.py              # Main entry point
│   ├── math_engine.py         # [VALIDABLE MODULE] Math formulas
│   ├── venue_manager.py       # Venue state
│   ├── fixture_manager.py     # Fixture state
│   ├── websocket_handler.py   # Network communication
│   └── config.py              # Configuration
│
├── frontend/
│   ├── index.html             # Main HTML
│   ├── styles.css             # Tailwind + custom styles
│   ├── js/
│   │   ├── main.js            # App initialization
│   │   ├── scene3d.js         # [VALIDABLE MODULE] Three.js
│   │   ├── ui_controls.js     # UI interactions
│   │   ├── properties_panel.js# Properties panel
│   │   ├── debug_console.js   # Console
│   │   └── websocket_client.js# WebSocket connection
│   └── assets/
│       └── (images, icons)
│
├── shared/
│   └── data_structures.py     # Shared data definitions
│
├── tests/
│   ├── test_math_engine.py
│   ├── test_venue_manager.py
│   ├── test_fixture_manager.py
│   └── test_websocket_handler.py
│
├── scenes/                     # Saved scene files
│   └── (empty initially)
│
├── fixtures/                   # Fixture preset definitions
│   ├── generic_moving_head.json
│   ├── generic_led_par.json
│   └── generic_wash.json
│
├── requirements.txt           # Python dependencies
├── package.json              # Node.js dependencies (if needed)
└── README.md                 # Setup instructions
```

---

## 🔗 Module Dependencies

```
┌─────────────────────────────────────────────┐
│              server.py                      │
│         (FastAPI application)               │
└────────┬────────────────────┬───────────────┘
         │                    │
         │                    │
    ┌────▼─────────┐   ┌──────▼──────────┐
    │ websocket_   │   │  Static files   │
    │  handler.py  │   │  (frontend)     │
    └────┬─────────┘   └─────────────────┘
         │
         │
    ┌────▼──────────┐
    │  venue_       │
    │  manager.py   │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │  fixture_     │
    │  manager.py   │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │  math_engine  │◄────────────────┐
    │     .py       │                 │
    │  [VALIDABLE]  │                 │
    └───────────────┘                 │
                                      │
                           ┌──────────┴──────────┐
                           │   Frontend JS       │
                           │   (uses same math)  │
                           └─────────────────────┘
```

**Key Point**: `math_engine.py` is independent. Frontend reimplements same formulas in JS for client-side preview.

---

## 📦 Module Specifications

### **1. server.py**

**Responsibility**: Main application entry point

**Dependencies**:
- FastAPI
- websocket_handler
- venue_manager
- fixture_manager

**Key Functions**:
```python
def main():
    """Start FastAPI server with WebSocket support"""

@app.get("/")
async def index():
    """Serve frontend HTML"""

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections from mobile"""
```

**Configuration**:
```python
HOST = "0.0.0.0"
PORT = 8080
DEBUG = True
```

---

### **2. math_engine.py** ⭐ **[CRITICAL - VALIDABLE MODULE]**

**Responsibility**: ALL mathematical calculations

**Dependencies**: 
- NumPy (only)

**ZERO dependencies on**:
- No UI code
- No WebSocket code
- No state management

**Key Functions**:

```python
def euler_to_direction(
    alpha: float, 
    beta: float, 
    gamma: float
) -> np.ndarray:
    """
    Convert Euler angles to 3D direction vector.
    
    Args:
        alpha: 0-360° compass/yaw
        beta: -180 to 180° pitch
        gamma: -90 to 90° roll
        
    Returns:
        Normalized numpy array [x, y, z]
    """
    pass


def create_calibration_offset(
    current_vector: np.ndarray,
    target_vector: np.ndarray
) -> np.ndarray:
    """
    Calculate rotation matrix to align current to target.
    
    Args:
        current_vector: Direction phone is pointing
        target_vector: Direction it SHOULD point (back wall)
        
    Returns:
        3x3 rotation matrix
    """
    pass


def apply_calibration(
    vector: np.ndarray,
    rotation_matrix: np.ndarray
) -> np.ndarray:
    """
    Apply calibration to uncalibrated vector.
    
    Args:
        vector: Raw direction from sensor
        rotation_matrix: Calibration offset
        
    Returns:
        Calibrated direction vector
    """
    pass


def ray_box_intersection(
    origin: np.ndarray,
    direction: np.ndarray,
    box_min: np.ndarray,
    box_max: np.ndarray
) -> Optional[np.ndarray]:
    """
    Find where ray hits axis-aligned box.
    
    Args:
        origin: Ray starting point (user position)
        direction: Ray direction (pointer vector)
        box_min: Venue corner (0, 0, 0)
        box_max: Venue corner (width, depth, height)
        
    Returns:
        Intersection point [x, y, z] or None
    """
    pass


def calculate_fixture_pan_tilt(
    fixture_position: np.ndarray,
    target_position: np.ndarray,
    mounting: str,  # "ceiling", "floor", "wall"
    pan_invert: bool = False,
    tilt_invert: bool = False
) -> Tuple[float, float]:
    """
    Calculate pan/tilt angles for fixture to point at target.
    
    Args:
        fixture_position: Where the fixture is mounted
        target_position: Where pointer is hitting
        mounting: How fixture is oriented
        pan_invert: Reverse pan direction
        tilt_invert: Reverse tilt direction
        
    Returns:
        (pan_degrees, tilt_degrees)
    """
    pass
```

**Testing**:
```python
# tests/test_math_engine.py

def test_euler_forward():
    """Test pointing straight forward"""
    vector = euler_to_direction(0, 0, 0)
    assert np.allclose(vector, [0, 1, 0])

def test_euler_up():
    """Test pointing straight up"""
    vector = euler_to_direction(0, 90, 0)
    assert np.allclose(vector, [0, 0, 1])

def test_calibration_identity():
    """Test calibration with same vector (no rotation)"""
    v = np.array([0, 1, 0])
    R = create_calibration_offset(v, v)
    assert np.allclose(R, np.eye(3))

def test_ray_hits_back_wall():
    """Test ray from center hits back wall"""
    origin = np.array([5, 5, 1])
    direction = np.array([0, 1, 0])
    box_min = np.array([0, 0, 0])
    box_max = np.array([10, 10, 4])
    
    hit = ray_box_intersection(origin, direction, box_min, box_max)
    assert hit is not None
    assert np.allclose(hit[1], 10)  # Hit Y=10 (back wall)
```

**Validation Criteria**:
- [ ] All tests pass
- [ ] No dependencies on UI/network code
- [ ] Functions are pure (no side effects)
- [ ] Documented with docstrings

Once validated: **MARK AS `[VALIDADO-YYYY-MM-DD]`**

---

### **3. venue_manager.py**

**Responsibility**: Manage venue state

**Dependencies**:
- shared.data_structures

**Key Class**:
```python
class VenueManager:
    def __init__(self):
        self.dimensions = (10, 10, 4)  # X, Y, Z
        self.grid_size = 1.0
        
    def set_dimensions(self, width, depth, height):
        """Update venue size"""
        
    def get_back_wall_center(self) -> tuple:
        """Calculate center point of back wall"""
        x = self.dimensions[0] / 2
        y = self.dimensions[1]  # Far edge
        z = self.dimensions[2] / 2
        return (x, y, z)
    
    def get_bounds(self) -> dict:
        """Return min/max corners"""
        return {
            "min": (0, 0, 0),
            "max": self.dimensions
        }
    
    def to_dict(self) -> dict:
        """Serialize for save file"""
        return {
            "dimensions": list(self.dimensions),
            "grid_size": self.grid_size
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Deserialize from save file"""
```

---

### **4. fixture_manager.py**

**Responsibility**: Manage fixtures

**Dependencies**:
- shared.data_structures
- math_engine (for pan/tilt calculation)

**Key Class**:
```python
class Fixture:
    def __init__(
        self, 
        name: str,
        position: tuple,
        pan_range: tuple,
        tilt_range: tuple,
        mounting: str = "ceiling"
    ):
        self.id = generate_uuid()
        self.name = name
        self.position = position
        self.pan_range = pan_range
        self.tilt_range = tilt_range
        self.mounting = mounting
        self.pan_invert = False
        self.tilt_invert = False
        self.current_pan = 0
        self.current_tilt = 0
        
    def point_at(self, target_position: tuple):
        """Calculate and store pan/tilt to aim at target"""
        from math_engine import calculate_fixture_pan_tilt
        
        pan, tilt = calculate_fixture_pan_tilt(
            self.position,
            target_position,
            self.mounting,
            self.pan_invert,
            self.tilt_invert
        )
        
        # Clamp to ranges
        self.current_pan = np.clip(pan, *self.pan_range)
        self.current_tilt = np.clip(tilt, *self.tilt_range)
    
    def to_dict(self) -> dict:
        """Serialize"""
        

class FixtureManager:
    def __init__(self):
        self.fixtures = {}
        self.load_presets()
        
    def load_presets(self):
        """Load fixture presets from JSON files"""
        
    def add_fixture(self, fixture: Fixture):
        """Add fixture to scene"""
        
    def get_fixture(self, fixture_id: str) -> Fixture:
        """Get fixture by ID"""
        
    def update_all_fixtures(self, target_position: tuple):
        """Update all fixtures to point at target"""
        for fixture in self.fixtures.values():
            fixture.point_at(target_position)
```

---

### **5. websocket_handler.py**

**Responsibility**: Handle WebSocket communication

**Dependencies**:
- FastAPI WebSocket
- asyncio

**Key Class**:
```python
class WebSocketHandler:
    def __init__(self):
        self.active_connections = []
        self.latency_buffer = LatencyBuffer(buffer_size=3)
        
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        
    async def disconnect(self, websocket: WebSocket):
        """Handle disconnection"""
        
    async def receive_sensor_data(self, websocket: WebSocket):
        """Receive alpha, beta, gamma from mobile"""
        data = await websocket.receive_json()
        
        # Add to buffer
        self.latency_buffer.add_sample(
            data,
            timestamp=time.time()
        )
        
        # Process immediately or interpolate
        return self.latency_buffer.get_latest()
        
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        

class LatencyBuffer:
    """Smooth out network latency"""
    def __init__(self, buffer_size: int = 3):
        self.samples = deque(maxlen=buffer_size)
        
    def add_sample(self, data: dict, timestamp: float):
        """Add sensor reading"""
        
    def get_latest(self) -> dict:
        """Get most recent (or interpolated)"""
```

---

### **6. Frontend: scene3d.js** ⭐ **[CRITICAL MODULE]**

**Responsibility**: Three.js scene management

**Dependencies**:
- Three.js
- OrbitControls

**Key Functions**:

```javascript
class Scene3D {
    constructor(containerElement) {
        this.container = containerElement;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(...);
        this.renderer = new THREE.WebGLRenderer(...);
        this.controls = new OrbitControls(...);
        
        this.objects = {
            venue: null,
            user: null,
            pointer: null,
            fixtures: []
        };
        
        this.init();
    }
    
    init() {
        // Setup scene, lights, camera
        this.setupScene();
        this.createVenue();
        this.createUser();
        this.createPointer();
        this.animate();
    }
    
    createVenue() {
        // Draw grid floor
        // Draw wireframe walls
        // Highlight back wall
    }
    
    createUser() {
        // Small blue sphere at center
    }
    
    createPointer() {
        // Red line (ray)
        // Red sphere (intersection point)
    }
    
    updatePointer(direction, intersection) {
        // Update ray direction
        // Move intersection sphere
    }
    
    addFixture(fixtureData) {
        // Create fixture mesh
        // Create light cone
    }
    
    updateFixture(fixtureId, pan, tilt) {
        // Rotate fixture to pan/tilt
    }
    
    onObjectClick(event) {
        // Raycasting to detect click
        // Emit 'objectSelected' event
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}
```

---

### **7. Frontend: websocket_client.js**

**Responsibility**: WebSocket connection to backend

```javascript
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.callbacks = {};
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('✅ WebSocket connected');
            this.reconnectAttempts = 0;
            this.emit('connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.emit('message', data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.emit('error', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket closed');
            this.attemptReconnect();
        };
    }
    
    send(data) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }
    
    emit(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(cb => cb(data));
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 2000);
        }
    }
}
```

---

## 🔄 Data Flow Example

### **Scenario: User calibrates system**

1. **Mobile sends sensor data**:
```json
// Mobile → Backend
{
  "type": "sensor_data",
  "alpha": 245.3,
  "beta": -12.7,
  "gamma": 3.2,
  "timestamp": 1702650123456
}
```

2. **Backend processes**:
```python
# websocket_handler receives
sensor_data = receive_sensor_data()

# Convert to vector
from math_engine import euler_to_direction
vector = euler_to_direction(
    sensor_data['alpha'],
    sensor_data['beta'],
    sensor_data['gamma']
)

# Calculate intersection
from math_engine import ray_box_intersection
user_pos = venue_manager.get_user_position()
venue_bounds = venue_manager.get_bounds()

intersection = ray_box_intersection(
    user_pos,
    vector,
    venue_bounds['min'],
    venue_bounds['max']
)

# Update fixtures
fixture_manager.update_all_fixtures(intersection)
```

3. **Backend broadcasts to frontend**:
```json
// Backend → Frontend
{
  "type": "state_update",
  "sensor": {
    "alpha": 245.3,
    "beta": -12.7,
    "gamma": 3.2
  },
  "pointer": {
    "direction": [0.12, 0.85, 0.51],
    "intersection": [5.2, 8.3, 2.1]
  },
  "fixtures": [
    {
      "id": "fixture_001",
      "pan": 125.3,
      "tilt": -45.7
    }
  ]
}
```

4. **Frontend updates visuals**:
```javascript
wsClient.on('message', (data) => {
    if (data.type === 'state_update') {
        // Update sliders
        uiControls.updateSliders(data.sensor);
        
        // Update 3D scene
        scene3d.updatePointer(
            data.pointer.direction,
            data.pointer.intersection
        );
        
        // Update fixtures
        data.fixtures.forEach(f => {
            scene3d.updateFixture(f.id, f.pan, f.tilt);
        });
        
        // Log to console
        debugConsole.log('State updated', 'info');
    }
});
```

---

## 🧪 Testing Strategy

### **Module Testing Order**

1. **math_engine.py** ← Test FIRST, validate FIRST
   - Pure functions, no dependencies
   - Easy to test in isolation
   - Once validated, becomes immutable

2. **venue_manager.py**
   - Test state management
   - Test serialization

3. **fixture_manager.py**
   - Test with mock math_engine
   - Test preset loading

4. **websocket_handler.py**
   - Test connection/disconnection
   - Test message routing

5. **Frontend modules**
   - Test UI interactions
   - Test WebSocket client
   - Manual testing of 3D scene

---

## 📝 Validation Protocol

### **For each module:**

1. **Write tests** BEFORE implementation
2. **Implement** module
3. **Run tests** → All must pass
4. **Code review** (check dependencies, coupling)
5. **Mark as `[VALIDADO-YYYY-MM-DD]`** in code
6. **Document in decision_log.md**

### **After validation:**
- Module becomes **IMMUTABLE**
- Changes require creating `_v2` version
- Original version stays for rollback

---

## 🎯 Integration Points

### **Phase 0 → Phase 1 transition**

**Reusable without changes**:
- ✅ `math_engine.py` (exact same formulas)
- ✅ `venue_manager.py` (same venue logic)
- ✅ `fixture_manager.py` (same fixture logic)

**Needs extension**:
- `websocket_handler.py` → Add mobile sensor streaming
- Frontend → Add mobile UI for sensor control

**New modules needed**:
- `mobile_interface.py` → Serve mobile HTML
- Mobile frontend (HTML/JS for phone)

---

## 🚀 Build Order Recommendation

**Week 1: Foundation**
1. Setup project structure
2. Implement `math_engine.py` + tests
3. Validate math_engine → MARK [VALIDADO]

**Week 2: Backend**
4. Implement `venue_manager.py`
5. Implement `fixture_manager.py`
6. Implement `websocket_handler.py`
7. Implement `server.py`
8. Test backend integration

**Week 3: Frontend Core**
9. Setup Three.js scene (`scene3d.js`)
10. Implement venue visualization
11. Implement pointer visualization
12. Implement camera controls

**Week 4: Frontend UI**
13. Implement sliders (`ui_controls.js`)
14. Implement properties panel
15. Implement debug console
16. Connect WebSocket client

**Week 5: Features**
17. Implement calibration
18. Implement save/load
19. Implement fixture following
20. Polish and bug fixes

---

**END OF MODULE ARCHITECTURE**

*Follow this structure to ensure clean, modular, testable code.*
