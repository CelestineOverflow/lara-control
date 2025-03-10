<script>
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';

  // Create a container for the 3D visualization
  let container;
  let scene, camera, renderer, cube;
  let animationId = null;
  let currentAnimation = null;
  let originalPosition = new THREE.Vector3(0, 0, 0);
  let originalRotation = new THREE.Euler(0, 0, 0);
  
  // Animation settings
  const ANIMATION_DISTANCE = 0.5;
  const ANIMATION_ROTATION = Math.PI / 4; // 45 degrees in radians
  const ANIMATION_DURATION = 1000; // ms
  const ANIMATION_SPEED = 0.01;

  // Initialize Three.js scene
  onMount(() => {
    initScene();
    animate();
    
    // Clean up on component unmount
    return () => {
      cancelAnimationFrame(animationId);
      if (renderer) {
        renderer.dispose();
      }
    };
  });
  
  function initScene() {
    // Create scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    
    // Create camera with 45 degree perspective view
    camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
    camera.position.set(2, 2, 2);
    camera.lookAt(0, 0, 0);
    
    // Create renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(200, 200); // Small viewbox
    container.appendChild(renderer.domElement);
    
    // Add grid for reference
    const gridHelper = new THREE.GridHelper(3, 10);
    scene.add(gridHelper);
    
    // Add axes helper
    const axesHelper = new THREE.AxesHelper(1.5);
    scene.add(axesHelper);
    
    // Create cube
    const geometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
    const material = new THREE.MeshStandardMaterial({ 
      color: 0x3080ff,
      roughness: 0.4,
      metalness: 0.3
    });
    cube = new THREE.Mesh(geometry, material);
    scene.add(cube);
    
    // Add lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 2, 3);
    scene.add(directionalLight);
    
    // Store original position and rotation
    originalPosition.copy(cube.position);
    originalRotation.copy(cube.rotation);
  }
  
  function animate() {
    animationId = requestAnimationFrame(animate);
    
    // Handle animations if active
    if (currentAnimation) {
      const { type, axis, direction, startTime, duration } = currentAnimation;
      const elapsedTime = performance.now() - startTime;
      const progress = Math.min(elapsedTime / duration, 1);
      
      // Reset to original position/rotation
      if (progress >= 1) {
        if (type === 'translation') {
          cube.position.copy(originalPosition);
        } else if (type === 'rotation') {
          cube.rotation.copy(originalRotation);
        }
        // Restart the animation
        currentAnimation.startTime = performance.now();
      } else {
        // Apply animation
        if (type === 'translation') {
          const moveVector = new THREE.Vector3();
          if (axis === 'x') moveVector.set(direction, 0, 0);
          else if (axis === 'y') moveVector.set(0, direction, 0);
          else if (axis === 'z') moveVector.set(0, 0, direction);
          
          // Sine wave motion for smooth back-and-forth
          const offset = Math.sin(progress * Math.PI) * ANIMATION_DISTANCE;
          cube.position.copy(originalPosition).addScaledVector(moveVector, offset);
        } 
        else if (type === 'rotation') {
          cube.rotation.copy(originalRotation);
          
          // Sine wave rotation for smooth back-and-forth
          const rotationOffset = Math.sin(progress * Math.PI) * ANIMATION_ROTATION;
          if (axis === 'a') cube.rotation.x += rotationOffset * direction;
          else if (axis === 'b') cube.rotation.y += rotationOffset * direction;
          else if (axis === 'c') cube.rotation.z += rotationOffset * direction;
        }
      }
    }
    
    renderer.render(scene, camera);
  }
  
  // Functions to start animation on hover
  function startTranslationAnimation(axis, direction) {
    currentAnimation = {
      type: 'translation',
      axis,
      direction,
      startTime: performance.now(),
      duration: ANIMATION_DURATION
    };
  }
  
  function startRotationAnimation(axis, direction) {
    currentAnimation = {
      type: 'rotation',
      axis,
      direction,
      startTime: performance.now(),
      duration: ANIMATION_DURATION
    };
  }
  
  function stopAnimation() {
    currentAnimation = null;
    cube.position.copy(originalPosition);
    cube.rotation.copy(originalRotation);
  }

  onDestroy(() => {
    if (animationId) {
      cancelAnimationFrame(animationId);
    }
  });
</script>

<div class="robot-visualization">
  <!-- Three.js container -->
  <div class="threejs-container" bind:this={container}></div>
  
  <!-- Control interface -->
  <div class="control-preview">
    <div class="grid-container">
      <!-- Translation Controls -->
      <div class="controls-section">
        <h3>Translation</h3>
        <div class="controls-grid">
          <button
            on:mouseenter={() => startTranslationAnimation('z', 1)}
            on:mouseleave={stopAnimation}>
            Z+
          </button>
          <button
            on:mouseenter={() => startTranslationAnimation('y', 1)}
            on:mouseleave={stopAnimation}>
            Y+
          </button>
          <button
            on:mouseenter={() => startTranslationAnimation('x', 1)}
            on:mouseleave={stopAnimation}>
            X+
          </button>
          <button
            on:mouseenter={() => startTranslationAnimation('z', -1)}
            on:mouseleave={stopAnimation}>
            Z-
          </button>
          <button
            on:mouseenter={() => startTranslationAnimation('y', -1)}
            on:mouseleave={stopAnimation}>
            Y-
          </button>
          <button
            on:mouseenter={() => startTranslationAnimation('x', -1)}
            on:mouseleave={stopAnimation}>
            X-
          </button>
        </div>
      </div>
      
      <!-- Rotation Controls -->
      <div class="controls-section">
        <h3>Rotation</h3>
        <div class="controls-grid">
          <button
            on:mouseenter={() => startRotationAnimation('c', 1)}
            on:mouseleave={stopAnimation}>
            Rz+
          </button>
          <button
            on:mouseenter={() => startRotationAnimation('b', 1)}
            on:mouseleave={stopAnimation}>
            Ry+
          </button>
          <button
            on:mouseenter={() => startRotationAnimation('a', 1)}
            on:mouseleave={stopAnimation}>
            Rx+
          </button>
          <button
            on:mouseenter={() => startRotationAnimation('c', -1)}
            on:mouseleave={stopAnimation}>
            Rz-
          </button>
          <button
            on:mouseenter={() => startRotationAnimation('b', -1)}
            on:mouseleave={stopAnimation}>
            Ry-
          </button>
          <button
            on:mouseenter={() => startRotationAnimation('a', -1)}
            on:mouseleave={stopAnimation}>
            Rx-
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .robot-visualization {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  
  .threejs-container {
    width: 200px;
    height: 200px;
    border: 1px solid #ccc;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .control-preview {
    width: 100%;
    max-width: 300px;
  }
  
  .grid-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .controls-section {
    background-color: rgba(99, 102, 241, 0.1);
    border-radius: 4px;
    padding: 0.5rem;
  }
  
  .controls-section h3 {
    margin: 0 0 0.5rem 0;
    font-size: 14px;
  }
  
  .controls-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
  }
  
  button {
    background-color: rgb(249, 115, 22);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 12px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  button:hover {
    background-color: rgb(234, 88, 12);
  }
</style>