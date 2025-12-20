# 🎯 Project Vision: 3D Gyroscope Pointer for Moving Lights Control

**Project Code**: GYRO-LIGHT-CONTROL  
**Created**: 2024-12-15  
**Status**: PLANNING PHASE  
**Lead Developer**: User  

---

## 📋 Executive Summary

Application that uses mobile device gyroscope sensors to create a 3D pointer in virtual space, enabling intuitive calibration and control of professional moving lights (stage lighting fixtures).

---

## 🎭 Core Concept

**The Problem**: Calibrating moving stage lights' positions is tedious and requires multiple people or complex interfaces.

**The Solution**: Point your phone at where you want the light to aim → the light moves there.

---

## 🏗️ Technical Architecture

### **Platform Stack**
- **Desktop Application**: Python-based server
  - Creates local web server
  - Handles 3D simulation/visualization
  - Manages DMX output via ArtNet protocol
  - Central control hub

- **Mobile Interface**: Web-based (responsive HTML/CSS/JS)
  - Accessed via browser (no app installation needed)
  - Streams gyroscope data to server
  - Minimal UI: pointer visual + calibration buttons
  - Connection via local network

### **Communication Flow**
```
[Mobile Browser] ←→ [Python Server] ←→ [DMX/ArtNet] ←→ [Moving Lights]
     WebSocket          Processing           Network         Hardware
```

---

## 🎮 User Workflow (Target Experience)

### Phase 1: Setup
1. User runs Python desktop app
2. Desktop shows: server URL (e.g., `http://192.168.1.10:8080`)
3. User opens that URL on mobile browser
4. Mobile connects, shows "READY" status

### Phase 2: Calibration
1. User stands at **venue center** (configurable, default: 10x10m venue, user at 5,5)
2. User aims phone at **back wall center**
3. User presses **"CALIBRATE"** button on mobile
4. System establishes coordinate reference frame
5. ⚠️ **CRITICAL CHALLENGE**: This is where mathematical complexity begins (deferred to detailed docs)

### Phase 3: Operation
1. User points phone in any direction
2. Desktop shows pointer in 3D space
3. Selected moving light follows pointer (Phase 2 feature)

---

## 📐 Coordinate System (High-Level)

- **Venue**: Configurable XYZ space (default: 10m × 10m × height)
- **Origin**: User-defined center point (default: 5, 5, 0)
- **Calibration Reference**: Back wall center
- **Mobile Orientation**: Raw gyroscope → quaternions/euler angles → 3D vector

**⚠️ DEFERRED**: Detailed mathematical formulas documented separately in `02_validated_formulas.md`

---

## 🎯 Development Phases (MVP Strategy)

### **PHASE 0: 3D Visualizer (Standalone Debug Tool)** ✋ **← START HERE**
**Goal**: Build comprehensive visualization and testing tool FIRST

**Deliverables**:
- ✅ Python desktop app (FastAPI backend + Three.js frontend)
- ✅ 3D viewport showing venue (10×10×4m configurable)
- ✅ READ-ONLY sliders displaying alpha/beta/gamma from sensor data
- ✅ Pointer visualization (laser ray + intersection point)
- ✅ 1 moving light fixture with automatic following
- ✅ Properties panel (venue, fixture, user configuration)
- ✅ Debug console with filters
- ✅ Manual calibration system
- ✅ Save/load scene configurations
- ✅ Simple fixture creation interface

**Success Criteria**:
- Receive sensor data from mobile → see pointer move in 3D
- Calibration locks pointer to back wall center
- Fixture follows pointer automatically
- Can save and reload complete scenes

---

### **PHASE 1: Real Sensor Integration** 
**Goal**: Connect real mobile gyroscope to visualizer

**Deliverables**:
- ✅ Mobile web interface (sensor access)
- ✅ WebSocket streaming to visualizer
- ✅ Real-time data flow with latency buffer
- ✅ Smooth pointer movement (<100ms latency)

**Success Criteria**: 
- Point phone → see pointer move in 3D space smoothly
- Calibration works with real device
- System handles network latency gracefully

---

### **PHASE 2: Light Control** ⏸️ **← LATER**
**Goal**: Connect to real hardware

