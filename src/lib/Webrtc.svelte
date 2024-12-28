<script lang="ts">
    import { onMount } from 'svelte';
    import { createEventDispatcher } from 'svelte';

    const pc = new RTCPeerConnection();
    let video: HTMLVideoElement;
    export let stream: MediaStream; // Accept the stream as a prop

    const dispatch = createEventDispatcher();

    onMount(async () => {
        if (stream) {
            await start_stream(stream);
        } else {
            console.error("No stream provided!");
        }
    });

    async function start_stream(mediaStream: MediaStream) {
        // Add tracks from the provided media stream to the WebRTC connection
        mediaStream.getTracks().forEach(track => pc.addTrack(track, mediaStream));

        // Display the stream in the video element (optional, for local preview)
        if (video) {
            video.srcObject = mediaStream;
        }

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const response = await fetch('http://localhost:1446/offer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sdp: pc.localDescription?.sdp || '',
                type: pc.localDescription?.type || '',
            }),
        });

        const answer = await response.json();
        await pc.setRemoteDescription(answer);

        // Dispatch an event if needed (e.g., connection success/failure)
        dispatch('connected', { pc });
    }
</script>

<!-- svelte-ignore a11y-media-has-caption -->
<video bind:this={video} autoplay playsinline muted style="display: none;"></video>