<script>
  import { onMount } from "svelte";
  import * as THREE from "three";
  import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
  import ObjectControl from "$lib/ObjectControl";
  let canvas;
  let scene, camera, renderer, orbitControls;
  let objectControl;
  // Box dims
  let boxWidth = 1;
  let boxHeight = 1;
  let boxDepth = 1;
  onMount(() => {
    // 1) Your existing Scene, Camera, Renderer
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(
      75,
      canvas.clientWidth / canvas.clientHeight,
      0.1,
      1000
    );
    camera.position.set(0, 5, 10);
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    // 2) Create your orbit controls
    orbitControls = new OrbitControls(camera, renderer.domElement);
    orbitControls.enableDamping = true;
    // 3) Optionally add lights, floor, etc.
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(10, 10, 10);
    scene.add(directionalLight);
    // 4) Initialize our ObjectControl module with references
    objectControl = new ObjectControl({
      scene,
      camera,
      renderer,
      orbitControls,
      domElement: renderer.domElement,
    });
    // 5) Kick off your own render loop (the module does not do it)
    animate();
  });
  // Example manual animation loop
  function animate() {
    requestAnimationFrame(animate);
    orbitControls.update();
    renderer.render(scene, camera);
  }
  // Hook up UI to the module
  function addBox() {
    objectControl?.addBox(boxWidth, boxHeight, boxDepth);
  }
  function setTransformMode(mode) {
    objectControl?.setTransformMode(mode);
  }
 </script>
 <div class="overlay">
 <label>
    Box Width
 <input type="number" bind:value={boxWidth} step="0.1" />
 </label>
 <label>
    Box Height
 <input type="number" bind:value={boxHeight} step="0.1" />
 </label>
 <label>
    Box Depth
 <input type="number" bind:value={boxDepth} step="0.1" />
 </label>
 <button on:click={addBox}>Add Box</button>
 <hr />
 <button on:click={() => setTransformMode("translate")}>Move</button>
 <button on:click={() => setTransformMode("rotate")}>Rotate</button>
 <button on:click={() => setTransformMode("scale")}>Scale</button>
 </div>
 <canvas bind:this={canvas}></canvas>
 <style>
  :global(html, body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
  }
  .overlay {
    position: absolute;
    top: 1rem;
    left: 1rem;
    background: rgba(255, 255, 255, 0.8);
    padding: 1rem;
    border-radius: 4px;
    z-index: 10;
  }
  .overlay label,
  .overlay input {
    display: block;
  }
  .overlay button {
    margin-top: 0.5rem;
    margin-right: 0.5rem;
  }
  canvas {
    display: block;
    width: 100vw;
    height: 100vh;
  }
 </style>
 
 