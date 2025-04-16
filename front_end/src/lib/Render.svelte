<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/addons/controls/OrbitControls.js";
  import ObjectControl from "$lib/ObjectControl";
  import RobotData from "$lib/RobotData.svelte";
  import { robotScene } from "$lib/RobotScene.svelte";

  // Canvas and rendering properties
  let canvas: HTMLCanvasElement;
  let container: HTMLDivElement;
  let renderer: THREE.WebGLRenderer;
  let camera: THREE.PerspectiveCamera;
  let controls: OrbitControls;
  let controlsObject: ObjectControl;
  let animationId: number;
  let resizeObserver: ResizeObserver;

  // Let parent determine the sizing by default
  export let width = "100%";
  export let height = "100%";
  
  onMount(() => {
    robotScene.initRobotArm();

    // Initialize camera
    const updateCameraSize = () => {
      const containerWidth = container.clientWidth;
      const containerHeight = container.clientHeight;
      camera.aspect = containerWidth / containerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(containerWidth, containerHeight);
    };

    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.01, 1000);
    camera.position.set(1, 1, 1);

    // Initialize renderer
    renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true
    });
    renderer.setClearColor(0x000000, 0);
    renderer.autoClear = false;
    updateCameraSize();

    // Initialize controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.update();

    // Setup object control
    controlsObject = new ObjectControl({
      scene: robotScene.scene,
      camera,
      renderer,
      controls,
      domElement: renderer.domElement,
    });

    // Use ResizeObserver to detect parent size changes
    resizeObserver = new ResizeObserver(() => {
      updateCameraSize();
    });
    resizeObserver.observe(container);

    // Animation loop
    function animate() {
      animationId = requestAnimationFrame(animate);
      controls.update();
      robotScene.updateJoints();
      renderer.render(robotScene.scene, camera);
    }
    animate();
  });

  onDestroy(() => {
    if (animationId) cancelAnimationFrame(animationId);
    if (renderer) renderer.dispose();
    if (controls) controls.dispose();
    if (resizeObserver) resizeObserver.disconnect();
  });
</script>

<div
  bind:this={container}
  style="width: {width}; height: {height}; position: relative;">
  <canvas bind:this={canvas} style="display: block;"></canvas>
  
</div>
