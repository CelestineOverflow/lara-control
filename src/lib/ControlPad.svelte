<script lang="ts">
    import GeneralPosition from "$lib/GeneralPosition.svelte";
    import Tray from "$lib/Tray.svelte";
    let distance_travel: number = 0.0001;
    let rotation_factor: number = 0.0001; // Set a different factor for rotation
    import * as THREE from "three";
    import {
        futurePosition,
        futureRotation,
        AprilTagInView,
        AprilTagRelativePosition,
    } from "./coordinate"

    let moveInterval: any = null;
    let rotateInterval: any = null;
    let last_known_position : any = null;

    function sigmoid(t: number): number {
        // Simple sigmoid function for smooth transitions
        return 1 / (1 + Math.exp(-t));
    }

    function interpolatePoints(start: THREE.Vector3, end: THREE.Vector3, t: number): THREE.Vector3 {
        // Applying the sigmoid function for smooth interpolation
        const factor = sigmoid((t - 0.5) * 10); // Adjust the multiplier to control steepness
        return new THREE.Vector3(
            start.x + (end.x - start.x) * factor,
            start.y + (end.y - start.y) * factor,
            start.z + (end.z - start.z) * factor
        );
    }

    async function smoothTransition(start: THREE.Vector3, end: THREE.Vector3, duration: number) {
        const startTime = performance.now();
        return new Promise<void>((resolve) => {
            function animate() {
                const elapsed = performance.now() - startTime;
                const t = Math.min(elapsed / duration, 1);
                const interpolated = interpolatePoints(start, end, t);
                
                futurePosition.update((position) => {
                    position.copy(interpolated);
                    return position;
                });

                if (t < 1) {
                    requestAnimationFrame(animate);
                } else {
                    resolve();
                }
            }

            animate();
        });
    }
    let safeYHeight = 0.3;
    async function moveTowardsTag() {
    if ($AprilTagInView) {
        // If the tag is in view, move towards it based on its relative position.
        const moveInterval = setInterval(() => {
            let reach_y = false;
            futurePosition.update((position) => {
                position.x -= $AprilTagRelativePosition.x * 0.01;
                position.z -= $AprilTagRelativePosition.z * 0.01;
                if ($AprilTagRelativePosition.y > 1.0) {
                    position.y -= $AprilTagRelativePosition.y * 0.0001;
                } else {
                    reach_y = true;
                }
                return position;
            });

            // Stop when close enough
            if (
                Math.abs($AprilTagRelativePosition.x) < 0.01 &&
                Math.abs($AprilTagRelativePosition.z) < 0.01 &&
                reach_y
            ) {
                clearInterval(moveInterval);
                last_known_position = $futurePosition.clone(); // Update last known position
            }
        }, 50);
    } else {
        // If the tag is not in view, go to the last known position + offset.
        let start = $futurePosition.clone();
        let end = new THREE.Vector3($futurePosition.x, safeYHeight, $futurePosition.z);
        await smoothTransition(start, end, 2000);
        futurePosition.update((position) => {
            position.x = last_known_position.x;
            position.y = safeYHeight; // You can adjust this based on your scenario
            position.z = last_known_position.z;
            return position;
        });
        start = end.clone();
        end = new THREE.Vector3(last_known_position.x, safeYHeight, last_known_position.z);
        await smoothTransition(start, end, 2000);
        futurePosition.update((position) => {
            position.x = last_known_position.x;
            position.y = safeYHeight; // You can adjust this based on your scenario
            position.z = last_known_position.z;
            return position;
        });

        // Wait for a second and retry detection
        setTimeout(() => {
            if ($AprilTagInView) {
                console.log("Tag found, resuming movement");
                moveTowardsTag(); // Try to move towards the tag again
            } else {
                console.log("Tag not found, retrying...");
            }
        }, 1000);
    }
}


    function move(axis: "x" | "y" | "z", direction: 1 | -1) {
        futurePosition.update((position) => {
            // console.log(position)
            position[axis] += distance_travel * direction;
            return position;
        });
    }

    function rotate(axis: "x" | "y" | "z", direction: 1 | -1) {
        futureRotation.update((rotation) => {
            rotation[axis] += direction * rotation_factor;
            return rotation;
        });
    }

    function startMoving(axis: "x" | "y" | "z", direction: 1 | -1) {
        if (moveInterval === null) {
            moveInterval = setInterval(() => move(axis, direction), 10); // Adjust the interval time as needed
        }
    }

    function stopMoving() {
        if (moveInterval !== null) {
            clearInterval(moveInterval);
            moveInterval = null;
        }
    }

    function startRotating(axis: "x" | "y" | "z", direction: 1 | -1) {
        if (rotateInterval === null) {
            rotateInterval = setInterval(() => rotate(axis, direction), 50); // Adjust interval time for rotation as well
        }
    }

    function stopRotating() {
        if (rotateInterval !== null) {
            clearInterval(rotateInterval);
            rotateInterval = null;
        }
    }

