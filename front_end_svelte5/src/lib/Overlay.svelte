<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import * as THREE from "three";
    import { robotScene, customFOV } from "$lib/RobotScene.svelte";
    
    // DOM elements
    let canvas_overlay: HTMLCanvasElement;
    let cameraFeed: HTMLImageElement;
    
    // Renderer
    let canvas_overlay_renderer: THREE.WebGLRenderer;
    let animationId: number;
    
    export let cameraUrl = "http://192.168.2.209:1692/my_camera";
    export let width = "1280px";
    export let height = "720px";
    
    function handleResize() {
      if (!cameraFeed) return;
      
      const rect = cameraFeed.getBoundingClientRect();
      const rectWidth = rect.width;
      const rectHeight = rect.height;
      
      if (robotScene.laraArm && robotScene.laraArm.camera) {
        // Update camera aspect ratio
        robotScene.laraArm.camera.aspect = rectWidth / rectHeight;
        // Set FOV from the store
        robotScene.laraArm.camera.fov = $customFOV;
        robotScene.laraArm.camera.updateProjectionMatrix();
        
        // Resize renderer
        canvas_overlay_renderer.setSize(rectWidth, rectHeight);
      }
    }
    
    onMount(() => {
      // Initialize WebGL renderer for overlay
      canvas_overlay_renderer = new THREE.WebGLRenderer({
        canvas: canvas_overlay,
        alpha: true
      });
      
      canvas_overlay_renderer.setClearColor(0x000000, 0);
      canvas_overlay_renderer.autoClear = false;
      
      // Initial size (will be updated in resize handler)
      const initialWidth = parseInt(width);
      const initialHeight = parseInt(height);
      canvas_overlay_renderer.setSize(initialWidth, initialHeight);
      
      // Animation loop for overlay
      function animate() {
        animationId = requestAnimationFrame(animate);
        
        // Only render if the robot camera is available
        if (robotScene.laraArm && robotScene.laraArm.camera) {
          // Handle visibility before rendering
          if (robotScene.arrowHelper) {
            robotScene.arrowHelper.visible = false;
          }
          
          if (robotScene.GeneralSceneGLB) {
            robotScene.GeneralSceneGLB.visible = false;
          }
          
          // Render the scene from robot camera perspective
          canvas_overlay_renderer.clear();
          canvas_overlay_renderer.render(robotScene.scene, robotScene.laraArm.camera);
          
          // Restore visibility
          if (robotScene.arrowHelper) {
            robotScene.arrowHelper.visible = true;
          }
          
          if (robotScene.GeneralSceneGLB) {
            robotScene.GeneralSceneGLB.visible = true;
          }
        }
      }
      
      animate();
      
      // Add resize event listeners
    //   window.addEventListener('resize', handleResize);
    });
    
    
  </script>
  
  <div style="position: relative; width: {width}; height: {height};">
    <!-- Camera feed -->
    <img
      bind:this={cameraFeed}
      src={cameraUrl}
      alt="Robot Camera Feed"
      style="width: 100%; height: 100%; position: absolute; top: 0; left: 0;"
      on:load={handleResize}
    />
    
    <!-- Overlay canvas -->
    <canvas
      bind:this={canvas_overlay}
      style="position: absolute; top: 0; left: 0; background: transparent; width: 100%; height: 100%;"
    ></canvas>
  </div>