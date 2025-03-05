<script lang="ts">
    import { setTranslationSpeed, max_rotation_speed, max_translation_speed, setRotationalSpeed } from "$lib/robotics/laraapi";
    import { robotJoints } from "$lib/coordinate";
    import {  radToDeg } from "three/src/math/MathUtils.js";
    import * as THREE from "three";
    import { onMount } from "svelte";
    
    import socketIOClient from 'socket.io-client';
    let socket: any;
    export function setupSocket() {
    socket = socketIOClient("http://192.168.2.13:8081");

     
    socket.on("connect", async () => {
        console.log(`Connected with socket ID: ${socket.id}`);
        console.log("Connected and emitted events.");
    });

    socket.on("heartbeat_check", () => {
        socket.emit("heartbeat_response", true);
    });

    //Cartesian_Pose
    socket.on("Cartesian_Pose", (data: any) => {
        robotJoints.update((joints) => {
            const x = parseFloat(data.X);
            const y = parseFloat(data.Y);
            const z = parseFloat(data.Z);
            const a = parseFloat(data.A);
            const b = parseFloat(data.B);
            const c = parseFloat(data.C);
            const _x = parseFloat(data._X);
            const _y = parseFloat(data._Y);
            const _z = parseFloat(data._Z);
            const _w = parseFloat(data._W);
            if (!isNaN(x)) joints.x = x;
            if (!isNaN(y)) joints.y = y;
            if (!isNaN(z)) joints.z = z;
            if (!isNaN(a)) joints.a = a;
            if (!isNaN(b)) joints.b = b;
            if (!isNaN(c)) joints.c = c;
            if (!isNaN(_x)) joints._x = _x;
            if (!isNaN(_y)) joints._y = _y;
            if (!isNaN(_z)) joints._z = _z;
            if (!isNaN(_w)) joints._w = _w;
            

            return joints;
        });
    });
    //Joint_Angle
    socket.on("Joint_Angle", (data: any) => {
        robotJoints.update((joints) => {
            const joint1 = parseFloat(data.A1);
            const joint2 = parseFloat(data.A2);
            const joint3 = parseFloat(data.A3);
            const joint4 = parseFloat(data.A4);
            const joint5 = parseFloat(data.A5);
            const joint6 = parseFloat(data.A6);
            if (!isNaN(joint1) && joint1 !== undefined) joints.joint1 = joint1;
            if (!isNaN(joint2) && joint2 !== undefined) joints.joint2 = joint2;
            if (!isNaN(joint3) && joint3 !== undefined) joints.joint3 = joint3;
            if (!isNaN(joint4) && joint4 !== undefined) joints.joint4 = joint4;
            if (!isNaN(joint5) && joint5 !== undefined) joints.joint5 = joint5;
            if (!isNaN(joint6) && joint6 !== undefined) joints.joint6 = joint6;
            return joints;
        });
    });

    socket.on("connect_error", (err: { message: any }) => {
        console.error(`Connection error due to ${err.message}`);
    });

    socket.on("disconnect", (reason: any) => {
        console.log(`Disconnected: ${reason}`);
    });

    socket.on("error", (error: any) => {
        console.error("Socket error:", error);
    });
}

export function setCollisionStatus(enable: boolean) {
    const status = enable ? "on" : "off";
    socket.emit("gui_collision_status", {
        gui_collision: status,
    });
}

export function startMovementSlider(q0: any, q1: any, q2: any, q3: any, q4: any, q5: any) {
    // console.log("startMovementSlider", q0, q1, q2, q3, q4, q5);
    let data = {
        q0: q0,
        q1: q1,
        q2: q2,
        q3: q3,
        q4: q4,
        q5: q5,
        status: true,
        joint: false,
        cartesian: true,
        freedrive: false,
        button: false,
        slider: true,
        goto: false,
        threeD: false,
        reference: "Base",
        absrel: "Absolute",
    };
    socket.emit("CartesianSlider", data);
}

export function stopMovementSlider(q0: any, q1: any, q2: any, q3: any, q4: any, q5: any) {
    let data = {
        q0: q0,
        q1: q1,
        q2: q2,
        q3: q3,
        q4: q4,
        q5: q5,
        status: false,
        joint: false,
        cartesian: true,
        freedrive: false,
        button: false,
        slider: true,
        goto: false,
        threeD: false,
        reference: "Base",
        absrel: "Absolute",
    };
    socket.emit("CartesianSlider", data);
}



    onMount(() => {
        setupSocket();
    });

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
        moveInterval = setInterval(() => move(axis, direction), 50);
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