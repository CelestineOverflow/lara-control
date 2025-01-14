<script>
  import { onMount } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/addons/controls/OrbitControls.js";
  let canvas;
  let scene;
  let camera;
  let renderer;
  let cubes = [];
  let controls;
  function generateCubes(poses) {
    // Remove existing cubes
    cubes.forEach((cube) => scene.remove(cube));
    cubes = [];
    // Add new cubes
    poses.forEach((pose) => {
      const geometry = new THREE.BoxGeometry();
      const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
      const mesh = new THREE.Mesh(geometry, material);
      // Set rotation
      if (pose.quat) {
        const q = new THREE.Quaternion(pose.quat[0], pose.quat[1], pose.quat[2], pose.quat[3]);
        mesh.setRotationFromQuaternion(q);
      }
      // Set position
      if (pose.pos) {
        mesh.position.set(pose.pos[0], pose.pos[1], pose.pos[2]);
      }
      scene.add(mesh);
      cubes.push(mesh);
    });
  }
  function randomPoses() {
    return Array.from({ length: 5 }, () => ({
      quat: [
        Math.random() * 2 - 1,
        Math.random() * 2 - 1,
        Math.random() * 2 - 1,
        Math.random() * 2 - 1
      ],
      pos: [
        Math.random() * 10 - 5,
        Math.random() * 10 - 5,
        Math.random() * 10 - 5
      ]
    }));
  }
  function testFunction() {
    generateCubes(randomPoses());
  }
  onMount(() => {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    renderer = new THREE.WebGLRenderer({ canvas });
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.position.z = 5;
    scene.background = new THREE.Color(0x000000);
    //add light
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(0, 0, 1);
    scene.add(light);
    //add plane
    const planeGeometry = new THREE.PlaneGeometry(10, 10);
    const planeMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00, side: THREE.DoubleSide });
    const plane = new THREE.Mesh(planeGeometry, planeMaterial);
    plane.rotation.x = Math.PI / 2;
    scene.add(plane);
    //add orbit controls
    controls = new OrbitControls(camera, renderer.domElement);

    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();
  });
 </script>
 <canvas bind:this={canvas}></canvas>
 <button on:click={testFunction}>Generate Cubes</button>