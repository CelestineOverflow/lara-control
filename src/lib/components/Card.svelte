<script lang="ts">
    export let title = "No title";
    let toggle = true;

    import { createEventDispatcher } from "svelte";
    const dispatch = createEventDispatcher();

    function handleToggle() {
        toggle = !toggle;
        dispatch("toggle", { visible: toggle });
    }
</script>

<div class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4 text-gray-800">
    <h1 class="text-2xl font-bold mb-4">{title}</h1>
    <button
        on:click={handleToggle}
        class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
    >
        {toggle ? "Hide" : "Show"}
    </button>
    {#if toggle}
        <slot></slot>
    {/if}
</div>
