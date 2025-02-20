<script lang="ts">
    import { setTranslationSpeed, startMovementSlider, stopMovementSlider, max_rotation_speed, max_translation_speed, setRotationalSpeed } from "./robotics/laraapi";
    import {  robotJoints } from "./coordinate";
    import {  radToDeg } from "three/src/math/MathUtils.js";
    import * as THREE from "three";
    let moveInterval: any = null;
    // Toggle to move along the robot’s local (actuator’s) axes
    let moveAlongNormal: boolean = false;
    /**
     * Moves the robot. For x and y moves, the z component after rotation is zeroed,
     * but for a z move the full local transformation is applied.
     */
    function move(
      axis: "x" | "y" | "z" | "a" | "b" | "c",
      direction: 1 | -1
    ) {
      let movementVector = [0, 0, 0]; // [dx, dy, dz]
      let newA = 0, newB = 0, newC = 0;
      // Set base movement vector
      switch (axis) {
        case "x":
          movementVector[0] += direction;
          break;
        case "y":
          movementVector[1] += direction;
          break;
        case "z":
          // For Z we always want to use the actuator’s local POV.
          movementVector[2] += direction;
          break;
        case "a":
          newA += direction;
          break;
        case "b":
          newB += direction;
          break;
        case "c":
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
      startMovementSlider(
        movementVector[0],
        movementVector[1],
        movementVector[2],
        newA,
        newB,
        newC
      );
    }
    function startMoving(
      axis: "x" | "y" | "z" | "a" | "b" | "c",
      direction: 1 | -1
    ) {
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
    let rotational_speed = 0.0;
    function setRotSpeed(arg0: number): void {
      rotational_speed = (arg0 / 1000) * max_rotation_speed;
      setRotationalSpeed(rotational_speed);
    }
    let linear_speed = 0.01;
    function setTransSpeed(arg0: number): void {
      linear_speed = (arg0 / 1000) * max_translation_speed;
      setTranslationSpeed(linear_speed);
    }
   </script>
   <!-- HTML Interface -->
   <button
    class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
    on:click={() => (moveAlongNormal = !moveAlongNormal)}>
   <span>{moveAlongNormal ? "Disable" : "Enable"} Move Along Normal</span>
   </button>
   <div class="grid grid-cols-2 gap-3 bg-indigo-600 bg-opacity-20 rounded">
   <h3 class="col-span-3">Translation (X, Y, Z) Speed: {linear_speed * 1000} mm/s</h3>
   <input
      type="range"
      min="0.1"
      max="100"
      step="0.1"
      on:input={e => setTransSpeed(parseFloat(e.target.value))}
      class="slider"
    />
   </div>
   <div class="grid grid-cols-3 gap-3 bg-indigo-600 bg-opacity-20 rounded">
   <!-- Z+ Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("z", 1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("z", 1)}
      on:touchend={stopMoving}>
      Z+
   </button>
   <!-- Y+ Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("y", 1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("y", 1)}
      on:touchend={stopMoving}>
      Y+
   </button>
   <!-- X+ Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("x", 1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("x", 1)}
      on:touchend={stopMoving}>
      X+
   </button>
   <!-- Z- Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("z", -1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("z", -1)}
      on:touchend={stopMoving}>
      Z-
   </button>
   <!-- Y- Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("y", -1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("y", -1)}
      on:touchend={stopMoving}>
      Y-
   </button>
   <!-- X- Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("x", -1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("x", -1)}
      on:touchend={stopMoving}>
      X-
   </button>
   </div>
   <div class="grid grid-cols-2 gap-3 bg-indigo-600 bg-opacity-20 rounded">
   <h3 class="col-span-3">Rotation (Rx, Ry, Rz) Speed: {radToDeg(rotational_speed).toFixed(2)}°/s</h3>
   <input
      type="range"
      min="0"
      max="1000"
      step="1"
      on:input={e => setRotSpeed(parseInt(e.target.value))}
      class="slider"
    />
   </div>
   <div class="grid grid-cols-3 gap-3 bg-indigo-600 bg-opacity-20 rounded">
   <!-- Rz+ Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("c", 1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("c", 1)}
      on:touchend={stopMoving}>
      Rz+
   </button>
   <!-- Ry+ Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("b", 1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("b", 1)}
      on:touchend={stopMoving}>
      Ry+
   </button>
   <!-- Rx+ Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("a", 1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("a", 1)}
      on:touchend={stopMoving}>
      Rx+
   </button>
   <!-- Rz- Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("c", -1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("c", -1)}
      on:touchend={stopMoving}>
      Rz-
   </button>
   <!-- Ry- Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("b", -1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("b", -1)}
      on:touchend={stopMoving}>
      Ry-
   </button>
   <!-- Rx- Button -->
   <button
      class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
      on:mousedown={() => startMoving("a", -1)}
      on:mouseup={stopMoving}
      on:mouseleave={stopMoving}
      on:touchstart={() => startMoving("a", -1)}
      on:touchend={stopMoving}>
      Rx-
   </button>
   </div>