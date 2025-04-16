<script lang="ts">
	import {
		setTranslationSpeed,
		startMovementSlider,
		stopMovementSlider,
		setRotationalSpeed
	} from '$lib/robotics/laraapi';
	import { robotJoints } from '$lib/robotics/coordinate.svelte';
	import { radToDeg } from 'three/src/math/MathUtils.js';
	import { onMount, onDestroy } from 'svelte';
	import * as THREE from 'three';

	let moveInterval: any = null;
	// Toggle to move along the robot’s local (actuator’s) axes
	let moveAlongNormal: boolean = false;
	/**
	 * Moves the robot. For x and y moves, the z component after rotation is zeroed,
	 * but for a z move the full local transformation is applied.
	 */
	function move(axis: 'x' | 'y' | 'z' | 'a' | 'b' | 'c', direction: 1 | -1) {
		let movementVector = [0, 0, 0]; // [dx, dy, dz]
		let newA = 0,
			newB = 0,
			newC = 0;
		// Set base movement vector
		switch (axis) {
			case 'x':
				movementVector[0] += direction;
				break;
			case 'y':
				movementVector[1] += direction;
				break;
			case 'z':
				// For Z we always want to use the actuator’s local POV.
				movementVector[2] += direction;
				break;
			case 'a':
				newA += direction;
				break;
			case 'b':
				newB += direction;
				break;
			case 'c':
				newC += direction;
				break;
		}
		if (moveAlongNormal) {
			// Retrieve the robot’s quaternion
			let quat = new THREE.Quaternion(
				$robotJoints._x,
				$robotJoints._y,
				$robotJoints._z,
				$robotJoints._w
			);
			// Create a quaternion for the 180° offset around the x‑axis.
			let offsetQuat = new THREE.Quaternion();
			offsetQuat.setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI);
			// Remove the offset by pre‑multiplying with the inverse.
			quat.premultiply(offsetQuat.invert());
			// Build a rotation matrix from the corrected quaternion.
			let rotationMatrix = new THREE.Matrix4();
			rotationMatrix.makeRotationFromQuaternion(quat);
			// Extract a 3x3 matrix (for vector rotation).
			let rotationMatrix3x3 = [
				[rotationMatrix.elements[0], rotationMatrix.elements[1], rotationMatrix.elements[2]],
				[rotationMatrix.elements[4], rotationMatrix.elements[5], rotationMatrix.elements[6]],
				[rotationMatrix.elements[8], rotationMatrix.elements[9], rotationMatrix.elements[10]]
			];
			// Rotate the movement vector using the corrected matrix.
			let rotatedMovementVector = multiplyMatrixAndVector(rotationMatrix3x3, movementVector);
			movementVector = rotatedMovementVector;
		}
		// Execute the movement using the (possibly rotated) movement vector.
		startMovementSlider(movementVector[0], movementVector[1], movementVector[2], newA, newB, newC);
	}
	function startMoving(axis: 'x' | 'y' | 'z' | 'a' | 'b' | 'c', direction: 1 | -1) {
		if (moveInterval === null) {
			move(axis, direction);
			moveInterval = setInterval(() => move(axis, direction), 10);
		}
	}
	function stopMoving() {
		if (moveInterval !== null) {
			clearInterval(moveInterval);
			moveInterval = null;
			stopMovementSlider(0, 0, 0, 0, 0, 0);
		}
	}
	// Helper: multiply a 3x3 matrix with a 3-element vector.
	function multiplyMatrixAndVector(matrix: number[][], vector: number[]): number[] {
		let result: number[] = [];
		for (let i = 0; i < matrix.length; i++) {
			let sum = 0;
			for (let j = 0; j < vector.length; j++) {
				sum += matrix[i][j] * vector[j];
			}
			result[i] = sum;
		}
		return result;
	}
	let rotational_speed = 1.0;
	let linear_speed = 1.0;

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
				} else if (type === 'rotation') {
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
		stopMoving();
		currentAnimation = null;
		cube.position.copy(originalPosition);
		cube.rotation.copy(originalRotation);
	}

	onDestroy(() => {
		if (animationId) {
			cancelAnimationFrame(animationId);
		}
	});

	let translationMode = true;
