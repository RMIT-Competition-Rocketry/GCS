/**
 * GCS Rocket Viewer
 *
 * This script renders a 3D rocket model using Three.js, and updates its orientation in real-time
 * using quaternion data. Smooth interpolation is supported to improve visual stability during flight.
 * 
 * Functions and constants should be prefixed with "rocket_" for clarity and namespace safety.
 */

import * as THREE from "./libraries/three.module.js";
import { GLTFLoader } from "./libraries/GLTFLoader.js";

// === Core Variables ===
let rocket = null;                                // The main rocket model group
let targetQuat = new THREE.Quaternion();          // Most recent target orientation
let hasReceivedQuaternion = false;                // Flag to begin rendering orientation once data is available

// === Orientation Smoothing Settings ===
const smoothingActivated = true;                  // Toggle smooth transitions between updates
const tau = 0.13;                                  // Time constant for exponential smoothing (in seconds)
let lastFrameTs = performance.now();              // Timestamp of the last frame (used for dt calculation)

window.addEventListener("DOMContentLoaded", () => {
    // === Canvas and Renderer Setup ===
    const container = document.getElementById("rocketViewerContainer");
    const canvas = document.getElementById("rocketCanvas");

    const renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,       // Smooth edges
        alpha: true            // Transparent background
    });

    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;

    // === Create Scene ===
    const scene = new THREE.Scene();
    scene.background = null; // Keep canvas transparent

    // === Camera Setup (Orthographic for a clean top-down view) ===
    const aspect = container.clientWidth / container.clientHeight;
    const viewSize = 10;
    const camera = new THREE.OrthographicCamera(
        -aspect * viewSize / 2,  // left
        aspect * viewSize / 2,   // right
        viewSize / 2,            // top
        -viewSize / 2,           // bottom
        0.1,
        1000
    );
    camera.position.set(0, 0, 20);
    camera.lookAt(0, 0, 0);

    // === Lighting Configuration (balanced accordingly for model clarity) ===
    const lights = [
        new THREE.DirectionalLight(0xffffff, 36),
        new THREE.DirectionalLight(0xffffff, 24),
        new THREE.SpotLight(0xffffff, 36),
        new THREE.HemisphereLight(0xffffff, 0x333333, 7.5)
    ];
    lights[0].position.set(15, 30, 20);
    lights[1].position.set(-15, 20, -10);
    lights[2].position.set(0, 30, 25);
    lights[2].angle = Math.PI / 5;
    lights[2].penumbra = 0.4;
    lights[2].decay = 1;
    lights[2].distance = 200;
    lights[3].position.set(50, 0, 0);
    lights.forEach(light => scene.add(light));

    // === Environment Texture (adds reflections and realism) ===
    const envTextureLoader = new THREE.CubeTextureLoader();
    const origin = new THREE.Vector3(3, -3.75, 0); // Not used in final render, just a helper reference
    scene.environment = envTextureLoader.load([
        "/img/textures/posx.jpg", "/img/textures/negx.jpg",
        "/img/textures/posy.jpg", "/img/textures/negy.jpg",
        "/img/textures/posz.jpg", "/img/textures/negz.jpg",
    ]);

    // === Load and Setup Rocket Model ===
    new GLTFLoader().load(
        "/static/models/rocket_model.glb",
        gltf => {
            const model = gltf.scene;
            model.scale.set(2, 2, 2); // Resize for better visibility

            // Center the model at the origin for rotation
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            model.position.sub(center);

            rocket = new THREE.Group();
            rocket.add(model);
            scene.add(rocket);

            // Dynamically position camera to fit model size
            const size = box.getSize(new THREE.Vector3()).length();
            camera.position.set(0, 0, size * 1.5);
            camera.lookAt(new THREE.Vector3(0, 0, 0));

            animate(); // Start render loop
        },
        xhr => console.log(`Loading: ${((xhr.loaded / xhr.total) * 100).toFixed(1)}%`),
        err => console.error("Error loading model:", err)
    );

    // === Main Render Loop ===
    function animate() {
        requestAnimationFrame(animate);

        const now = performance.now();
        const dt = (now - lastFrameTs) / 1000;
        lastFrameTs = now;

        // Only rotate model once we've received a quaternion
        if (rocket && hasReceivedQuaternion) {
            if (smoothingActivated) {
                // compute frame-based alpha from time constant tau
                // (smooth with variable dt because we're using unreliable UDP)
                const alpha = 1 - Math.exp(-dt / tau);
                // smoothly blend current orientation → target
                rocket.quaternion.slerp(targetQuat, alpha);
            } else {
                // snap instantly to target orientation
                rocket.quaternion.copy(targetQuat);
            }

            // Extract Euler angles from smoothed quaternion for display
            const hudEuler = new THREE.Euler().setFromQuaternion(rocket.quaternion, 'XYZ');
            displaySetValue("rocket-pitch", THREE.MathUtils.radToDeg(hudEuler.x), 1);
            displaySetValue("rocket-yaw", THREE.MathUtils.radToDeg(hudEuler.y), 1);
            displaySetValue("rocket-roll", THREE.MathUtils.radToDeg(hudEuler.z), 1);
        }

        renderer.render(scene, camera);
    }

    // === Responsive Canvas Resize ===
    function onResize() {
        renderer.setSize(container.clientWidth, container.clientHeight);
        const aspect = container.clientWidth / container.clientHeight;
        camera.left = -aspect * viewSize / 2;
        camera.right = aspect * viewSize / 2;
        camera.top = viewSize / 2;
        camera.bottom = -viewSize / 2;
        camera.updateProjectionMatrix();
    }
    window.addEventListener("resize", onResize);

    // === External Quaternion Update Entry Point ===
    // Call this from elsewhere to update rocket orientation.
    window.rocketUpdate = function (data) {
        if (
            data.qw == null || data.qx == null ||
            data.qy == null || data.qz == null
        ) return;

        targetQuat.set(data.qx, data.qy, data.qz, data.qw).normalize();
        hasReceivedQuaternion = true;
    };
});
