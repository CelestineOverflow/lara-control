<script lang="ts">
    import { isPaused } from "./coordinate";
    import { setPause } from "./robotics/laraapi";

    let modes = ["Teach", "Automatic", "SemiAutomatic"];
    let selectedMode = 0;
    async function setMode() {
        const response = await fetch(`http://localhost:1442/changeMode?mode=${modes[selectedMode]}`, {
            method: "POST",
            headers: {
                Accept: "application/json",
            },
        }).then(
            (response) => {
                if (response.ok) {
                    console.log("Mode changed successfully");
                } else {
                    alert("Failed to change mode");
                }
            },
            (error) => {
                alert("Failed to change mode");
            }
        );
    }
    async function init() {
        const response = await fetch(`http://localhost:1442/init`, {
            method: "GET",
            headers: {
                Accept: "application/json",
            },
        }).then(
            (response) => {
                if (response.ok) {
                    console.log("Initiated successfully");
                } else {
                    alert("Failed to initiate");
                }
            },
            (error) => {
                alert("Failed to initiate");
            }
        );
        
    }


</script>
<div>
    <p class="text-2xl font-bold">API</p>
    <button
    class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
    on:click={init}
    >

    Init
    </button>
    
    <div class="relative inline-block w-64">
    <select
        class="block appearance-none w-full bg-white border border-gray-400 hover:border-gray-500 px-4 py-2 pr-8 rounded shadow leading-tight focus:outline-none focus:shadow-outline text-black"
        bind:value={selectedMode}
        on:change={setMode}
    >
        {#each modes as mode, index}
            <option value={index}>{mode}</option>
        {/each}
    </select>
    <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
        <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
            <path d="M7 10l5 5 5-5H7z" />
        </svg>
    </div>
    </div>
    <button
    class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
    on:click={()=>setPause()}
    >

    {#if $isPaused}
        Resume
    {:else}
        Pause
    {/if}
    </button>
</div>

