import * as THREE from "./three.module.js";
import { GLTFLoader } from "./GLTFLoader.js";

let rocket = null;
let quat = new THREE.Quaternion();
let lastQuaternion = new THREE.Quaternion(); // backup for packet loss
let euler = new THREE.Euler();
let hasReceivedQuaternion = false;

let xArrow, yArrow, zArrow;

window.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("rocketViewerContainer");
    const canvas = document.getElementById("rocketCanvas");

    const renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: true,
    });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;

    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 2, 8);

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
    lights[3].position.set(0, 50, 0);
    lights.forEach(light => scene.add(light));

    const envTextureLoader = new THREE.CubeTextureLoader();
    scene.environment = envTextureLoader.load([
        "/img/textures/posx.jpg",
        "/img/textures/negx.jpg",
        "/img/textures/posy.jpg",
        "/img/textures/negy.jpg",
        "/img/textures/posz.jpg",
        "/img/textures/negz.jpg",
    ]);

    new GLTFLoader().load(
        "/static/models/rocket_model.glb",
        gltf => {
            const model = gltf.scene;
            model.scale.set(2, 2, 2);

            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            model.position.sub(center);

            rocket = new THREE.Group();
            rocket.add(model);
            scene.add(rocket);

            // Body-frame axis arrows (local to rocket)
            const origin = new THREE.Vector3(0, 0, 0);
            xArrow = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), origin, 2, 0xff0000); // Red = X
            yArrow = new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), origin, 2, 0x00ff00); // Green = Y
            zArrow = new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), origin, 2, 0x0000ff); // Blue = Z
            rocket.add(xArrow, yArrow, zArrow); // Add arrows to rocket itself

            // Fit camera
            const size = box.getSize(new THREE.Vector3()).length();
            camera.position.set(0, 0, size * 1.5);
            camera.lookAt(new THREE.Vector3(0, 0, 0));

            animate();
        },
        xhr => console.log(`Loading: ${((xhr.loaded / xhr.total) * 100).toFixed(1)}%`),
        err => console.error("Error loading model:", err)
    );

    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }

    function onResize() {
        renderer.setSize(container.clientWidth, container.clientHeight);
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
    }

    window.addEventListener("resize", onResize);

    // === LIVE ORIENTATION UPDATER  ===
    function rocketUpdate(data) {
        if (!rocket || !data) return;

        const pitchEl = document.getElementById("pitchDisplay");
        const rollEl = document.getElementById("rollDisplay");
        const yawEl = document.getElementById("yawDisplay");

        if (
            data.qx !== undefined &&
            data.qy !== undefined &&
            data.qz !== undefined &&
            data.qw !== undefined
        ) {
            quat.set(data.qx, data.qy, data.qz, data.qw).normalize();
            lastQuaternion.copy(quat);
            hasReceivedQuaternion = true;
        } else if (hasReceivedQuaternion) {
            quat.copy(lastQuaternion);
        } else {
            if (pitchEl && yawEl && rollEl) {
                pitchEl.textContent = "Pitch: — (no data)";
                rollEl.textContent = "Roll:  — (no data)";
                yawEl.textContent = "Yaw:   — (no data)";
            }
            return;
        }

        // Apply Blender +Z correction
        const correction = new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0));
        const correctedQuat = quat.clone().premultiply(correction);

        // Apply quaternion to model
        rocket.setRotationFromQuaternion(correctedQuat);

        // Rotate body-frame vectors
        const bodyX = new THREE.Vector3(1, 0, 0).applyQuaternion(correctedQuat);
        const bodyY = new THREE.Vector3(0, 1, 0).applyQuaternion(correctedQuat);
        const bodyZ = new THREE.Vector3(0, 0, 1).applyQuaternion(correctedQuat);

        // Update arrow directions
        xArrow.setDirection(bodyX);
        yArrow.setDirection(bodyY);
        zArrow.setDirection(bodyZ);

        // Update Euler HUD
        euler.setFromQuaternion(correctedQuat, 'XYZ');
        const pitch = THREE.MathUtils.radToDeg(euler.x);
        const yaw   = THREE.MathUtils.radToDeg(euler.y);
        const roll  = THREE.MathUtils.radToDeg(euler.z);

        if (pitchEl && yawEl && rollEl) {
            pitchEl.textContent = `Pitch: ${pitch.toFixed(1)}°`;
            yawEl.textContent   = `Yaw:   ${yaw.toFixed(1)}°`;
            rollEl.textContent  = `Roll:  ${roll.toFixed(1)}°`;
        }
    }

    // Make rocketUpdate accessible globally
    window.rocketUpdate = rocketUpdate;
});
