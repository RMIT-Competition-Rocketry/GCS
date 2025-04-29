import * as THREE from "https://cdn.skypack.dev/three@0.129.0/build/three.module.js";
import { GLTFLoader } from "https://cdn.skypack.dev/three@0.129.0/examples/jsm/loaders/GLTFLoader.js";

let rocket = null;
let rocketPitch = 0;
let rocketRoll = 0;
let rocketYaw = 0;
const deltaTime = 0.2; // 5 packets per second

// === LIVE ORIENTATION UPDATER ===
function rocketUpdate(data) {
  if (!rocket || !data) return;

  const gx = data.gyroX || 0;
  const gy = data.gyroY || 0;
  const gz = data.gyroZ || 0;

  // DEAD RECKONING: 
  rocketPitch += gx * deltaTime;
  rocketRoll  += gy * deltaTime;
  rocketYaw   += gz * deltaTime;

  // Apply to rocket rotation 
  rocket.rotation.x = THREE.MathUtils.degToRad(rocketPitch);  // pitch
  rocket.rotation.z = THREE.MathUtils.degToRad(rocketRoll);   // roll
  rocket.rotation.y = THREE.MathUtils.degToRad(rocketYaw) + Math.PI / 2;  // yaw + correction

  // Live HUD update
  const pitchEl = document.getElementById("pitchDisplay");
  const yawEl   = document.getElementById("yawDisplay");
  const rollEl  = document.getElementById("rollDisplay");

  if (pitchEl && yawEl && rollEl) {
    pitchEl.textContent = `Pitch: ${rocketPitch.toFixed(1)}°`;
    yawEl.textContent   = `Yaw:   ${rocketYaw.toFixed(1)}°`;
    rollEl.textContent  = `Roll:  ${rocketRoll.toFixed(1)}°`;
  }
}

window.rocketUpdate = rocketUpdate; 

// === MAIN VIEWER INITIALISATION ===
window.addEventListener("DOMContentLoaded", () => {
  console.log("Loaded rocket_viewer.js");

  const container = document.getElementById("rocketViewerContainer");
  const canvas = document.getElementById("rocketCanvas");

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.shadowMap.enabled = true;

  const scene = new THREE.Scene();
  scene.background = null;

  const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
  camera.position.set(0, 2, 8);

  // Lighting
  const lights = [
    new THREE.DirectionalLight(0xffffff, 12),
    new THREE.DirectionalLight(0xffffff, 8),
    new THREE.SpotLight(0xffffff, 12),
    new THREE.HemisphereLight(0xffffff, 0x333333, 2.5)
  ];
  lights[0].position.set(15, 30, 20).castShadow = true;
  lights[1].position.set(-15, 20, -10).castShadow = true;
  lights[2].position.set(0, 30, 25);
  lights[2].angle = Math.PI / 5;
  lights[2].penumbra = 0.4;
  lights[2].decay = 1;
  lights[2].distance = 200;
  lights[2].castShadow = true;
  lights[3].position.set(0, 50, 0);
  lights.forEach(light => scene.add(light));

  // reflection environment
  const envTextureLoader = new THREE.CubeTextureLoader();
  scene.environment = envTextureLoader.load([
    'https://threejs.org/examples/textures/cube/Bridge2/posx.jpg',
    'https://threejs.org/examples/textures/cube/Bridge2/negx.jpg',
    'https://threejs.org/examples/textures/cube/Bridge2/posy.jpg',
    'https://threejs.org/examples/textures/cube/Bridge2/negy.jpg',
    'https://threejs.org/examples/textures/cube/Bridge2/posz.jpg',
    'https://threejs.org/examples/textures/cube/Bridge2/negz.jpg',
  ]);

  // Load rocket model
  new GLTFLoader().load('/static/models/rocket_model.glb',
    gltf => {
      rocket = gltf.scene;
      rocket.rotation.y = Math.PI / 2;
      rocket.scale.set(2, 2, 2);

      scene.add(rocket);

      const box = new THREE.Box3().setFromObject(rocket);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3()).length();

      camera.position.copy(center);
      camera.position.z += size * 1.3;
      camera.lookAt(center);
    },
    xhr => console.log(`🔄 Loading: ${(xhr.loaded / xhr.total * 100).toFixed(1)}%`),
    err => console.error(" Error loading model:", err)
  );

  function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener("resize", () => {
    renderer.setSize(container.clientWidth, container.clientHeight);
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
  });
});
