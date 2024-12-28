<script lang="ts">
    import { setTranslationSpeed, setupSocket, startMovementSlider, stopMovementSlider, max_rotation_speed, max_translation_speed, setRotationalSpeed } from "./robotics/laraapi";
    import { onMount } from "svelte";
    import { loadcell_value, robotJoints } from "./coordinate";
    import { radToDeg } from "three/src/math/MathUtils.js";
    onMount(() => {
        // Connect to the robot API
        setupSocket();
    });
    let moveInterval: any = null;
    let moveAlongNormal: boolean = false; // Toggle for moving along robot's local axes

    //
    async function move_until_pressure(value :  number){
        const loadcell_current_value = $loadcell_value;

        let movementVector = [0, 0, 0]; // [dx, dy, dz]

        if (loadcell_current_value < value){
            movementVector[2] += 1;
        }else{
            movementVector[2] -= 1;
        }

        // Get the robot's current orientation angles (in radians)
        let a = $robotJoints.a;
        let b = $robotJoints.b;
        let c = $robotJoints.c;
        let rotationMatrix = eulerToRotationMatrix(a, b, c);
        // Rotate the movement vector
        movementVector = multiplyMatrixAndVector(rotationMatrix, movementVector);

        startMovementSlider(
            movementVector[0],
            movementVector[1],
            movementVector[2],
            0,
            0,
            0
        );
        //wait 50 ms 
        await new Promise(r => setTimeout(r, 50));
        console.log("Pressure: ", $loadcell_value);
        stopMovementSlider(0, 0, 0, 0, 0, 0);
    }


    function move(axis: "x" | "y" | "z" | "a" | "b" | "c", direction: 1 | -1) {
        let movementVector = [0, 0, 0]; // [dx, dy, dz]
        let newA = 0;
        let newB = 0;
        let newC = 0;
        switch (axis) {
            case "x":
                movementVector[0] +=  direction;
                break;
            case "y":
                movementVector[1] +=  direction;
                break;
            case "z":
                movementVector[2] +=  direction;
                break;
            case "a":
                newA +=  direction;
                break;
            case "b":
                newB +=  direction;
                break;
            case "c":
                newC +=  direction;
                break;
        }
        // If moveAlongNormal is true, rotate the movement vector based on the robot's orientation
        if (moveAlongNormal) {
            // Get the robot's current orientation angles (in radians)
            let a = $robotJoints.a;
            let b = $robotJoints.b;
            let c = $robotJoints.c;
            let rotationMatrix = eulerToRotationMatrix(a, b, c);
            // Rotate the movement vector
            movementVector = multiplyMatrixAndVector(rotationMatrix, movementVector);

            //
            let debugVector = multiplyMatrixAndVector(rotationMatrix, [0, 0, 1]);
            //to deg
            console.log("Debug A: ", a * 180 / Math.PI);
            console.log("Debug B: ", b * 180 / Math.PI);
            console.log("Debug C: ", c * 180 / Math.PI);
            console.log("Debug Vector: ", debugVector);
            
        }
        // Use the adjusted movement vector
        startMovementSlider(
            movementVector[0],
            movementVector[1],
            movementVector[2],
            newA,
            newB,
            newC
        );
    }
    function startMoving(axis: "x" | "y" | "z" | "a" | "b" | "c", direction: 1 | -1) {
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
    // Function to compute rotation matrix from Euler angles (Z-Y-X convention)
    function eulerToRotationMatrix(a: number, b: number, c: number): number[][] {
        let cosA = Math.cos(a),
            sinA = Math.sin(a);
        let cosB = Math.cos(b),
            sinB = Math.sin(b);
        let cosC = Math.cos(c),
            sinC = Math.sin(c);
        // Rotation matrices around X, Y, Z axes
        let Rx = [
            [1, 0, 0],
            [0, cosA, -sinA],
            [0, sinA, cosA],
        ];
        let Ry = [
            [cosB, 0, sinB],
            [0, 1, 0],
            [-sinB, 0, cosB],
        ];
        let Rz = [
            [cosC, -sinC, 0],
            [sinC, cosC, 0],
            [0, 0, 1],
        ];
        // Combined rotation matrix: R = Rz * Ry * Rx
        let Rzy = multiplyMatrices(Rz, Ry);
        let R = multiplyMatrices(Rzy, Rx);
        return R;
    }
    // Function to multiply two matrices
    function multiplyMatrices(a: number[][], b: number[][]): number[][] {
        let result: number[][] = [];
        for (let i = 0; i < a.length; i++) {
            result[i] = [];
            for (let j = 0; j < b[0].length; j++) {
                let sum = 0;
                for (let k = 0; k < b.length; k++) {
                    sum += a[i][k] * b[k][j];
                }
                result[i][j] = sum;
            }
        }
        return result;
    }
    // Function to multiply a matrix and a vector
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
    function setRotSpeed(arg0: number): any {
        //max 250mm/s
        rotational_speed = arg0 / 1000 * max_rotation_speed;
        setRotationalSpeed(rotational_speed);
    }
    let linear_speed = 0.0;

    function setTransSpeed(arg0: number){
        //max 250mm/s
        linear_speed = arg0 / 1000 * max_translation_speed;
        setTranslationSpeed(linear_speed);
    }
</script>

 <button
        class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
        on:click={() => (moveAlongNormal = !moveAlongNormal)}>
        <span>{moveAlongNormal ? "Disable" : "Enable"}</span
    > Toggle Move Along Normal
    </button>

    <div class="grid grid-cols-2 gap-3 bg-indigo-600 bg-opacity-20 rounded">
        <h3 class="col-span-3">Translation (X, Y, Z) Speed: {linear_speed * 1000} mm/s</h3>
        <input
            type="range"
            min="0"
            max="1000"
            step="1"
            on:input={e => setTransSpeed(parseInt(e.target.value))}
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

    <button
        class="p-4 bg-orange-500 text-white rounded justify-center text-sm hover:bg-orange-600"
        on:click={() => move_until_pressure(1000)}>
        Move until pressure
    </button>
</div>
