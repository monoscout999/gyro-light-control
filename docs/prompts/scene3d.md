# PROMPT: Implementar scene3d.js - Visualización 3D con Three.js

## CONTEXTO DEL PROYECTO

Estás implementando el módulo de visualización 3D que renderiza el venue, el puntero, y los fixtures en tiempo real usando Three.js. Este es el **corazón visual** del proyecto - donde todo cobra vida en 3D.

Este módulo se ejecuta en el navegador y NO tiene acceso directo a los módulos Python del backend.

---

## TU TAREA

Crear el archivo `scene3d.js` que:
- Configure escena Three.js completa
- Renderice venue (grid + paredes wireframe)
- Visualice usuario (esfera azul)
- Muestre pointer (rayo láser rojo + punto intersección)
- Renderice fixtures con haz de luz
- Implemente sistema de selección (click en objetos)
- Controles de cámara orbital
- Actualización en tiempo real vía WebSocket

---

## ESPECIFICACIONES TÉCNICAS

### Sistema de Coordenadas (IMPORTANTE)

**Mismo que el backend:**
```
        Norte (+Y) ← pared trasera
           ↑
           |
Oeste ←----●---→ Este
(-X)    usuario   (+X)
           |
           ↓
        Sur (-Y)

Z = Vertical (↑ arriba)
```

**Three.js usa el mismo sistema** - NO hay conversión necesaria.

### Colores del Sistema

```javascript
const COLORS = {
    // 3D Objects
    USER: 0x4a9eff,           // Blue sphere
    POINTER_RAY: 0xef4444,    // Red line
    POINTER_DOT: 0xef4444,    // Red sphere
    FIXTURE: 0xa0a0a0,        // Gray cone
    LIGHT_BEAM: 0xffffff,     // White cone
    
    // Venue
    GRID: 0x404040,           // Dark gray
    WALLS: 0x606060,          // Medium gray
    BACK_WALL: 0x4ade80,      // Green (highlight)
    
    // Selection
    SELECTED: 0xfbbf24,       // Yellow highlight
    
    // Background
    SCENE_BG: 0x1a1a1a        // Very dark gray
};
```

---

## ESTRUCTURA DE LA CLASE

```javascript
/**
 * Scene3D - Gestor de visualización 3D con Three.js
 * 
 * Responsabilidades:
 * - Crear y gestionar escena Three.js
 * - Renderizar venue, usuario, pointer, fixtures
 * - Sistema de selección de objetos
 * - Controles de cámara orbital
 * - Actualización en tiempo real
 */
class Scene3D {
    constructor(containerElement) {
        this.container = containerElement;
        
        // Three.js core
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        // Raycaster para selección
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        // Referencias a objetos en escena
        this.objects = {
            venue: null,
            user: null,
            pointerRay: null,
            pointerDot: null,
            fixtures: new Map(),  // id → fixture mesh
            selectedObject: null
        };
        
        // Estado
        this.venueSize = { width: 10, depth: 10, height: 4 };
        
        // Callbacks
        this.onObjectSelected = null;  // Callback cuando se selecciona objeto
        
        this.init();
    }
    
    /**
     * Inicializa toda la escena 3D
     */
    init() {
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.createLights();
        this.createControls();
        
        // Crear objetos iniciales
        this.createVenue();
        this.createUser();
        this.createPointer();
        
        // Event listeners
        this.setupEventListeners();
        
        // Iniciar loop de animación
        this.animate();
    }
    
    // ... métodos implementados abajo
}
```

---

## MÉTODOS PRINCIPALES

### 1. Setup Inicial

```javascript
createScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(COLORS.SCENE_BG);
    this.scene.fog = new THREE.Fog(COLORS.SCENE_BG, 20, 50);
}

createCamera() {
    const aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
    
    // Posición inicial: vista isométrica
    this.camera.position.set(8, 8, 6);
    this.camera.lookAt(5, 5, 2);  // Mirar al centro del venue
}

createRenderer() {
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(
        this.container.clientWidth, 
        this.container.clientHeight
    );
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.container.appendChild(this.renderer.domElement);
}

createLights() {
    // Luz ambiental suave
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambient);
    
    // Luz direccional (simula sol)
    const directional = new THREE.DirectionalLight(0xffffff, 0.8);
    directional.position.set(10, 15, 10);
    this.scene.add(directional);
}

createControls() {
    // Requiere: OrbitControls importado
    this.controls = new THREE.OrbitControls(
        this.camera, 
        this.renderer.domElement
    );
    
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.minDistance = 2;
    this.controls.maxDistance = 30;
    this.controls.maxPolarAngle = Math.PI / 2;  // No ir debajo del piso
    
    // Target: centro del venue
    this.controls.target.set(5, 5, 2);
}
```

