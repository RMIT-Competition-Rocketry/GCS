import * as THREE from "./three.module.js";
import { GLTFLoader } from "./GLTFLoader.js";

let rocket = null;
let quat = new THREE.Quaternion();
let lastQuaternion = new THREE.Quaternion(); // backup for packet loss
let euler = new THREE.Euler();

let hasReceivedQuaternion = false;

const deltaTime = 0.2;

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
            rocket = gltf.scene;
            rocket.rotation.y = Math.PI / 2;
            rocket.scale.set(2, 2, 2);

            scene.add(rocket);

            const box = new THREE.Box3().setFromObject(rocket);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3()).length();

            camera.position.copy(center);
            camera.position.z += size * 1.5;
            camera.lookAt(center);

            renderScene();
        },
        xhr => console.log(` Loading: ${((xhr.loaded / xhr.total) * 100).toFixed(1)}%`),
        err => console.error(" Error loading model:", err)
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

        const pitchEl = document.getElementById("pitchDisplay");
        const yawEl = document.getElementById("yawDisplay");
        const rollEl = document.getElementById("rollDisplay");

        if (
            data.qx !== undefined &&
            data.qy !== undefined &&
            data.qz !== undefined &&
            data.qw !== undefined
        ) {
            //  Valid quaternion received
            quat.set(data.qx, data.qy, data.qz, data.qw).normalize();
            lastQuaternion.copy(quat);
            hasReceivedQuaternion = true;
        } else if (hasReceivedQuaternion) {
            console.warn(" Quaternion packet missing. Reusing last known orientation.");
            quat.copy(lastQuaternion);
        } else {
            console.error(" No quaternion data has ever been received.");
            if (pitchEl && yawEl && rollEl) {
                pitchEl.textContent = "Pitch: — (no data)";
                yawEl.textContent = "Yaw:   — (no data)";
                rollEl.textContent = "Roll:  — (no data)";
            }
            return;
        }

        //  Apply rotation
        rocket.setRotationFromQuaternion(quat);

        //  Convert to Euler angles for HUD
        euler.setFromQuaternion(quat, 'XYZ');
        const pitch = THREE.MathUtils.radToDeg(euler.x);
        const yaw = THREE.MathUtils.radToDeg(euler.y);
        const roll = THREE.MathUtils.radToDeg(euler.z);

        if (pitchEl && yawEl && rollEl) {
            pitchEl.textContent = `Pitch: ${pitch.toFixed(1)}°`;
            yawEl.textContent   = `Yaw:   ${yaw.toFixed(1)}°`;
            rollEl.textContent  = `Roll:  ${roll.toFixed(1)}°`;
        }

        renderScene();
    }

    window.rocketUpdate = rocketUpdate;
});
