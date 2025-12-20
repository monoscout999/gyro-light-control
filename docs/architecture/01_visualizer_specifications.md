# 📐 Visualizer Technical Specifications

**Document**: Phase 0 - 3D Visualizer Standalone Tool  
**Version**: 1.0  
**Date**: 2024-12-15  
**Status**: APPROVED - Ready for implementation  

---

## 🎯 Purpose

Build a comprehensive 3D visualization and debugging tool that:
1. Simulates the complete venue environment
2. Displays real-time sensor data from mobile device
3. Provides manual calibration system
4. Manages moving light fixtures
5. Serves as the foundation for Phase 1 and Phase 2

---

## 🏗️ Technical Stack

### **Backend**
- **Language**: Python 3.10+
- **Framework**: FastAPI (async, WebSocket support)
- **Math**: NumPy
- **WebSocket**: `websockets` library
- **Platform**: Windows desktop (primary)

### **Frontend**
- **3D Engine**: Three.js (r160+)
- **UI**: Vanilla JavaScript (no framework)
- **Styling**: Tailwind CSS (dark mode)
- **WebSocket**: Native browser WebSocket API

### **Desktop Wrapper** (Future)
- Electron (optional, for now runs in browser)

---

## 📐 Coordinate System

### **Axes**
```
        North (+Y) ← BACK WALL (calibration target)
           ↑
           |
Oeste ←----●---→ Este
(-X)    USER     (+X)
           |
           ↓
        Sur (-Y)

Z = Vertical (↑ UP)
```

### **Defaults**
- **Venue size**: 10m × 10m × 4m (configurable)
- **User position**: (5, 5, 1) - center of venue, 1m height
- **Origin**: (0, 0, 0) at venue corner
- **Back wall center**: (5, 10, 2) - calibration target point

---

## 🖥️ User Interface Layout

```
┌────────────────────────────────────────────────────┐
│  TOOLBAR: [Calibrar] [Reset] [Guardar] [Cargar]   │
├────────────────────────┬───────────────────────────┤
│                        │                           │
│                        │   PROPERTIES PANEL        │
│    3D VIEWPORT         │   (context-sensitive)     │
│    (70% width)         │   (30% width)             │
│                        │                           │
│                        │   [Object properties]     │
│                        │   [Editable fields]       │
│                        │                           │
├────────────────────────┴───────────────────────────┤
│  BOTTOM PANEL (fixed height: 250px)                │
│  ┌──────────────┬──────────────┬─────────────────┐ │
│  │ SENSOR DATA  │ DEBUG INFO   │ CONSOLE         │ │
│  │              │              │                 │ │
│  │ Alpha: ████  │ User:        │ [Log entries]   │ │
│  │   245.3°     │  (5.0, 5.0,  │ [Info][Warn]    │ │
│  │              │   1.0)       │ [Error]         │ │
│  │ Beta:  ████  │              │                 │ │
│  │   -12.7°     │ Pointer:     │ > Calibration   │ │
│  │              │  (5.2, 8.3,  │   successful    │ │
│  │ Gamma: ████  │   2.1)       │ > FPS: 60       │ │
│  │   3.2°       │              │                 │ │
│  │              │ Latency: 23ms│                 │ │
│  └──────────────┴──────────────┴─────────────────┘ │
└────────────────────────────────────────────────────┘
```

---

## 🎮 Components Detailed Specs

### **1. 3D VIEWPORT**

#### **Venue Visualization**
- **Grid floor**: 1m × 1m squares
- **Walls**: Wireframe outlines only (no solid faces)
- **Back wall highlight**: Thicker line or different color
- **Center marker**: Small sphere at back wall center (5, 10, 2)

#### **Camera Controls**
- **Type**: Orbital camera (Three.js OrbitControls)
- **Mouse**: 
  - Left drag = Rotate around center
  - Right drag = Pan view
  - Scroll = Zoom in/out
- **Keyboard shortcuts**:
  - `F` = Toggle fullscreen viewport
  - `R` = Reset camera to default view

#### **Objects in Scene**
1. **User** (avatar)
   - Small sphere (0.3m diameter)
   - Color: Blue
   - Position: (5, 5, user_height)
   - Fixed at center for Phase 0

2. **Pointer** (laser ray)
   - Origin: User position
   - Direction: Calculated from alpha/beta/gamma
   - Visualization: Red line from user to intersection
   - Endpoint: Red sphere (0.2m) at wall/floor intersection
   - Confined to venue boundaries