### 2. Venue (Espacio 3D)

```javascript
createVenue() {
    const group = new THREE.Group();
    
    // Grid en el piso
    const gridHelper = new THREE.GridHelper(
        this.venueSize.width,
        this.venueSize.width,  // Divisiones cada 1m
        COLORS.GRID,
        COLORS.GRID
    );
    gridHelper.rotation.x = 0;  // Grid horizontal
    gridHelper.position.set(
        this.venueSize.width / 2,
        this.venueSize.depth / 2,
        0
    );
    group.add(gridHelper);
    
    // Paredes wireframe
    const wallGeometry = new THREE.BoxGeometry(
        this.venueSize.width,
        this.venueSize.depth,
        this.venueSize.height
    );
    const wallEdges = new THREE.EdgesGeometry(wallGeometry);
    const wallLines = new THREE.LineSegments(
        wallEdges,
        new THREE.LineBasicMaterial({ color: COLORS.WALLS })
    );
    wallLines.position.set(
        this.venueSize.width / 2,
        this.venueSize.depth / 2,
        this.venueSize.height / 2
    );
    group.add(wallLines);
    
    // Highlight pared trasera (Y máximo)
    const backWallGeometry = new THREE.PlaneGeometry(
        this.venueSize.width,
        this.venueSize.height
    );
    const backWallMaterial = new THREE.MeshBasicMaterial({
        color: COLORS.BACK_WALL,
        transparent: true,
        opacity: 0.1,
        side: THREE.DoubleSide
    });
    const backWall = new THREE.Mesh(backWallGeometry, backWallMaterial);
    backWall.position.set(
        this.venueSize.width / 2,
        this.venueSize.depth,  // Pared trasera
        this.venueSize.height / 2
    );
    backWall.rotation.x = Math.PI / 2;  // Vertical
    group.add(backWall);
    
    // Marcar centro de pared trasera
    const centerMarker = new THREE.Mesh(
        new THREE.SphereGeometry(0.1, 16, 16),
        new THREE.MeshBasicMaterial({ color: COLORS.BACK_WALL })
    );
    centerMarker.position.set(
        this.venueSize.width / 2,
        this.venueSize.depth,
        this.venueSize.height / 2
    );
    group.add(centerMarker);
    
    group.name = 'venue';
    this.objects.venue = group;
    this.scene.add(group);
}

updateVenueDimensions(width, depth, height) {
    // Eliminar venue actual
    if (this.objects.venue) {
        this.scene.remove(this.objects.venue);
    }
    
    // Actualizar tamaño
    this.venueSize = { width, depth, height };
    
    // Recrear venue
    this.createVenue();
}
```

### 3. Usuario

```javascript
createUser() {
    const geometry = new THREE.SphereGeometry(0.3, 32, 32);
    const material = new THREE.MeshStandardMaterial({
        color: COLORS.USER,
        metalness: 0.5,
        roughness: 0.5
    });
    
    const user = new THREE.Mesh(geometry, material);
    user.position.set(
        this.venueSize.width / 2,
        this.venueSize.depth / 2,
        1.0  // Altura default
    );
    
    user.name = 'user';
    this.objects.user = user;
    this.scene.add(user);
}

updateUserHeight(height) {
    if (this.objects.user) {
        this.objects.user.position.z = height;
    }
}
```

### 4. Pointer (Rayo + Punto)