**Deliverables**:
- ✅ DMX/ArtNet output working
- ✅ Library for various light models (generic + custom)
- ✅ Pointer → Pan/Tilt translation
- ✅ Multi-light support
- ✅ Save/load configurations

**Success Criteria**:
- Point phone → light physically moves to that position

---

## 🚫 What This Document Does NOT Cover

These are intentionally deferred to specialized documents:

- ❌ Detailed gyroscope math formulas → `02_validated_formulas.md`
- ❌ DMX/ArtNet protocol specifics → `03_module_architecture.md`
- ❌ UI/UX design details → `03_module_architecture.md`
- ❌ Code implementation → `/src/` directory
- ❌ Calibration algorithm details → `02_validated_formulas.md`

---

## 🧠 Development Philosophy (CRITICAL)

### **Why This Project Failed Before**

**Problem**: Working with AI agents on long sessions led to:
1. ✅ Solution A works → implement Solution B → Solution A breaks
2. Mathematical formulas "drift" between versions
3. Context contamination (mixing unrelated features)
4. No "source of truth" for validated code

### **The Solution: Multi-Agent Modular Architecture**

**Core Principle**: 
> "No single agent has the full context. Each agent owns one domain. A Registrar Agent maintains the master state."

**Agent Roles**:
1. **Registrar Agent** (Documentation custodian)
   - NO CODE GENERATION
   - Maintains decision logs
   - Marks validated code as immutable
   - Generates clean contexts for other agents

2. **Prompt Engineer Agent** (Context preparer)
   - Prevents contamination
   - Creates focused prompts for specialists
   
3. **Math Agent** (Sensor/3D calculations)
   - Owns gyroscope formulas
   - 3D transformations
   - Calibration algorithms

4. **Backend Agent** (Python server)
   - Server architecture
   - WebSocket handling
   - DMX output

5. **Frontend Agent** (Mobile UI)
   - Web interface
   - Sensor access
   - Real-time updates

**Protocol**:
- Each coding session starts with Registrar providing context
- After validation, code marked `[VALIDADO-{date}]`
- Validated code CANNOT be modified without explicit approval
- All decisions logged with rationale

---

## 📊 Success Metrics

**Phase 1 Complete When**:
- [ ] Server runs without errors
- [ ] Mobile connects reliably
- [ ] 3D visualization responsive (<100ms latency)
- [ ] Calibration reproducible (same result on repeated attempts)
- [ ] Code is modular and documented

**Phase 2 Complete When**:
- [ ] At least 1 real moving light controlled successfully
- [ ] Pointer-to-light accuracy within ±5° (acceptable for stage use)
- [ ] Configuration save/load works
- [ ] Multi-light support functional

---

## 🔒 Immutability Rules

**This Document Cannot Change**:
- Core concept (gyroscope → 3D pointer → light control)
- Phase 1 before Phase 2 ordering
- Multi-agent architecture principle
- Technology stack (Python + Web)

**This Document Can Evolve**:
- Venue size defaults
- Exact protocols (as long as DMX/ArtNet compatible)
- Additional phases beyond Phase 2
- Non-breaking refinements

---

## 📝 Related Documents (To Be Created)

- `01_technical_requirements.md` - Detailed specs
- `02_validated_formulas.md` - Math that WORKS
- `03_module_architecture.md` - Code structure
- `04_decision_log.md` - Why we chose X over Y
- `05_agent_protocols.md` - How to interact with each agent

---

## 🎬 Next Steps (When Development Starts)

1. **Create remaining documentation** (with Registrar Agent)
2. **Design Phase 1 architecture** (modular structure)
3. **Prototype sensor streaming** (simplest possible version)
4. **Validate core math** (quaternion → vector transform)
5. **Build 3D visualization** (Three.js or similar)
6. **Integrate & test** (end-to-end Phase 1)

---

## 💡 Developer Notes

**When returning to this project**:
- Read this document first (5 min)
- Check `04_decision_log.md` for latest state
- Consult `02_validated_formulas.md` before touching math
- Never modify `[VALIDADO]` code without Registrar review

**When stuck**:
- Return to this vision
- Is the problem blocking Phase 1 or Phase 2?
- Can it be deferred?
- Is there a simpler approach?

---

**END OF VISION DOCUMENT**

*This is the anchor. Everything else is implementation detail.*
