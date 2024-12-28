<script lang="ts">
    import { onMount } from "svelte";
    import socketIOClient from 'socket.io-client';
    //very important  npm install socket.io-client@2 --save
    let isConnected = false;
    let A1 = 0;
    let A2 = 0;
    let A3 = 0;
    let A4 = 0;
    let A5 = 0;
    let A6 = 0;

    let socket: any;

    

    function setupSocket() {
        socket = socketIOClient("http://192.168.2.13:8081");

        socket.on("connect", () => {
            console.log(`Connected with socket ID: ${socket.id}`);
            isConnected = true;

            // Emitting initial events
            socket.emit("PowerStatus", { data: "CheckPower" });
            socket.emit("check_zerog_status", { data: "check_zerog" });
            socket.emit("isHmiButton", { hmi_button: false });
            socket.emit("SimulateReal", { data: false });
            console.log("Connected and emitted events.");
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

    function startMovement() {
        socket.emit("JointGotoManual", {
            q0: A1,
            q1: A2,
            q2: A3,
            q3: A4,
            q4: A5,
            q5: A6,
            status: true, // Start movement
            joint: true,
            cartesian: false,
            freedrive: false,
            button: false,
            slider: false,
            goto: true,
            threeD: false,
            reference: "nil",
            absrel: "Absolute",
        });
        console.log("Sent 'JointGotoManual' start event.");
    }

    function stopMovement() {
        socket.emit("JointGotoManual", {
            q0: A1,
            q1: A2,
            q2: A3,
            q3: A4,
            q4: A5,
            q5: A6,
            status: false, // Stop movement
            joint: false,
            cartesian: false,
            freedrive: false,
            button: false,
            slider: false,
            goto: false,
            threeD: false,
            reference: "nil",
            absrel: "Absolute",
        });
        console.log("Sent 'JointGotoManual' stop event.");
    }
</script>

<!-- svelte-ignore a11y-label-has-associated-control -->

<div class="p-6 max-w-md mx-auto bg-white rounded-xl shadow-md space-y-4">
    <h1 class="text-xl font-bold">Robot Arm Control</h1>
    <h1 class="text-xl font-bold">WS state: {isConnected}</h1>

    <button
        on:click={() => {
            setupSocket();
        }}
        class="bg-blue-500 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded w-full"
    >
        Connect
    </button>

    <div class="space-y-2">
        <div class="flex items-center">
            <label class="w-16">A1:</label>
            <input
                type="number"
                bind:value={A1}
                class="border rounded px-2 py-1 flex-1"
            />
        </div>
        <div class="flex items-center">
            <label class="w-16">A2:</label>
            <input
                type="number"
                bind:value={A2}
                class="border rounded px-2 py-1 flex-1"
            />
        </div>
        <div class="flex items-center">
            <label class="w-16">A3:</label>
            <input
                type="number"
                bind:value={A3}
                class="border rounded px-2 py-1 flex-1"
            />
        </div>
        <div class="flex items-center">
            <label class="w-16">A4:</label>
            <input
                type="number"
                bind:value={A4}
                class="border rounded px-2 py-1 flex-1"
            />
        </div>
        <div class="flex items-center">
            <label class="w-16">A5:</label>
            <input
                type="number"
                bind:value={A5}
                class="border rounded px-2 py-1 flex-1"
            />
        </div>
        <div class="flex items-center">
            <label class="w-16">A6:</label>
            <input
                type="number"
                bind:value={A6}
                class="border rounded px-2 py-1 flex-1"
            />
        </div>
    </div>

    <div>
        <button
            on:mousedown={startMovement}
            on:mouseup={stopMovement}
            on:mouseleave={stopMovement}
            class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded w-full"
        >
            Move Arm
        </button>
    </div>
</div>