3. **Moving Light Fixture**
   - Simple cone shape (base 0.5m, height 1m)
   - Position: Configurable (x, y, z)
   - Light beam: White cone from fixture toward pointer
   - Automatically rotates to follow pointer

#### **Selection System**
- Click on object → Highlight (yellow outline)
- Selected object → Properties panel updates
- Selectable objects: Venue, Fixture, User

---

### **2. SENSOR DATA PANEL**

#### **Display Format**
Each sensor has:
- **Label**: "Alpha:", "Beta:", "Gamma:"
- **Progress bar**: Visual representation (0-360° for alpha, ±180° for beta/gamma)
- **Numeric value**: Large, readable font (e.g., "245.3°")

#### **Behavior**
- **READ-ONLY**: Values updated from mobile sensor data only
- **NOT EDITABLE**: No manual slider dragging
- **Update rate**: 30 FPS (smoothed with interpolation)
- **Color coding**:
  - Normal: White text
  - Extreme values: Yellow (near limits)

---

### **3. DEBUG INFO PANEL**

#### **User Info**
```
User Position:
  X: 5.00 m
  Y: 5.00 m
  Z: 1.00 m (height slider)
```

#### **Pointer Info**
```
Pointer:
  Direction: (0.12, 0.85, 0.51)
  Intersection: (5.2, 8.3, 2.1)
  Distance: 3.4 m
```

#### **Performance Info**
```
FPS: 60
Latency: 23 ms
Last update: 0.03s ago
```

---

### **4. CONSOLE**

#### **Message Types**
- **Info** (white): Normal events
- **Warning** (yellow): Non-critical issues
- **Error** (red): Critical problems

#### **Filter Buttons**
- `[Info]` `[Warning]` `[Error]` - Toggle visibility
- `[Clear]` - Clear all messages

#### **Features**
- Auto-scroll to bottom
- Max 100 messages (oldest removed)
- Timestamp for each message

#### **Example Logs**
```
14:23:45 [INFO] WebSocket connected
14:23:52 [INFO] Calibration started
14:23:53 [INFO] Calibration successful (error: ±2.1°)
14:24:10 [WARN] High latency detected (142ms)
```

---

### **5. PROPERTIES PANEL**

#### **When VENUE selected**

```
┌─────────────────────────┐
│ VENUE PROPERTIES        │
├─────────────────────────┤
│ Dimensions:             │
│  Width (X):  [10.0] m   │
│  Depth (Y):  [10.0] m   │
│  Height (Z): [4.0 ] m   │
│                         │
│ Grid Size:   [1.0 ] m   │
│                         │
│ [Apply Changes]         │
└─────────────────────────┘
```

#### **When FIXTURE selected**

```
┌─────────────────────────┐
│ FIXTURE PROPERTIES      │
├─────────────────────────┤
│ Name: [Moving Head 1]   │
│                         │
│ Position:               │
│  X: [7.5 ] m            │
│  Y: [9.0 ] m            │
│  Z: [3.5 ] m            │
│                         │
│ Mounting:               │
│  ○ Floor                │
│  ● Ceiling              │
│  ○ Wall (horizontal)    │
│                         │
│ Pan/Tilt Config:        │
│  Pan Range:             │
│    Min: [-270] °        │
│    Max: [ 270] °        │
│  ☑ Invert Pan           │
│                         │
│  Tilt Range:            │
│    Min: [-135] °        │
│    Max: [ 135] °        │
│  ☐ Invert Tilt          │
│                         │
│ Current State:          │
│  Pan:  125.3°           │
│  Tilt: -45.7°           │
│                         │
│ [Apply] [Load Preset▼] │
└─────────────────────────┘
```

#### **When USER selected**

```
┌─────────────────────────┐
│ USER PROPERTIES         │
├─────────────────────────┤
│ Position:               │
│  X: 5.0 m (center)      │
│  Y: 5.0 m (center)      │
│                         │
│ Height: [████░░░] 1.0 m │
│         0.5 ─────── 1.5 │
│                         │
│ (Position fixed in      │
│  Phase 0)               │
└─────────────────────────┘
```

#### **When NOTHING selected**