</script>

<button
	class="justify-center rounded bg-orange-500 p-4 text-sm text-white hover:bg-orange-600"
	on:click={() => (moveAlongNormal = !moveAlongNormal)}
>
	<span>{moveAlongNormal ? 'Disable' : 'Enable'} Move Along Normal</span>
</button>

<div class="robot-visualization">
	<!-- Three.js container -->
	<div class="threejs-container" bind:this={container}></div>

	<!-- Control interface -->

	<div class="control-preview">
		<div class="grid-container">
			<!-- Translation Controls -->

			<label class="fieldset-label">
				<input type="checkbox" class="toggle toggle-primary" bind:checked={translationMode} />
				{#if translationMode}
					<span class="label-text">Translation</span>
				{:else}
					<span class="label-text">Rotation</span>
				{/if}
			</label>

			{#if translationMode}
    <input type="range" min="1.0" max="25.0" step="0.5" class="range range-primary range-xs" bind:value={linear_speed} on:change={() => setTranslationSpeed(linear_speed)} />
      <p> Speed: {linear_speed} mm/s</p>
				<div class="controls-section">
					<h3>Translation</h3>
					<div class="controls-grid">
						<button
							on:mouseenter={() => startTranslationAnimation('z', 1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('z', 1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('z', 1)}
							on:touchend={stopMoving}
						>
							Z+
						</button>
						<button
							on:mouseenter={() => startTranslationAnimation('y', 1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('y', 1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('y', 1)}
							on:touchend={stopMoving}
						>
							Y+
						</button>
						<button
							on:mouseenter={() => startTranslationAnimation('x', 1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('x', 1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('x', 1)}
							on:touchend={stopMoving}
						>
							X+
						</button>
						<button
							on:mouseenter={() => startTranslationAnimation('z', -1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('z', -1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('z', -1)}
							on:touchend={stopMoving}
						>
							Z-
						</button>
						<button
							on:mouseenter={() => startTranslationAnimation('y', -1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('y', -1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('y', -1)}
							on:touchend={stopMoving}
						>
							Y-
						</button>
						<button
							on:mouseenter={() => startTranslationAnimation('x', -1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('x', -1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('x', -1)}
							on:touchend={stopMoving}
						>
							X-
						</button>
					</div>
				</div>
			{:else}
				<!-- Rotation Controls -->
        <input type="range" min="1.0" max="15.0" step="0.5" class="range range-secondary range-xs" bind:value={rotational_speed} on:change={() => setRotationalSpeed(rotational_speed)} />
        <p> Speed: {rotational_speed } °/s</p>
				<div class="controls-section">
					<h3>Rotation</h3>
					<div class="controls-grid">
						<button
							on:mouseenter={() => startRotationAnimation('c', 1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('c', 1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('c', 1)}
							on:touchend={stopMoving}
						>
							Rz+
						</button>
						<button
							on:mouseenter={() => startRotationAnimation('b', 1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('b', 1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('b', 1)}
							on:touchend={stopMoving}
						>
							Ry+
						</button>
						<button
							on:mouseenter={() => startRotationAnimation('a', 1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('a', 1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('a', 1)}
							on:touchend={stopMoving}
						>
							Rx+
						</button>
						<button
							on:mouseenter={() => startRotationAnimation('c', -1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('c', -1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('c', -1)}
							on:touchend={stopMoving}
						>
							Rz-
						</button>
						<button
							on:mouseenter={() => startRotationAnimation('b', -1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('b', -1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('b', -1)}
							on:touchend={stopMoving}
						>
							Ry-
						</button>
						<button
							on:mouseenter={() => startRotationAnimation('a', -1)}
							on:mouseleave={stopAnimation}
							on:mousedown={() => startMoving('a', -1)}
							on:mouseup={stopMoving}
							on:touchstart={() => startMoving('a', -1)}
							on:touchend={stopMoving}
						>
							Rx-
						</button>
					</div>
				</div>
			{/if}
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
