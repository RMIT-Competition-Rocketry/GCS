/**
 * GCS Rocket Viewer
 * 
 * Uses three.js to animate a 6DOF 3D model of the rocket
 * 
 * Functions and constants should be prefixed with "rocket_" 
 */

import * as THREE from "./libraries/three.module.js";
import { GLTFLoader } from "./libraries/GLTFLoader.js";

let rocket = null;
let quat = new THREE.Quaternion();
let lastQuaternion = new THREE.Quaternion();
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
    camera.position.set(0, 0, 20); // Move back far enough for a full view
    camera.lookAt(0, 0, 0);


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

    const envTextureLoader = new THREE.CubeTextureLoader();
    const origin = new THREE.Vector3(3, -3.75, 0);
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

            /*
            // Body-frame axis arrows
            xArrow = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), origin, 2, 0xff0000);
            yArrow = new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), origin, 2, 0x00ff00);
            zArrow = new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), origin, 2, 0x0000ff);
            
            scene.add(xArrow, yArrow, zArrow);
            */

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
        const aspect = container.clientWidth / container.clientHeight;
        camera.left = -aspect * viewSize / 2;
        camera.right = aspect * viewSize / 2;
        camera.top = viewSize / 2;
        camera.bottom = -viewSize / 2;
        camera.updateProjectionMatrix();

    }

    window.addEventListener("resize", onResize);

    function rocketUpdate(data) {
        if (!rocket || !data) return;

        if (
            typeof data.qw === "number" && !isNaN(data.qw) &&
            typeof data.qx === "number" && !isNaN(data.qx) &&
            typeof data.qy === "number" && !isNaN(data.qy) &&
            typeof data.qz === "number" && !isNaN(data.qz)
        ) {
            quat.set(data.qx, data.qy, data.qz, data.qw).normalize();
            lastQuaternion.copy(quat);
            hasReceivedQuaternion = true;
        } else if (hasReceivedQuaternion) {
            quat.copy(lastQuaternion);
        } else {
            return;
        }

        // No correction needed: assuming rocket points +Y already
        rocket.setRotationFromQuaternion(quat);

        // Update body-frame axes based on raw quaternion
        const bodyX = new THREE.Vector3(1, 0, 0).applyQuaternion(quat);
        const bodyY = new THREE.Vector3(0, 1, 0).applyQuaternion(quat);
        const bodyZ = new THREE.Vector3(0, 0, 1).applyQuaternion(quat);

        const rocketPosition = new THREE.Vector3();
        rocket.getWorldPosition(rocketPosition);

        /*
        xArrow.position.copy(origin);
        xArrow.setDirection(bodyX);

        yArrow.position.copy(origin);
        yArrow.setDirection(bodyY);

        zArrow.position.copy(origin);
        zArrow.setDirection(bodyZ);
        */

        // Euler angles for HUD
        euler.setFromQuaternion(quat, 'XYZ');
        displaySetValue("rocket-pitch", THREE.MathUtils.radToDeg(euler.x), 1);
        displaySetValue("rocket-yaw", THREE.MathUtils.radToDeg(euler.y), 1);
        displaySetValue("rocket-roll", THREE.MathUtils.radToDeg(euler.z), 1);
    }

    window.rocketUpdate = rocketUpdate;
});