```
┌─────────────────────────┐
│ SCENE INFO              │
├─────────────────────────┤
│ Objects:                │
│  • 1 Venue              │
│  • 1 User               │
│  • 1 Fixture            │
│                         │
│ Calibration:            │
│  Status: ✅ Calibrated  │
│  Error: ±2.1°           │
│                         │
│ Scene File:             │
│  venue_teatro.json      │
│  Last saved: 14:20      │
└─────────────────────────┘
```

---

## 🔧 Fixture Management System

### **Fixture Presets (Built-in)**

```python
FIXTURE_PRESETS = {
    "Generic Moving Head": {
        "pan_range": (-270, 270),
        "tilt_range": (-135, 135),
        "mounting": "ceiling"
    },
    "Generic LED Par": {
        "pan_range": (0, 0),      # Fixed position
        "tilt_range": (-90, 90),
        "mounting": "floor"
    },
    "Generic Wash Light": {
        "pan_range": (-180, 180),
        "tilt_range": (-110, 110),
        "mounting": "ceiling"
    }
}
```

### **Custom Fixture Creation**

Simple dialog:
```
┌────────────────────────────────┐
│ CREATE CUSTOM FIXTURE          │
├────────────────────────────────┤
│ Name: [________________]       │
│                                │
│ Pan Range:                     │
│  Min: [____]° Max: [____]°     │
│                                │
│ Tilt Range:                    │
│  Min: [____]° Max: [____]°     │
│                                │
│ Mounting:                      │
│  [▼ Ceiling    ]               │
│                                │
│ [Create] [Cancel]              │
└────────────────────────────────┘
```

### **Fixture File Format (JSON)**

```json
{
  "name": "My Custom Fixture",
  "pan_range": [-270, 270],
  "tilt_range": [-135, 135],
  "mounting": "ceiling",
  "pan_invert": false,
  "tilt_invert": false
}
```

---

## 🎯 Calibration System

### **Calibration Process**

**Prerequisites:**
1. Mobile sensor streaming data (alpha, beta, gamma)
2. User physically pointing phone at back wall center
3. Phone screen facing up (sky)

**User Action:**
1. Click `[Calibrar]` button in toolbar

**System Behavior:**
```python
def calibrate():
    # 1. Capture current sensor values
    alpha_0 = current_alpha
    beta_0 = current_beta
    gamma_0 = current_gamma
    
    # 2. Calculate ideal vector to back wall center
    user_pos = (5, 5, 1)
    target_pos = (5, 10, 2)  # Back wall center
    ideal_vector = normalize(target_pos - user_pos)
    # ideal_vector ≈ (0, 0.981, 0.196)
    
    # 3. Calculate rotation offset
    current_vector = euler_to_vector(alpha_0, beta_0, gamma_0)
    rotation_offset = calculate_rotation(current_vector, ideal_vector)
    
    # 4. Store calibration
    calibration_data = {
        "timestamp": now(),
        "sensor_values": (alpha_0, beta_0, gamma_0),
        "rotation_offset": rotation_offset,
        "target_position": target_pos
    }
    
    # 5. Visual feedback
    snap_pointer_to_target(target_pos)
    show_console_message("✅ Calibration successful")
    
    return calibration_data
```

**Visual Feedback:**
- Pointer snaps to back wall center
- Console message: `"✅ Calibration successful (error: ±X.X°)"`
- Properties panel updates calibration status

---

## 📊 Data Flow

### **Mobile → Visualizer**

```
┌─────────────┐
│   MOBILE    │
│  (browser)  │
└──────┬──────┘
       │ WebSocket
       │ { alpha, beta, gamma }
       │ @ 30 FPS
       ↓
┌──────────────────┐
│  BACKEND SERVER  │
│  (FastAPI)       │
│                  │
│ 1. Receive data  │
│ 2. Apply buffer  │
│ 3. Broadcast     │
└──────┬───────────┘
       │ WebSocket
       │ { sensor_data, pointer_pos }
       ↓
┌──────────────────┐
│  FRONTEND        │
│  (Three.js)      │
│                  │
│ 1. Update sliders│
│ 2. Calc pointer  │
│ 3. Move fixture  │
│ 4. Render 3D     │
└──────────────────┘
```

### **Latency Buffer**

To handle network delays:
```python
class LatencyBuffer:
    def __init__(self, buffer_size=3):
        self.buffer = []
        
    def add_sample(self, data, timestamp):
        self.buffer.append((data, timestamp))
        if len(self.buffer) > buffer_size:
            self.buffer.pop(0)
    
    def get_interpolated(self, target_time):
        # Linear interpolation between samples
        # Predicts 2-3 frames ahead
        return interpolate(self.buffer, target_time)
```

