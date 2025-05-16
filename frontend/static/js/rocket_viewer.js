import * as THREE from "./three.module.js";
import { GLTFLoader } from "./GLTFLoader.js";

let rocket = null;
let quat = new THREE.Quaternion();
let lastQuaternion = new THREE.Quaternion();
let euler = new THREE.Euler();
let hasReceivedQuaternion = false;

window.addEventListener("DOMContentLoaded", () => {
    console.log("Loaded rocket_viewer.js");

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

    const lightMultiplier = 3;
    const lights = [
        new THREE.DirectionalLight(0xffffff, 12 * lightMultiplier),
        new THREE.DirectionalLight(0xffffff, 8 * lightMultiplier),
        new THREE.SpotLight(0xffffff, 12 * lightMultiplier),
        new THREE.HemisphereLight(0xffffff, 0x333333, 2.5 * lightMultiplier)
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
            model.scale.set(3, 3, 3);

            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            model.position.sub(center);

            rocket = new THREE.Group();
            rocket.add(model);
            scene.add(rocket);

            // Fixed axis arrows in world space (bottom right)
            const axisLength = 1.7;
            const headLength = 0.4;
            const headWidth = 0.2;
            const origin = new THREE.Vector3(3.5, -4.2, 2.5);

            const xArrow = new THREE.ArrowHelper(
                new THREE.Vector3(1, 0, 0), origin, axisLength, 0xff0000, headLength, headWidth
            );
            const yArrow = new THREE.ArrowHelper(
                new THREE.Vector3(0, 1, 0), origin, axisLength, 0x00ff00, headLength, headWidth
            );
            const zArrow = new THREE.ArrowHelper(
                new THREE.Vector3(0, 0, 1), origin, axisLength, 0x0000ff, headLength, headWidth
            );

            scene.add(xArrow, yArrow, zArrow);

            const size = box.getSize(new THREE.Vector3()).length();
            camera.position.set(0, 0, size * 1.1);
            camera.lookAt(new THREE.Vector3(0, 0, 0));

            renderScene();
        },
        xhr => console.log(`Loading: ${((xhr.loaded / xhr.total) * 100).toFixed(1)}%`),
        err => console.error("Error loading model:", err)
    );

    function renderScene() {
        renderer.render(scene, camera);
    }

    function onResize() {
        renderer.setSize(container.clientWidth, container.clientHeight);
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderScene();
    }

    window.addEventListener("resize", onResize);

    // === LIVE ORIENTATION UPDATER ===
    function rocketUpdate(data) {
        if (!rocket || !data) return;

        const pitchEl = document.querySelector(".rocket-pitch");
        const yawEl = document.querySelector(".rocket-yaw");
        const rollEl = document.querySelector(".rocket-roll");

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
            console.warn("Quaternion packet missing. Reusing last known orientation.");
            quat.copy(lastQuaternion);
        } else {
            console.error("No quaternion data has ever been received.");
            if (pitchEl && yawEl && rollEl) {
                pitchEl.value = "—";
                yawEl.value = "—";
                rollEl.value = "—";
            }
            return;
        }

        // Compute rotated body-frame basis vectors 
        const basisX = new THREE.Vector3(1, 0, 0).applyQuaternion(quat);
        const basisY = new THREE.Vector3(0, 1, 0).applyQuaternion(quat);
        const basisZ = new THREE.Vector3(0, 0, 1).applyQuaternion(quat);

        // Build rotation matrix and set it on the rocket
        const rotationMatrix = new THREE.Matrix4().makeBasis(basisX, basisY, basisZ);
        rocket.setRotationFromMatrix(rotationMatrix);

        // Update Euler angles for HUD
        euler.setFromQuaternion(quat, 'XYZ');
        const pitch = THREE.MathUtils.radToDeg(euler.x);
        const yaw   = THREE.MathUtils.radToDeg(euler.y);
        const roll  = THREE.MathUtils.radToDeg(euler.z);

        if (pitchEl && yawEl && rollEl) {
            pitchEl.value = pitch.toFixed(1);
            yawEl.value   = yaw.toFixed(1);
            rollEl.value  = roll.toFixed(1);
        }

        renderScene();
    }

    window.rocketUpdate = rocketUpdate;
});
