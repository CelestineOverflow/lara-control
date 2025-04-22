<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as THREE from 'three';
	import { robotScene } from '$lib/RobotScene.svelte';
	import Render from './Render.svelte';
	import RobotData from './RobotData.svelte';
	let container: HTMLDivElement;
	let canvas_overlay: HTMLCanvasElement;
	let cameraFeed: HTMLImageElement;
	let canvas_overlay_renderer: THREE.WebGLRenderer;
	let animationId: number;
	export let cameraUrl = 'http://192.168.2.209:1692/my_camera';
	// Update renderer and camera based on container size
	function onResize() {
		if (!container) return;
		// const size = container.parentElement.getBoundingClientRect();;
		
		// const width = size.width;
		// //keep the aspect ratio of the camera feed
		// const height = width * 9 / 16;
		// container.style.width = `${width}px`;
		// container.style.height = `${height}px`;
		// if (canvas_overlay_renderer) {
		// 	canvas_overlay_renderer.setSize(width, height);
		// }
		// if (robotScene.laraArm && robotScene.laraArm.camera) {
		// 	robotScene.laraArm.camera.aspect = width / height;
		// 	robotScene.laraArm.camera.updateProjectionMatrix();
		// }
		// if (cameraFeed) {
		// 	cameraFeed.width = width;
		// 	cameraFeed.height = height;
		// }
		if (!cameraFeed) return;
		const width = container.clientWidth;
		const height = container.clientHeight;
		console.log('Container size:', width, height);
		console.log('Camera feed size:', cameraFeed.clientWidth, cameraFeed.clientHeight);
		if (canvas_overlay_renderer) {
			canvas_overlay_renderer.setSize(width, height);
		}
		if (robotScene.laraArm && robotScene.laraArm.camera) {
			robotScene.laraArm.camera.aspect = width / height;
			robotScene.laraArm.camera.updateProjectionMatrix();
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
		// Set initial size from the container
		onResize();
		// Update sizes on window resize
		window.addEventListener('resize', onResize);
		// Animation loop for rendering the overlay
		function animate() {
			onResize();
			animationId = requestAnimationFrame(animate);
			if (robotScene.laraArm && robotScene.laraArm.camera) {
				// Update the camera's aspect ratio based on the container
				const width = container.clientWidth;
				const height = container.clientHeight;
				robotScene.laraArm.camera.aspect = width / height;
				robotScene.laraArm.camera.updateProjectionMatrix();
				// Hide certain elements before rendering
				if (robotScene.arrowHelper) {
					robotScene.arrowHelper.visible = false;
				}
				if (robotScene.GeneralSceneGLB) {
					robotScene.GeneralSceneGLB.visible = false;
				}
				canvas_overlay_renderer.clear();
				canvas_overlay_renderer.render(robotScene.scene, robotScene.laraArm.camera);
				// Restore the elements' visibility
				if (robotScene.arrowHelper) {
					robotScene.arrowHelper.visible = true;
				}
				if (robotScene.GeneralSceneGLB) {
					robotScene.GeneralSceneGLB.visible = true;
				}
			}
		}
		animate();
		return () => {
			cancelAnimationFrame(animationId);
			window.removeEventListener('resize', onResize);
		};
	});
</script>

<div class="container" bind:this={container}>
	<!-- Camera feed: scales responsively -->
	<img
		bind:this={cameraFeed}
		src={cameraUrl}
		alt="Robot Camera Feed"
		class="full-size camera-feed"
	/>
	
	<!-- Overlay canvas: will match the camera feed dimensions -->
	<canvas bind:this={canvas_overlay} class="full-size" style="background: transparent;"></canvas>
  <div class="absolute left-0 top-0 z-10 m-2 w-1/3 h-1/3 aspect-square rounded-lg border border-white bg-transparent p-2">
    <Render />
  </div>

  <div style="position: absolute; top: 10px; right: 10px; color: white; z-index: 1;">
    <RobotData />
  </div>
  
</div>


<style>
	/* The container maintains a 16:9 aspect ratio */
	.container {
		position: relative;
		width: 100%;
		display: block;
		aspect-ratio: 16 / 9;
		background: black;
	}
	/* Fill the container */
	.full-size {
		position: absolute;
		width: 100%;
		height: 100%;
	}
</style>