**Benefit**: Smoother visualization even with 50-100ms latency

---

## 💾 Save/Load System

### **Scene File Format (JSON)**

```json
{
  "version": "1.0",
  "created": "2024-12-15T14:30:00Z",
  "venue": {
    "dimensions": [10, 10, 4],
    "grid_size": 1.0
  },
  "user": {
    "position": [5, 5, 1],
    "height": 1.0
  },
  "fixtures": [
    {
      "id": "fixture_001",
      "name": "Moving Head 1",
      "position": [7.5, 9.0, 3.5],
      "mounting": "ceiling",
      "pan_range": [-270, 270],
      "tilt_range": [-135, 135],
      "pan_invert": false,
      "tilt_invert": true
    }
  ],
  "calibration": {
    "is_calibrated": true,
    "timestamp": "2024-12-15T14:25:00Z",
    "rotation_offset": [...],
    "error_estimate": 2.1
  }
}
```

### **File Operations**

**Save:**
- Button: `[Guardar]` in toolbar
- Opens file dialog
- Default name: `venue_YYYY-MM-DD_HHmm.json`

**Load:**
- Button: `[Cargar]` in toolbar
- Opens file picker
- Validates JSON structure
- Restores complete scene state

---

## 🧮 Mathematical Formulas

### **Euler Angles to Direction Vector**

```python
def euler_to_direction(alpha, beta, gamma):
    """
    Convert mobile sensor angles to 3D direction vector.
    
    Args:
        alpha: 0-360° (compass/yaw) - rotation around Z
        beta: -180 to 180° (pitch) - rotation around X
        gamma: -90 to 90° (roll) - rotation around Y
        
    Returns:
        normalized vector (x, y, z)
    """
    # Convert to radians
    a = radians(alpha)
    b = radians(beta)
    g = radians(gamma)
    
    # Initial forward vector (assuming phone screen up, pointing north)
    # This is BEFORE calibration offset
    x = sin(a) * cos(b)
    y = cos(a) * cos(b)
    z = sin(b)
    
    # Apply gamma (roll) - usually small correction
    # (Simplified - full implementation uses rotation matrices)
    
    return normalize(Vector3(x, y, z))
```

### **Apply Calibration Offset**

```python
def apply_calibration(vector, calibration_data):
    """
    Apply rotation offset from calibration.
    
    Args:
        vector: Current direction vector
        calibration_data: Stored rotation offset
        
    Returns:
        Calibrated vector pointing in correct direction
    """
    rotation_matrix = calibration_data["rotation_offset"]
    calibrated = rotation_matrix @ vector
    return normalize(calibrated)
```

### **Ray-Box Intersection**

```python
def ray_box_intersection(origin, direction, box_min, box_max):
    """
    Find where laser ray hits venue walls/floor.
    
    Args:
        origin: User position (x, y, z)
        direction: Normalized pointer vector
        box_min: Venue corner (0, 0, 0)
        box_max: Venue opposite corner (10, 10, 4)
        
    Returns:
        intersection_point (x, y, z) or None
    """
    # Standard ray-box intersection algorithm
    # Tests all 6 faces, returns closest hit
    
    t_min = (box_min - origin) / direction
    t_max = (box_max - origin) / direction
    
    t1 = min(t_min, t_max)
    t2 = max(t_min, t_max)
    
    t_near = max(t1)
    t_far = min(t2)
    
    if t_near > t_far or t_far < 0:
        return None  # No intersection
    
    t = t_near if t_near > 0 else t_far
    return origin + direction * t
```

---

## 🎨 Visual Style Guide

### **Color Palette (Dark Mode)**

```css
--bg-primary: #1a1a1a     /* Main background */
--bg-secondary: #2d2d2d   /* Panels */
--bg-tertiary: #3a3a3a    /* Inputs */

--text-primary: #e0e0e0   /* Main text */
--text-secondary: #a0a0a0 /* Labels */
--text-muted: #707070     /* Disabled */

--accent-primary: #4a9eff  /* Buttons, highlights */
--accent-success: #4ade80  /* Success messages */
--accent-warning: #fbbf24  /* Warnings */
--accent-error: #ef4444    /* Errors */

--3d-user: #4a9eff         /* User avatar (blue) */
--3d-pointer: #ef4444      /* Pointer ray/dot (red) */
--3d-fixture: #a0a0a0      /* Fixture body (gray) */
--3d-light-beam: #ffffff   /* Light cone (white) */
--3d-grid: #404040         /* Floor grid */
--3d-walls: #606060        /* Venue walls */
--3d-back-wall: #4ade80    /* Back wall highlight (green) */
--3d-selected: #fbbf24     /* Selected object (yellow) */
```

