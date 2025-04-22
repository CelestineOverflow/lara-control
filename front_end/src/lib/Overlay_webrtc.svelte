<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as THREE from 'three';
	import { robotScene } from '$lib/RobotScene.svelte';
	import Render from './Render.svelte';
	import RobotData from './RobotData.svelte';
	import WebRtc from './WebRTC.svelte';
	let container: HTMLDivElement;
	let canvas_overlay: HTMLCanvasElement;
	let canvas_overlay_renderer: THREE.WebGLRenderer;
    let videoHeight;
    let videoWidth;
	let animationId: number;
	// Update renderer and camera based on container size
	function onResize() {
		if (!container) return;
		const size = container.getBoundingClientRect();;
		const width = size.width;
		const height = width * 9 / 16;
		if (canvas_overlay_renderer) {
			canvas_overlay_renderer.setSize(width, height);
		}
        videoHeight = height;
        videoWidth = width;
	}
	onMount(() => {
		// Initialize WebGL renderer for overlay
		canvas_overlay_renderer = new THREE.WebGLRenderer({
			canvas: canvas_overlay,
			alpha: true
		});
		canvas_overlay_renderer.setClearColor(0x000000, 0);
		canvas_overlay_renderer.autoClear = false;
		// Animation loop for rendering the overlay
		function animate() {
			onResize();
			animationId = requestAnimationFrame(animate);
			if (robotScene.laraArm && robotScene.laraArm.camera) {
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
		};
	});
    
</script>

<div style="position: relative; width: 100%; height: 100%;" bind:this={container}>
	<!-- WebRtc on the bottom layer -->
	<WebRtc bind:videoHeight bind:videoWidth />

	<!-- Canvas overlay on top -->
	<canvas
		bind:this={canvas_overlay}
		class="border-2 border-solid"
		style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: transparent; z-index: 1;"
	></canvas>
	<div style="position: absolute; top: 10px; left: 10px; color: white; z-index: 10;" class="w-1/4 h-1/5 aspect-square rounded-lg border border-white bg-transparent p-2">
		<Render />
	</div>
	<div style="position: absolute; top: 10px; right: 10px; color: white; z-index: 10;">
		<RobotData />
	</div>
</div>
