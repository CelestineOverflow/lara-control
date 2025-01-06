<script lang="ts">
    let states: string[] = ["normal", "square_detector", "tag_detector"];
    let cameras: number[] = [0, 1];
    let current_state: string = "normal";
    let current_camera: number = 0;

    async function set_state(state: string): Promise<void> {
        try {
            const response = await fetch(`http://localhost:1447/set_state/${state}`, {
                method: "POST",
                headers: {
                    "accept": "application/json",
                },
            });
            if (!response.ok) {
                console.error("Failed to set state");
            }
        } catch (error) {
            console.error("Error setting state", error);
        }
    }

    async function set_camera(index: number): Promise<void> {
        try {
            const response = await fetch(`http://localhost:1447/set_camera/${index}`, {
                method: "POST",
                headers: {
                    "accept": "application/json",
                },
            });
            if (!response.ok) {
                console.error("Failed to set camera");
            }
        } catch (error) {
            console.error("Error setting camera", error);
        }
    }

    async function get_state(): Promise<void> {
        try {
            const response = await fetch(`http://localhost:1447/get_state`, {
                method: "GET",
                headers: {
                    "accept": "application/json",
                },
            });
            if (response.ok) {
                const data = await response.json();
                current_state = data.state;
                current_camera = data.camera;
            } else {
                console.error("Failed to get state");
            }
        } catch (error) {
            console.error("Error fetching state", error);
        }
    }
</script>

<div class="p-4 space-y-4">
    <div class="space-y-2">
        <h2 class="text-lg font-bold">Select State</h2>
        <div class="flex flex-wrap gap-2">
            {#each states as state}
                <button
                    class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:ring focus:ring-blue-300"
                    on:click={() => set_state(state)}>
                    {state}
                </button>
            {/each}
        </div>
    </div>

    <div class="space-y-2">
        <h2 class="text-lg font-bold">Select Camera</h2>
        <div class="flex flex-wrap gap-2">
            {#each cameras as camera}
                <button
                    class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 focus:ring focus:ring-gray-300"
                    on:click={() => set_camera(camera)}>
                    Camera {camera}
                </button>
            {/each}
        </div>
    </div>

    <div>
        <h2 class="text-lg font-bold">Current State</h2>
        <p class="p-2 bg-gray-100 rounded">State: {current_state}</p>
        <p class="p-2 bg-gray-100 rounded">Camera: {current_camera}</p>
        <button 
            class="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 focus:ring focus:ring-green-300"
            on:click={get_state}>
            Refresh State
        </button>
    </div>
</div>