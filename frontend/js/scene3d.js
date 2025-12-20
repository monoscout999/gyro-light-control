/**
 * scene3d.js - Three.js 3D Visualization Module
 *
 * Gyro Light Control Visualizer
 * Módulo crítico de visualización 3D
 *
 * SISTEMA DE COORDENADAS (CRÍTICO):
 * ================================
 * Este proyecto usa Z-UP (igual que el backend Python):
 *
 *      Z (UP/Altura)
 *      ↑
 *      |
 *      |___→ X (Ancho)
 *     /
 *    ↙ Y (Profundidad)
 *
 * - X: 0 a venue.width (izquierda a derecha)
 * - Y: 0 a venue.depth (frente a fondo, Y=max es pared trasera)
 * - Z: 0 a venue.height (piso a techo)
 * - Usuario default: (width/2, depth/2, 1.0) = centro, 1m altura
 *
 * RESPONSABILIDADES:
 * - Renderizar venue con grid y paredes
 * - Visualizar usuario (esfera azul)
 * - Mostrar pointer (rayo láser + punto intersección)
 * - Renderizar fixtures con haz de luz
 * - Sistema de selección (click en objetos)
 * - Controles de cámara orbital
 * - Actualización en tiempo real
 */

// ============================================================================
// COLORES DEL SISTEMA
// ============================================================================

const COLORS = {
    // 3D Objects
    USER: 0x4a9eff,           // Blue sphere
    POINTER_RAY: 0xef4444,    // Red line
    POINTER_DOT: 0xef4444,    // Red sphere

    // Venue
    GRID: 0x404040,           // Dark gray
    WALLS: 0x606060,          // Medium gray
    BACK_WALL: 0x4ade80,      // Green highlight

    // Selection
    SELECTED: 0xfbbf24,       // Yellow highlight

    // Background
    SCENE_BG: 0x1a1a1a        // Very dark gray
};


