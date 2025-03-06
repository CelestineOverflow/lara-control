<script>
// @ts-nocheck

    import Webrtc from "$lib/Webrtc.svelte";
    import { onMount } from "svelte";
    let toggle = false;
    let stream;

    // Function to get user media
    async function getUserMedia() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        } catch (err) {
            console.error("Error accessing media devices.", err);
        }
    }

    // Call the function to get user media when the component is mounted
    onMount(() => {
        getUserMedia();
    });
</script>

<button on:click={()=>{toggle=true}}>opencv</button>
{#if toggle}
<Webrtc {stream} />
{/if}