```javascript
createPointer() {
    // Rayo láser (línea)
    const rayMaterial = new THREE.LineBasicMaterial({
        color: COLORS.POINTER_RAY,
        linewidth: 2
    });
    const rayGeometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, 1, 0)
    ]);
    const ray = new THREE.Line(rayGeometry, rayMaterial);
    ray.name = 'pointerRay';
    this.objects.pointerRay = ray;
    this.scene.add(ray);
    
    // Punto de intersección
    const dotGeometry = new THREE.SphereGeometry(0.2, 16, 16);
    const dotMaterial = new THREE.MeshBasicMaterial({
        color: COLORS.POINTER_DOT
    });
    const dot = new THREE.Mesh(dotGeometry, dotMaterial);
    dot.name = 'pointerDot';
    this.objects.pointerDot = dot;
    this.scene.add(dot);
}

updatePointer(direction, intersection) {
    /**
     * Actualiza posición del pointer
     * 
     * @param {Array} direction - Vector [x, y, z] direccional
     * @param {Array} intersection - Punto [x, y, z] donde toca pared
     */
    if (!this.objects.user) return;
    
    const userPos = this.objects.user.position;
    const targetPos = new THREE.Vector3(...intersection);
    
    // Actualizar rayo
    const points = [
        new THREE.Vector3(userPos.x, userPos.y, userPos.z),
        targetPos
    ];
    this.objects.pointerRay.geometry.setFromPoints(points);
    
    // Actualizar punto
    this.objects.pointerDot.position.copy(targetPos);
}
```

### 5. Fixtures

```javascript
createFixture(fixtureData) {
    /**
     * Crea y agrega un fixture a la escena
     * 
     * @param {Object} fixtureData - {id, name, position, pan, tilt, ...}
     */
    const group = new THREE.Group();
    
    // Cuerpo del fixture (cono)
    const bodyGeometry = new THREE.ConeGeometry(0.5, 1, 8);
    const bodyMaterial = new THREE.MeshStandardMaterial({
        color: COLORS.FIXTURE,
        metalness: 0.6,
        roughness: 0.4
    });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    
    // Orientar según mounting
    if (fixtureData.mounting === 'ceiling') {
        body.rotation.x = Math.PI;  // Cono apuntando hacia abajo
    } else if (fixtureData.mounting === 'floor') {
        body.rotation.x = 0;  // Cono apuntando hacia arriba
    }
    
    group.add(body);
    
    // Haz de luz (cono semi-transparente)
    const beamGeometry = new THREE.ConeGeometry(0.3, 3, 8, 1, true);
    const beamMaterial = new THREE.MeshBasicMaterial({
        color: COLORS.LIGHT_BEAM,
        transparent: true,
        opacity: 0.3,
        side: THREE.DoubleSide
    });
    const beam = new THREE.Mesh(beamGeometry, beamMaterial);
    beam.position.set(0, 0, -1.5);  // Offset del cono
    group.add(beam);
    
    // Posicionar fixture
    group.position.set(...fixtureData.position);
    group.name = `fixture_${fixtureData.id}`;
    group.userData = { id: fixtureData.id, type: 'fixture' };
    
    this.objects.fixtures.set(fixtureData.id, group);
    this.scene.add(group);
    
    return group;
}

updateFixture(fixtureId, pan, tilt) {
    /**
     * Actualiza rotación de un fixture
     * 
     * @param {String} fixtureId - UUID del fixture
     * @param {Number} pan - Ángulo pan en grados
     * @param {Number} tilt - Ángulo tilt en grados
     */
    const fixture = this.objects.fixtures.get(fixtureId);
    if (!fixture) return;
    
    // Convertir grados a radianes
    const panRad = THREE.MathUtils.degToRad(pan);
    const tiltRad = THREE.MathUtils.degToRad(tilt);
    
    // Aplicar rotaciones
    fixture.rotation.z = panRad;   // Pan (rotación horizontal)
    fixture.rotation.x = tiltRad;  // Tilt (rotación vertical)
}

removeFixture(fixtureId) {
    const fixture = this.objects.fixtures.get(fixtureId);
    if (fixture) {
        this.scene.remove(fixture);
        this.objects.fixtures.delete(fixtureId);
    }
}
```

### 6. Sistema de Selección

