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
  
    export let width = "100%";
    export let height = "800px";
    
    onMount(() => {
      // Initialize the robot arm in browser context
      robotScene.initRobotArm();
      
      // Initialize camera
      const containerWidth = container.clientWidth;
      const containerHeight = container.clientHeight;
      camera = new THREE.PerspectiveCamera(75, containerWidth / containerHeight, 0.01, 1000);
      camera.position.set(1, 1, 1);
  
      // Initialize renderer
      renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
      renderer.setSize(containerWidth, containerHeight);
      
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
  
      // Handle canvas resize
      function handleCanvasResize() {
        const width = container.clientWidth;
        const height = container.clientHeight;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
      }
  
      // Animation loop
      function animate() {
        animationId = requestAnimationFrame(animate);
        
        // Resize handling
        handleCanvasResize();
        
        // Update controls
        controls.update();
        
        // Update robot joints
        robotScene.updateJoints();
        
        // Render the scene
        renderer.render(robotScene.scene, camera);
      }
      
      // Start animation loop
      animate();
    });
  
    onDestroy(() => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      
      // Clean up resources
      if (renderer) {
        renderer.dispose();
      }
      
      if (controls) {
        controls.dispose();
      }
    });
  </script>
  
  <div bind:this={container} style="width: {width}; height: {height}; position: relative;">
    <canvas bind:this={canvas} style="display: block;"></canvas>
    <div style="position: absolute; top: 10px; right: 10px; color: white; z-index: 1;">
      <RobotData />
    </div>
  </div>