// ============================================================================
// CLASE SCENE3D
// ============================================================================

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
            selectedObject: null
        };

        // Estado
        this.venueSize = { width: 10, depth: 10, height: 4 };

        // Callbacks
        this.onObjectSelected = null;  // Callback cuando se selecciona objeto

        // Bind methods
        this.animate = this.animate.bind(this);
        this.onWindowResize = this.onWindowResize.bind(this);
        this.onCanvasClick = this.onCanvasClick.bind(this);

        this.init();
    }


    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================

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

        // NOTA: El loop de animación se inicia desde main.js para evitar doble render
        // NO llamar this.animate() aquí

        console.log('✅ Scene3D initialized');
    }

    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(COLORS.SCENE_BG);
        this.scene.fog = new THREE.Fog(COLORS.SCENE_BG, 20, 50);
    }

    createCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);

        // Establecer Z como eje UP (sistema Z-UP)
        this.camera.up.set(0, 0, 1);

        // Posición inicial: vista isométrica
        this.camera.position.set(15, -5, 10);
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

        // Target: centro del venue
        this.controls.target.set(5, 5, 2);
    }


    // ========================================================================
    // VENUE (Espacio 3D)
    // ========================================================================

    createVenue() {
        const group = new THREE.Group();

        // Grid en el piso (plano XY para sistema Z-UP)
        // GridHelper por defecto está en plano XZ (Y-UP), rotamos para Z-UP
        const gridHelper = new THREE.GridHelper(
            this.venueSize.width,
            this.venueSize.width,  // Divisiones cada 1m
            COLORS.GRID,
            COLORS.GRID
        );
        gridHelper.rotation.x = Math.PI / 2;  // Rotar al plano XY (Z-UP)
        gridHelper.position.set(
            this.venueSize.width / 2,
            this.venueSize.depth / 2,
            0
        );
        group.add(gridHelper);

        // Paredes wireframe
        // Para Z-UP: BoxGeometry(X=width, Y=depth, Z=height)
        const wallGeometry = new THREE.BoxGeometry(
            this.venueSize.width,   // X
            this.venueSize.depth,   // Y
            this.venueSize.height   // Z
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
        // Eliminar venue actual y liberar VRAM
        if (this.objects.venue) {
            this.disposeObject(this.objects.venue);
            this.scene.remove(this.objects.venue);
            this.objects.venue = null;
        }

        // Actualizar tamaño
        this.venueSize = { width, depth, height };

        // Recrear venue
        this.createVenue();
    }


    // ========================================================================
    // USUARIO
    // ========================================================================

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


    // ========================================================================
    // POINTER (Rayo + Punto)
    // ========================================================================

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

    updatePointer(intersection) {
        if (!intersection) {
            // Ocultar el pointer ray y dot
            if (this.objects.pointerRay) this.objects.pointerRay.visible = false;
            if (this.objects.pointerDot) this.objects.pointerDot.visible = false;
            return [];
        }

        const point = intersection.point;

        // Actualizar pointer ray - dibujar línea desde usuario hasta punto de intersección
        if (this.objects.pointerRay && this.objects.user) {
            const positions = this.objects.pointerRay.geometry.attributes.position.array;

            // Vértice 0: posición del usuario
            const userPos = this.objects.user.position;
            positions[0] = userPos.x;
            positions[1] = userPos.y;
            positions[2] = userPos.z;

            // Vértice 1: punto de intersección
            positions[3] = point.x;
            positions[4] = point.y;
            positions[5] = point.z;

            // Marcar geometría como actualizada
            this.objects.pointerRay.geometry.attributes.position.needsUpdate = true;

            // Resetear posición del objeto (los vértices ya tienen coords absolutas)
            this.objects.pointerRay.position.set(0, 0, 0);
            this.objects.pointerRay.visible = true;
        }

        // Actualizar pointer dot
        if (this.objects.pointerDot) {
            this.objects.pointerDot.position.copy(point);
            this.objects.pointerDot.visible = true;
        }

        return [{
            position: point.toArray(),
            normal: intersection.face ? intersection.face.normal.toArray() : [0, 1, 0]
        }];
    }


    // ========================================================================
    // SISTEMA DE SELECCIÓN
    // ========================================================================

    setupEventListeners() {
        // Click para seleccionar objetos
        this.renderer.domElement.addEventListener(
            'click',
            this.onCanvasClick,
            false
        );

        // Resize
        window.addEventListener(
            'resize',
            this.onWindowResize,
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
            this.objects.user
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

        // Aplicar highlight (guardando material original para restaurar después)
        object.traverse((child) => {
            if (child.isMesh) {
                // Guardar material original
                child.userData.originalMaterial = child.material;
                // Crear clone para highlight
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
                if (child.isMesh && child.userData.originalMaterial) {
                    // Disponer el material clonado para liberar VRAM
                    if (child.material && child.material !== child.userData.originalMaterial) {
                        child.material.dispose();
                    }
                    // Restaurar material original
                    child.material = child.userData.originalMaterial;
                    delete child.userData.originalMaterial;
                }
            });
            this.objects.selectedObject = null;
        }
    }


    // ========================================================================
    // LOOP DE ANIMACIÓN
    // ========================================================================

    animate() {
        try {
            requestAnimationFrame(this.animate);

            // Actualizar controles
            if (this.controls) {
                this.controls.update();
            }

            // Render
            if (this.renderer && this.scene && this.camera) {
                this.renderer.render(this.scene, this.camera);
            }
        } catch (error) {
            console.error('🔴 Render loop error:', error);
            // Continuar el loop aunque haya error
            requestAnimationFrame(this.animate);
        }
    }

    onWindowResize() {
        if (!this.container) return;

        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        if (this.camera) {
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
        }

        if (this.renderer) {
            this.renderer.setSize(width, height);
        }
    }


    // ========================================================================
    // UTILIDADES
    // ========================================================================

    /**
     * Libera memoria de un objeto THREE.js y todos sus hijos
     * CRÍTICO para evitar memory leaks en VRAM
     */
    disposeObject(object) {
        if (!object) return;

        // Recursivamente disponer hijos
        while (object.children.length > 0) {
            this.disposeObject(object.children[0]);
            object.remove(object.children[0]);
        }

        // Disponer geometría
        if (object.geometry) {
            object.geometry.dispose();
        }

        // Disponer material(es)
        if (object.material) {
            if (Array.isArray(object.material)) {
                object.material.forEach(mat => mat.dispose());
            } else {
                object.material.dispose();
            }
        }
    }

    resetCamera() {
        if (this.camera) {
            this.camera.position.set(8, 8, 6);
        }
        if (this.controls) {
            this.controls.target.set(5, 5, 2);
            this.controls.update();
        }
    }

    render() {
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    resize() {
        if (!this.container) return;

        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        if (this.camera) {
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
        }
        if (this.renderer) {
            this.renderer.setSize(width, height);
        }
    }

    dispose() {
        // Cleanup al destruir
        if (this.renderer) {
            this.renderer.dispose();
            if (this.renderer.domElement) {
                this.renderer.domElement.removeEventListener('click', this.onCanvasClick);
            }
        }
        if (this.controls) {
            this.controls.dispose();
        }

        // Remover event listeners
        window.removeEventListener('resize', this.onWindowResize);
    }
}


// ============================================================================
// EXPORT
// ============================================================================

// Export para usar en index.html
window.Scene3D = Scene3D;