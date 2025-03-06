<script lang="ts">
    import Modal from "$lib/components/Modal.svelte";
    import * as THREE from "three";
    import {
        generalWaypoints,
        addWaypointbyName,
        clearGeneralWaypoints,
        futurePosition,
        getWaypoint,
        generateWaypointDefault,
        currentTargetPosition,
    } from "$lib/coordinate";
    let showModal = false;
    let tempWaypointName = "";
    $: {
        const waypoint = getWaypoint(tempWaypointName)?.position;
        if (waypoint) {
            futurePosition.set(
                new THREE.Vector3(waypoint.x, waypoint.y, waypoint.z),
            );
        }
    }
    let stepSize = 0.001;
</script>

<button
    on:click={() => (showModal = true)}
    class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
    >Select Waypoint</button
>

<Modal bind:showModal>
    <h2 slot="header">Tray</h2>
    <p>target {JSON.stringify($futurePosition)}</p>

    <div class="p-4 bg-gray-100 grid grid-cols-5">
        <input
            type="text"
            bind:value={tempWaypointName}
            class="border rounded p-2 text-black"
            placeholder="Waypoint Name"
        />
        <button
            on:click={() => addWaypointbyName(tempWaypointName)}
            class="bg-blue-500 text-white px-4 py-2 rounded ml-2"
        >
            Add Waypoint
        </button>
        <button
            on:click={clearGeneralWaypoints}
            class="bg-red-500 text-white px-4 py-2 rounded ml-2"
        >
            Clear Waypoints
        </button>
        <!-- svelte-ignore a11y-label-has-associated-control -->
        <label class="block mb-2">Select Waypoint:</label>
        <select
            bind:value={tempWaypointName}
            class="border rounded p-2 text-black"
        >
            {#each $generalWaypoints as waypoint (waypoint.name)}
                <option value={waypoint.name}>{waypoint.name}</option>
            {/each}
        </select>
    </div>
</Modal>
