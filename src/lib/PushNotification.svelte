<script lang="ts">
    export let showModal : boolean; // show modal
    $: if (showModal) {
        setTimeout(() => {
            showModal = false;
        }, 10000); // auto-hide notification after 3 seconds
    }
</script>

<!-- Notification -->
{#if showModal}
<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div class="notification" on:click={() => showModal = false}>
    <slot/>
    <button class="text-sm float-right bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-1 px-2 border border-gray-400 rounded shadow" on:click={() => showModal = false}>Close</button>
</div>
{/if}

<style>
    .notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        max-width: 20em;
        padding: 1em;
        background-color: #f0f0f0;
        border: 1px solid #ccc;
        border-radius: 0.2em;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        animation: slide-in 0.3s ease-out;
        z-index: 1000;
        cursor: pointer;
    }
    .notification p {
        margin: 0;
    }

    @keyframes slide-in {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slide-out {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }

    .notification[hidden] {
        animation: slide-out 0.3s ease-in;
    }
</style>