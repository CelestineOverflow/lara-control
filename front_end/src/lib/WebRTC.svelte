<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';

  export let srcUrl = 'http://192.168.2.209:5176/offer';
  export let width = 1920;
  export let height = 1080;

  const dispatch = createEventDispatcher();
  let videoEl;
  let pc;
  let statsInterval;
  
  // reactive bitrate (in kbps)
  let bitrate = 0;

  function updateStatus(status, error = '') {
    dispatch('statusChange', { status, error });
  }

  async function start() {
    updateStatus('connecting');
    pc = new RTCPeerConnection();

    pc.ontrack = e => {
      if (e.track.kind === 'video') {
        videoEl.srcObject = e.streams[0];
        updateStatus('connected');

        // once we have a stream, kick off our stats loop
        let lastBytes = 0;
        let lastTimestamp = 0;
        statsInterval = setInterval(async () => {
          const stats = await pc.getStats();
          stats.forEach(report => {
            if (report.type === 'inbound-rtp' && report.kind === 'video') {
              if (lastTimestamp) {
                const bytesNow = report.bytesReceived;
                const timeNow  = report.timestamp;
                const bitrateBps = (bytesNow - lastBytes) * 8 / ((timeNow - lastTimestamp) / 1000);
                bitrate = Math.round(bitrateBps / 1000); // to kbps
              }
              lastBytes = report.bytesReceived;
              lastTimestamp = report.timestamp;
            }
          });
        }, 1000);
      }
    };

    pc.oniceconnectionstatechange = () => {
      if (pc.iceConnectionState.match(/failed|disconnected|closed/)) {
        updateStatus('error', pc.iceConnectionState);
      }
    };

    try {
      const offer = await pc.createOffer({ offerToReceiveVideo: true });
      await pc.setLocalDescription(offer);

      const res = await fetch(srcUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sdp: pc.localDescription.sdp,
          type: pc.localDescription.type,
          resolution: { width, height }
        })
      });

      const answer = await res.json();
      await pc.setRemoteDescription(answer);
    } catch (err) {
      updateStatus('error', err.message);
    }
  }

  function stop() {
    if (statsInterval) clearInterval(statsInterval);
    if (pc) pc.close();
    if (videoEl) videoEl.srcObject = null;
    updateStatus('disconnected');
  }

  onMount(() => {
    start();
  });

  onDestroy(() => {
    stop();
  });
</script>

<style>
  .video-container {
    position: relative;
    width: /* you can constrain this if you want it smaller on screen */;
    height: /* same as above */;
  }
  .bitrate {
    position: absolute;
    top: 4px;
    left: 4px;
    font-size: 12px;
    line-height: 1;
    color: #0f0;
    background: rgba(0, 0, 0, 0.5);
    padding: 2px 4px;
    border-radius: 3px;
    pointer-events: none;
    font-family: monospace;
  }
  video {
    display: block;
    width: 100%;
    height: 100%;
  }
</style>

<div class="video-container" style="width: {width}px; height: {height}px;">
  <video
    bind:this={videoEl}
    autoplay
    playsinline
    muted
  />
  <div class="bitrate">
    {#if bitrate}
      {bitrate} kbps
    {:else}
      – kbps
    {/if}
  </div>
</div>