```javascript
setupEventListeners() {
    // Click para seleccionar objetos
    this.renderer.domElement.addEventListener(
        'click',
        (event) => this.onCanvasClick(event),
        false
    );
    
    // Resize
    window.addEventListener(
        'resize',
        () => this.onWindowResize(),
        false
    );
}

onCanvasClick(event) {
    // Calcular posición del mouse normalizada (-1 a 1)
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    
    // Raycast
    this.raycaster.setFromCamera(this.mouse, this.camera);
    
    // Objetos seleccionables
    const selectableObjects = [
        this.objects.venue,
        this.objects.user,
        ...Array.from(this.objects.fixtures.values())
    ].filter(obj => obj !== null);
    
    const intersects = this.raycaster.intersectObjects(
        selectableObjects,
        true  // recursive
    );
    
    if (intersects.length > 0) {
        // Encontrar el objeto root (venue, user, o fixture)
        let selectedObj = intersects[0].object;
        while (selectedObj.parent && selectedObj.parent !== this.scene) {
            selectedObj = selectedObj.parent;
        }
        
        this.selectObject(selectedObj);
    } else {
        this.deselectAll();
    }
}

selectObject(object) {
    // Deseleccionar anterior
    this.deselectAll();
    
    // Aplicar highlight
    object.traverse((child) => {
        if (child.isMesh) {
            child.material = child.material.clone();
            child.material.emissive = new THREE.Color(COLORS.SELECTED);
            child.material.emissiveIntensity = 0.5;
        }
    });
    
    this.objects.selectedObject = object;
    
    // Callback
    if (this.onObjectSelected) {
        const objectType = object.userData.type || object.name;
        this.onObjectSelected({
            type: objectType,
            id: object.userData.id,
            object: object
        });
    }
}

deselectAll() {
    if (this.objects.selectedObject) {
        this.objects.selectedObject.traverse((child) => {
            if (child.isMesh && child.material.emissive) {
                child.material.emissive.setHex(0x000000);
                child.material.emissiveIntensity = 0;
            }
        });
        this.objects.selectedObject = null;
    }
}
```

### 7. Loop de Animación

```javascript
animate() {
    requestAnimationFrame(() => this.animate());
    
    // Actualizar controles
    this.controls.update();
    
    // Render
    this.renderer.render(this.scene, this.camera);
}

onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    
    this.renderer.setSize(width, height);
}
```

### 8. Utilidades

```javascript
resetCamera() {
    this.camera.position.set(8, 8, 6);
    this.controls.target.set(5, 5, 2);
    this.controls.update();
}

dispose() {
    // Cleanup al destruir
    this.renderer.dispose();
    this.controls.dispose();
    
    // Remover event listeners
    window.removeEventListener('resize', this.onWindowResize);
}
```

---

## ARCHIVO COMPLETO MÍNIMO

```javascript
/**
 * scene3d.js - Three.js 3D Visualization Module
 * 
 * Gyro Light Control Visualizer
 * Módulo crítico de visualización 3D
 */

// COLORES
const COLORS = {
    USER: 0x4a9eff,
    POINTER_RAY: 0xef4444,
    POINTER_DOT: 0xef4444,
    FIXTURE: 0xa0a0a0,
    LIGHT_BEAM: 0xffffff,
    GRID: 0x404040,
    WALLS: 0x606060,
    BACK_WALL: 0x4ade80,
    SELECTED: 0xfbbf24,
    SCENE_BG: 0x1a1a1a
};

class Scene3D {
    // Implementar todos los métodos según especificación arriba
    // ...
}

// Export para usar en index.html
window.Scene3D = Scene3D;
```

---

## DEPENDENCIAS EN HTML

```html
<!-- En index.html -->
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
<script src="js/scene3d.js"></script>
```

---

## CRITERIOS DE VALIDACIÓN

- [ ] Scene, camera, renderer inicializan correctamente
- [ ] Venue renderiza con grid y paredes
- [ ] Pared trasera destacada en verde
- [ ] Usuario (esfera azul) visible
- [ ] Pointer (rayo + punto) actualizable
- [ ] Fixtures crean y rotan correctamente
- [ ] Sistema de selección funciona (click)
- [ ] Controles orbitales fluidos
- [ ] Resize window funciona
- [ ] Sin errores en console

---

## NOTAS IMPORTANTES

1. **Three.js desde CDN**:
   - Versión 0.160+ recomendada
   - OrbitControls en examples/js/

2. **Sistema de coordenadas**:
   - IGUAL al backend (no conversión)
   - Z hacia arriba

3. **Performance**:
   - Geometrías simples (low poly)
   - Materials básicos
   - 60 FPS objetivo

4. **Selección**:
   - Raycasting en click
   - Highlight con emissive
   - Callback a UI externa

---

## TIEMPO ESTIMADO

**40-50 minutos** (el módulo más complejo del frontend)

---

**ENTREGA**: Archivo `scene3d.js` completo, funcional con Three.js, renderizando venue + pointer + fixtures.