</script>

<div class="grid grid-cols-3 gap-3 bg-indigo-600 bg-opacity-20 rounded">
    <!-- Translation Controls -->
    <h3 class="col-span-3">Translation (X, Y, Z)</h3>
    <button
        class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
        on:mousedown={() => startMoving("z", 1)}
        on:mouseup={stopMoving}
        on:mouseleave={stopMoving}>Z+</button
    >
    <button
        class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
        on:mousedown={() => startMoving("y", 1)}
        on:mouseup={stopMoving}
        on:mouseleave={stopMoving}>Y+</button
    >
    <button
        class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
        on:mousedown={() => startMoving("x", 1)}
        on:mouseup={stopMoving}
        on:mouseleave={stopMoving}>X+</button
    >

    <button
        class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
        on:mousedown={() => startMoving("z", -1)}
        on:mouseup={stopMoving}
        on:mouseleave={stopMoving}>Z-</button
    >
    <button
        class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
        on:mousedown={() => startMoving("y", -1)}
        on:mouseup={stopMoving}
        on:mouseleave={stopMoving}>Y-</button
    >
    <button
        class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
        on:mousedown={() => startMoving("x", -1)}
        on:mouseup={stopMoving}
        on:mouseleave={stopMoving}>X-</button
    >

    <!-- Rotation Controls -->
    <h3 class="col-span-3">Rotation (Y, X, Z)</h3>
    <button
        class="p-4 bg-blue-500 text-white rounded justify-center text-sm hover:bg-blue-600"
        on:mousedown={() => startRotating("z", 1)}
        on:mouseup={stopRotating}
        on:mouseleave={stopRotating}>Z +</button
    >
    <button
        class="p-4 bg-blue-500 text-white rounded justify-center text-sm hover:bg-blue-600"
        on:mousedown={() => startRotating("x", 1)}
        on:mouseup={stopRotating}
        on:mouseleave={stopRotating}>X +</button
    >
    <button
        class="p-4 bg-blue-500 text-white rounded justify-center text-sm hover:bg-blue-600"
        on:mousedown={() => startRotating("y", 1)}
        on:mouseup={stopRotating}
        on:mouseleave={stopRotating}>Y +</button
    >

    <button
        class="p-4 bg-blue-500 text-white rounded justify-center text-sm hover:bg-blue-600"
        on:mousedown={() => startRotating("z", -1)}
        on:mouseup={stopRotating}
        on:mouseleave={stopRotating}>Z -</button
    >
    <button
        class="p-4 bg-blue-500 text-white rounded justify-center text-sm hover:bg-blue-600"
        on:mousedown={() => startRotating("x", -1)}
        on:mouseup={stopRotating}
        on:mouseleave={stopRotating}>X -</button
    >
    <button
        class="p-4 bg-blue-500 text-white rounded justify-center text-sm hover:bg-blue-600"
        on:mousedown={() => startRotating("y", -1)}
        on:mouseup={stopRotating}
        on:mouseleave={stopRotating}>Y -</button
    >
    <button
        class="p-4 bg-blue-500 text-white rounded justify-center text-sm hover:bg-blue-600"
        on:click={moveTowardsTag}>Move Towards Tag</button
    >
</div>

<Tray />
<GeneralPosition />