### **Typography**

```css
--font-primary: 'Inter', sans-serif
--font-mono: 'Fira Code', monospace

--text-xs: 0.75rem    /* Labels */
--text-sm: 0.875rem   /* Normal text */
--text-base: 1rem     /* Headings */
--text-lg: 1.25rem    /* Large values */
```

---

## ⚙️ Performance Requirements

### **Target Metrics**
- **3D Render**: 30 FPS minimum (60 FPS ideal)
- **WebSocket latency**: <100ms target, <200ms acceptable
- **Sensor update rate**: 30 Hz (from mobile)
- **UI responsiveness**: <16ms for interactions

### **Optimization Strategies**
1. Use Three.js frustum culling
2. Simple geometries (low poly count)
3. WebSocket message throttling (30 FPS max)
4. Interpolation buffer for smooth movement
5. Lazy update of properties panel (only when selection changes)

---

## 🧪 Testing Requirements

### **Unit Tests** (Python backend)
- `test_euler_to_vector()` - Math conversions
- `test_calibration_offset()` - Calibration logic
- `test_ray_intersection()` - Pointer calculation
- `test_fixture_tracking()` - Pan/Tilt calculation

### **Integration Tests**
- WebSocket connection/disconnection
- Message serialization/deserialization
- File save/load round-trip
- Calibration data persistence

### **Manual Testing Checklist**
- [ ] 3D scene renders correctly
- [ ] Objects selectable by click
- [ ] Properties panel updates on selection
- [ ] Sliders display sensor data correctly
- [ ] Calibration moves pointer to back wall
- [ ] Fixture follows pointer smoothly
- [ ] Console logs messages
- [ ] Save/Load preserves all state
- [ ] Camera controls work (orbit, zoom, pan)

---

## 📋 Module Breakdown

### **Backend Modules**

1. **`server.py`**
   - FastAPI app initialization
   - WebSocket endpoint
   - Static file serving

2. **`math_engine.py`** [CRITICAL - REUSABLE]
   - `euler_to_direction(alpha, beta, gamma)`
   - `apply_calibration(vector, calibration_data)`
   - `ray_box_intersection(origin, direction, box)`
   - `calculate_fixture_angles(fixture_pos, target_pos)`

3. **`venue_manager.py`**
   - Venue state management
   - Dimension validation
   - Scene serialization

4. **`fixture_manager.py`**
   - Fixture CRUD operations
   - Preset loading
   - Tracking logic

5. **`websocket_handler.py`**
   - Connection management
   - Message routing
   - Latency buffer

### **Frontend Modules**

1. **`main.js`**
   - App initialization
   - WebSocket connection
   - State management

2. **`scene3d.js`** [CRITICAL]
   - Three.js scene setup
   - Object rendering
   - Camera controls
   - Selection system

3. **`ui_controls.js`**
   - Sensor sliders
   - Toolbar buttons
   - User interactions

4. **`properties_panel.js`**
   - Dynamic panel content
   - Form handling
   - Property updates

5. **`debug_console.js`**
   - Log management
   - Filtering
   - Auto-scroll

---

## 🚀 Success Criteria

Phase 0 is **COMPLETE** when:

- [ ] Desktop app launches and shows UI
- [ ] 3D viewport renders venue correctly
- [ ] Can connect to mobile device via WebSocket
- [ ] Sensor sliders update in real-time
- [ ] Pointer ray visible and moves with sensor data
- [ ] Calibration button locks pointer to back wall
- [ ] Fixture follows pointer automatically
- [ ] Can select objects (venue, fixture, user)
- [ ] Properties panel shows/edits object properties
- [ ] Console logs events with filtering
- [ ] Can save scene to JSON file
- [ ] Can load scene from JSON file
- [ ] Camera controls work smoothly
- [ ] No critical bugs, stable operation

---

**END OF VISUALIZER SPECIFICATIONS**

*This document is the complete blueprint for Phase 0. All implementation should follow these specs exactly.*
