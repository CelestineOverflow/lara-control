<!-- WebRTCCamera.svelte -->
<script>
    import { onMount, onDestroy, createEventDispatcher } from 'svelte';
    
    // Event dispatcher
    const dispatch = createEventDispatcher();
    
    // Props
    export let serverUrl = 'http://localhost:8080'; // Default URL to your Python server
    export let autoStart = true; // Automatically start the video
    export let videoWidth = 1920; // Default video width
    export let videoHeight = 1080; // Default video height
    export let initialQuality = 'high'; // low, medium, high, fullhd, ultra, custom
    export let preferredCodec = 'auto'; // auto, h264, vp8, vp9
  
    // Reactive state
    let videoElement;
    let stream = null;
    let peerConnection = null;
    let connectionStatus = 'disconnected'; // disconnected, connecting, connected, error
    let errorMessage = '';
    let retryCount = 0;
    const MAX_RETRIES = 3;
    
    // Server response info
    let actualResolution = null;
    let activeCodec = 'unknown';
    let connectionStats = null;
    let statsInterval = null;
    
    // Quality settings
    let selectedQuality = initialQuality;
    let customBitrate = 10000; // kbps
    let customFrameRate = 30; // fps
    let showCustomControls = initialQuality === 'custom';
    let showAdvancedSettings = false;
    
    // Quality presets - Updated with higher bitrates
    const qualityPresets = {
      low: {
        width: 320,
        height: 240,
        frameRate: 15,
        bitrate: 500 // Increased from 250
      },
      medium: {
        width: 640,
        height: 480,
        frameRate: 25,
        bitrate: 2000 // Increased from 1000
      },
      high: {
        width: 1280,
        height: 720,
        frameRate: 30,
        bitrate: 5000 // Increased from 2500
      },
      fullhd: {
        width: 1920,
        height: 1080,
        frameRate: 30,
        bitrate: 10000 // Increased from 4000
      },
      ultra: {
        width: 1920,
        height: 1080,
        frameRate: 60,
        bitrate: 20000 // New ultra quality preset
      },
      custom: {
        width: videoWidth,
        height: videoHeight,
        frameRate: customFrameRate,
        bitrate: customBitrate
      }
    };
    
    // Advanced codec settings
    let codecSettings = {
      h264: {
        profile: 'high', // baseline, main, high
        level: '4.2',
        packetizationMode: 1,
        useTemporalLayers: true
      },
      vp8: {
        useTemporalLayers: true,
        denoise: true,
        errorResilient: true
      },
      general: {
        qualityVsSpeed: 'quality', // quality, balanced, speed
        forceTwoPass: true,
        adaptiveQuantization: true
      }
    };
    
    // Current quality settings (reactive)
    let currentQuality = { ...qualityPresets[selectedQuality] };
    
    // Update connection status and dispatch event
    function updateConnectionStatus(status, error = '') {
      connectionStatus = status;
      errorMessage = error;
      
      dispatch('statusChange', {
        status: connectionStatus,
        error: errorMessage
      });
    }
    
    // Update quality settings when selectedQuality changes
    $: {
      if (selectedQuality === 'custom') {
        showCustomControls = true;
        currentQuality = {
          width: videoWidth,
          height: videoHeight,
          frameRate: customFrameRate,
          bitrate: customBitrate
        };
      } else {
        showCustomControls = false;
        currentQuality = { ...qualityPresets[selectedQuality] };
        
        // Update displayed dimensions
        videoWidth = currentQuality.width;
        videoHeight = currentQuality.height;
        customFrameRate = currentQuality.frameRate;
      }
      
      console.log('Quality settings updated:', currentQuality);
    }
    
    // Store previous stats for calculating rates
    let previousStats = {
      framesDecoded: 0,
      bytesReceived: 0,
      timestamp: Date.now()
    };
    
    // Get connection statistics for troubleshooting
    async function getConnectionStats() {
      if (!peerConnection) return;
      
      const currentTime = Date.now();
      const timeElapsed = (currentTime - previousStats.timestamp) / 1000; // time in seconds
      
      try {
        const stats = await peerConnection.getStats();
        let inboundRtpStats = null;
        let videoReceiver = null;
        let codecStats = null;
        
        stats.forEach(stat => {
          if (stat.type === 'inbound-rtp' && stat.kind === 'video') {
            inboundRtpStats = stat;
          } else if (stat.type === 'codec' && stat.mimeType && stat.mimeType.toLowerCase().includes('video')) {
            codecStats = stat;
          }
        });
        
        if (inboundRtpStats && codecStats) {
          // Try to determine active codec
          if (codecStats.mimeType) {
            const codecMime = codecStats.mimeType.toLowerCase();
            if (codecMime.includes('h264')) {
              activeCodec = 'H.264';
            } else if (codecMime.includes('vp8')) {
              activeCodec = 'VP8';
            } else if (codecMime.includes('vp9')) {
              activeCodec = 'VP9';
            } else if (codecMime.includes('av1')) {
              activeCodec = 'AV1';
            } else {
              activeCodec = codecMime.split('/')[1];
            }
          }
          
          // Calculate frame rate from frames decoded since last check
          const framesDelta = inboundRtpStats.framesDecoded - previousStats.framesDecoded;
          const frameRate = timeElapsed > 0 ? Math.round(framesDelta / timeElapsed) : 0;
          
          // Calculate bitrate from bytes received since last check
          const bytesDelta = inboundRtpStats.bytesReceived - previousStats.bytesReceived;
          const kbps = timeElapsed > 0 ? Math.round((bytesDelta * 8) / timeElapsed / 1000) : 0;
          
          // Update connection stats
          connectionStats = {
            receivedFrames: inboundRtpStats.framesReceived,
            framesDecoded: inboundRtpStats.framesDecoded,
            framesDropped: inboundRtpStats.framesDropped,
            bytesReceived: inboundRtpStats.bytesReceived,
            packetsLost: inboundRtpStats.packetsLost,
            jitter: inboundRtpStats.jitter,
            actualBitrate: kbps,
            frameRate: frameRate,
            codec: activeCodec,
            timestamp: new Date().toLocaleTimeString()
          };
          
          // Update previous stats for next calculation
          previousStats = {
            framesDecoded: inboundRtpStats.framesDecoded,
            bytesReceived: inboundRtpStats.bytesReceived,
            timestamp: currentTime
          };
        }
      } catch (err) {
        console.error('Error getting connection stats:', err);
      }
    }
    
    // Start the connection to the WebRTC server
    async function startConnection() {
      try {
        updateConnectionStatus('connecting');
        
        // Create a new RTCPeerConnection
        peerConnection = new RTCPeerConnection({
          iceServers: [] // No STUN/TURN servers needed for local network
        });
        
        // When we get a remote stream, attach it to our video element
        peerConnection.ontrack = (event) => {
          if (videoElement && event.streams[0]) {
            videoElement.srcObject = event.streams[0];
            stream = event.streams[0];
            updateConnectionStatus('connected');
            
            // Start gathering stats
            if (statsInterval) clearInterval(statsInterval);
            // Initialize the previous stats before starting the interval
            previousStats = {
              framesDecoded: 0,
              bytesReceived: 0,
              timestamp: Date.now()
            };
            statsInterval = setInterval(getConnectionStats, 2000);
          }
        };
        
        // Set up event handlers for monitoring connection state
        peerConnection.oniceconnectionstatechange = () => {
          console.log('ICE connection state:', peerConnection.iceConnectionState);
          if (peerConnection.iceConnectionState === 'failed' || 
              peerConnection.iceConnectionState === 'disconnected' ||
              peerConnection.iceConnectionState === 'closed') {
            updateConnectionStatus('error', `ICE connection state: ${peerConnection.iceConnectionState}`);
            if (statsInterval) {
              clearInterval(statsInterval);
              statsInterval = null;
            }
          }
        };
        
        // Create an SDP offer with quality constraints
        const offerOptions = {
          offerToReceiveVideo: true,
          offerToReceiveAudio: false
        };
        
        // Create the initial offer
        const offer = await peerConnection.createOffer(offerOptions);
        
        // Get the current dimensions and bitrate to use
        const width = currentQuality.width;
        const height = currentQuality.height;
        const bitrate = currentQuality.bitrate;
        const frameRate = currentQuality.frameRate;
        
        console.log(`Requesting video: ${width}x${height} @ ${frameRate}fps, ${bitrate}kbps`);
        
        // Modify SDP to request specific quality
        let modifiedSdp = offer.sdp;
        
        // Modified approach to handle both VP8 and H.264
        const vp8Match = modifiedSdp.match(/a=rtpmap:(\d+) VP8\/90000/);
        const h264Match = modifiedSdp.match(/a=rtpmap:(\d+) H264\/90000/);
        const vp9Match = modifiedSdp.match(/a=rtpmap:(\d+) VP9\/90000/);
        
        // Reorder codecs if user has preference
        if (preferredCodec !== 'auto' && modifiedSdp.includes('m=video ')) {
          console.log(`Trying to prioritize ${preferredCodec} codec`);
          // This is a simplistic approach - codec reordering is complex and might not work in all browsers
          if (preferredCodec === 'h264' && h264Match) {
            const h264PayloadType = h264Match[1];
            // Try to move H264 to front of preference list
            const videoLine = modifiedSdp.match(/m=video \d+ UDP\/TLS\/RTP\/SAVPF ([\d ]+)/)[0];
            const payloadTypes = videoLine.split(' ').slice(3);
            const h264Index = payloadTypes.indexOf(h264PayloadType);
            if (h264Index > 0) {
              const reorderedPayloads = [h264PayloadType, ...payloadTypes.filter(pt => pt !== h264PayloadType)];
              const newVideoLine = `m=video ${videoLine.split(' ')[1]} UDP/TLS/RTP/SAVPF ${reorderedPayloads.join(' ')}`;
              modifiedSdp = modifiedSdp.replace(videoLine, newVideoLine);
            }
          } else if (preferredCodec === 'vp8' && vp8Match) {
            // Similar approach for VP8
            const vp8PayloadType = vp8Match[1];
            const videoLine = modifiedSdp.match(/m=video \d+ UDP\/TLS\/RTP\/SAVPF ([\d ]+)/)[0];
            const payloadTypes = videoLine.split(' ').slice(3);
            const vp8Index = payloadTypes.indexOf(vp8PayloadType);
            if (vp8Index > 0) {
              const reorderedPayloads = [vp8PayloadType, ...payloadTypes.filter(pt => pt !== vp8PayloadType)];
              const newVideoLine = `m=video ${videoLine.split(' ')[1]} UDP/TLS/RTP/SAVPF ${reorderedPayloads.join(' ')}`;
              modifiedSdp = modifiedSdp.replace(videoLine, newVideoLine);
            }
          }
        }
        
        // Configure VP8 if available
        if (vp8Match) {
          const vp8PayloadType = vp8Match[1];
          
          // 1. Add image attributes for resolution
          const imageAttr = `a=imageattr:${vp8PayloadType} recv [x=[1:${width}],y=[1:${height}]]`;
          
          // Find where to insert the image attribute (after the rtpmap line)
          const rtpmapRegex = new RegExp(`a=rtpmap:${vp8PayloadType} VP8\\/90000\\r\\n`);
          modifiedSdp = modifiedSdp.replace(rtpmapRegex, `$&${imageAttr}\\r\\n`);
          
          // 2. Add frame rate restriction
          const frameRateAttr = `a=framerate:${frameRate}.0`;
          modifiedSdp = modifiedSdp.replace(rtpmapRegex, `$&${frameRateAttr}\\r\\n`);
          
          // 3. Add VP8-specific settings via fmtp
          let vp8FmtpLine = `a=fmtp:${vp8PayloadType} `;
          let vp8Params = [];
          
          if (codecSettings.vp8.useTemporalLayers) {
            vp8Params.push("max-fr=" + frameRate);
            vp8Params.push("max-fs=" + Math.floor((width * height) / 256));
          }
          
          if (codecSettings.vp8.denoise) {
            vp8Params.push("denoise=1");
          }
          
          if (codecSettings.vp8.errorResilient) {
            vp8Params.push("error-resilient=1");
          }
          
          // Only add fmtp if we have parameters to set
          if (vp8Params.length > 0) {
            vp8FmtpLine += vp8Params.join(";");
            modifiedSdp = modifiedSdp.replace(rtpmapRegex, `$&${vp8FmtpLine}\\r\\n`);
          }
          
          // 4. Add bitrate constraint (b=AS is Application Specific bandwidth)
          const midRegex = /a=mid:0\r\n/g;
          if (modifiedSdp.match(midRegex)) {
            modifiedSdp = modifiedSdp.replace(midRegex, `a=mid:0\r\nb=AS:${bitrate}\r\nb=TIAS:${bitrate * 1000}\r\n`);
          }
        }
        
        // Configure H.264 if available
        if (h264Match) {
          const h264PayloadType = h264Match[1];
          
          // 1. Add image attributes for resolution
          const imageAttr = `a=imageattr:${h264PayloadType} recv [x=[1:${width}],y=[1:${height}]]`;
          
          // Find where to insert the image attribute
          const h264RtpmapRegex = new RegExp(`a=rtpmap:${h264PayloadType} H264\\/90000\\r\\n`);
          modifiedSdp = modifiedSdp.replace(h264RtpmapRegex, `$&${imageAttr}\\r\\n`);
          
          // 2. Add frame rate restriction
          const frameRateAttr = `a=framerate:${frameRate}.0`;
          modifiedSdp = modifiedSdp.replace(h264RtpmapRegex, `$&${frameRateAttr}\\r\\n`);
          
          // 3. Add H.264-specific settings via fmtp
          let h264FmtpParams = [];
          
          // Check if there's an existing fmtp line for H.264
          const existingFmtpMatch = modifiedSdp.match(new RegExp(`a=fmtp:${h264PayloadType} (.+)\\r\\n`));
          if (existingFmtpMatch) {
            // Parse existing parameters
            const existingParams = existingFmtpMatch[1].split(';');
            h264FmtpParams = [...existingParams];
            
            // Remove the existing fmtp line
            modifiedSdp = modifiedSdp.replace(new RegExp(`a=fmtp:${h264PayloadType} .+\\r\\n`), '');
          }
          
          // Set profile based on settings
          let profileId = '42e01f'; // Default: High profile, Level 3.1
          if (codecSettings.h264.profile === 'high') {
            if (codecSettings.h264.level === '4.2') {
              profileId = '640029'; // High profile, Level 4.2
            } else if (codecSettings.h264.level === '5.1') {
              profileId = '640034'; // High profile, Level 5.1
            } else {
              profileId = '64001f'; // High profile, Level 3.1
            }
          } else if (codecSettings.h264.profile === 'main') {
            profileId = '4d001f'; // Main profile, Level 3.1
          } else {
            profileId = '42001f'; // Baseline profile, Level 3.1
          }
          
          // Replace profile-level-id if it exists, otherwise add it
          let hasProfile = false;
          for (let i = 0; i < h264FmtpParams.length; i++) {
            if (h264FmtpParams[i].includes('profile-level-id')) {
              h264FmtpParams[i] = `profile-level-id=${profileId}`;
              hasProfile = true;
              break;
            }
          }
          
          if (!hasProfile) {
            h264FmtpParams.push(`profile-level-id=${profileId}`);
          }
          
          // Add packetization mode
          let hasPacketization = false;
          for (let i = 0; i < h264FmtpParams.length; i++) {
            if (h264FmtpParams[i].includes('packetization-mode')) {
              h264FmtpParams[i] = `packetization-mode=${codecSettings.h264.packetizationMode}`;
              hasPacketization = true;
              break;
            }
          }
          
          if (!hasPacketization) {
            h264FmtpParams.push(`packetization-mode=${codecSettings.h264.packetizationMode}`);
          }
          
          // Add level-asymmetry-allowed for better compatibility
          h264FmtpParams.push('level-asymmetry-allowed=1');
          
          // Add additional quality parameters
          h264FmtpParams.push('x-google-max-bitrate=' + bitrate);
          h264FmtpParams.push('x-google-min-bitrate=' + Math.floor(bitrate * 0.7));
          h264FmtpParams.push('x-google-start-bitrate=' + Math.floor(bitrate * 0.85));
          
          // Add the new fmtp line
          const newFmtpLine = `a=fmtp:${h264PayloadType} ${h264FmtpParams.join(';')}\r\n`;
          modifiedSdp = modifiedSdp.replace(h264RtpmapRegex, `$&${newFmtpLine}`);
          
          // 4. Add bitrate constraint if not already done for VP8
          if (!vp8Match) {
            const midRegex = /a=mid:0\r\n/g;
            if (modifiedSdp.match(midRegex)) {
              modifiedSdp = modifiedSdp.replace(midRegex, `a=mid:0\r\nb=AS:${bitrate}\r\nb=TIAS:${bitrate * 1000}\r\n`);
            }
          }
        }
        
        // Apply the modified SDP
        const modifiedOffer = new RTCSessionDescription({
          type: offer.type,
          sdp: modifiedSdp
        });
        
        await peerConnection.setLocalDescription(modifiedOffer);
        
        // Add additional debug info
        console.log("SDP offer being sent:", modifiedSdp);
        
        // Send the offer to the server and get answer
        const response = await fetch(`${serverUrl}/offer`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            sdp: peerConnection.localDescription.sdp,
            type: peerConnection.localDescription.type,
            // Explicitly include resolution and bitrate in case SDP parsing fails
            resolution: {
              width,
              height,
              bitrate,
              frameRate
            }
          }),
          credentials: 'include' // Include credentials (cookies) if needed
        });
        
        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }
        
        // Process the SDP answer from the server
        const answer = await response.json();
        
        // Store actual resolution info if provided by server
        if (answer.actualResolution) {
          actualResolution = answer.actualResolution;
          console.log("Server is using resolution:", actualResolution);
        }
        
        // Detect which codec the server is using
        if (answer.sdp) {
          if (answer.sdp.includes('H264')) {
            activeCodec = 'H.264';
          } else if (answer.sdp.includes('VP8')) {
            activeCodec = 'VP8';
          } else if (answer.sdp.includes('VP9')) {
            activeCodec = 'VP9';
          }
        }
        
        await peerConnection.setRemoteDescription(
          new RTCSessionDescription({
            sdp: answer.sdp,
            type: answer.type
          })
        );
        
        // Reset retry count on successful connection
        retryCount = 0;
        
      } catch (err) {
        // Check if this is a CORS error
        if (err.message.includes('Failed to fetch')) {
          updateConnectionStatus('error', 'CORS error: The server is not allowing connections from this origin.');
          console.error('CORS error detected:', err);
        } else {
          updateConnectionStatus('error', err.message || 'Failed to connect to server');
          console.error('Connection error:', err);
        }
        
        // Auto-retry logic for connection errors
        if (retryCount < MAX_RETRIES) {
          retryCount++;
          const retryDelay = 2000 * retryCount; // Increasing backoff
          console.log(`Retrying connection in ${retryDelay/1000} seconds... (Attempt ${retryCount} of ${MAX_RETRIES})`);
          
          setTimeout(() => {
            if (connectionStatus === 'error') {
              startConnection();
            }
          }, retryDelay);
        }
      }
    }
  
    // Cleanup function to close connections
    function stopConnection() {
      if (statsInterval) {
        clearInterval(statsInterval);
        statsInterval = null;
      }
      
      if (stream) {
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        stream = null;
      }
      
      if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
      }
      
      if (videoElement) {
        videoElement.srcObject = null;
      }
      
      updateConnectionStatus('disconnected');
      retryCount = 0;
      actualResolution = null;
      connectionStats = null;
    }
    
    // Apply quality changes by restarting the connection
    function applyQualitySettings() {
      if (connectionStatus === 'connected') {
        console.log("Applying new quality settings:", currentQuality);
        
        // Update custom quality preset if using custom
        if (selectedQuality === 'custom') {
          currentQuality.frameRate = customFrameRate;
          
          // Update the qualityPresets.custom
          qualityPresets.custom = {
            width: videoWidth,
            height: videoHeight,
            frameRate: customFrameRate,
            bitrate: customBitrate
          };
        }
        
        stopConnection();
        setTimeout(() => {
          startConnection();
        }, 500);
      }
    }
    
    // Format data size into human-readable format
    function formatBytes(bytes, decimals = 2) {
      if (bytes === 0) return '0 Bytes';
      const k = 1000;
      const dm = decimals < 0 ? 0 : decimals;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
  
    // Initialize on component mount
    onMount(() => {
      if (autoStart) {
        startConnection();
      }
    });
  
    // Clean up on component destroy
    onDestroy(() => {
      stopConnection();
    });
  </script>
  
  <div class="webrtc-container">
    <div class="video-container">
      <video 
        bind:this={videoElement} 
        width={videoWidth} 
        height={videoHeight}
        autoplay 
        playsinline
        muted
      >
        <track kind="captions" />
      </video>
      
      {#if connectionStatus === 'connecting'}
        <div class="status-overlay connecting">
          <p>Connecting to camera...</p>
        </div>
      {/if}
      
      {#if connectionStatus === 'error'}
        <div class="status-overlay error">
          <p>Connection error: {errorMessage}</p>
          {#if retryCount > 0 && retryCount < MAX_RETRIES}
            <p class="retry-message">Retrying... (Attempt {retryCount} of {MAX_RETRIES})</p>
          {/if}
        </div>
      {/if}
    </div>
    
    <div class="controls">
      {#if connectionStatus === 'disconnected' || connectionStatus === 'error'}
        <button on:click={startConnection}>Connect</button>
      {:else}
        <button on:click={stopConnection}>Disconnect</button>
      {/if}
      
      <span class="status-text">Status: {connectionStatus}</span>
      
      {#if activeCodec !== 'unknown'}
        <span class="codec-badge">Codec: {activeCodec}</span>
      {/if}
    </div>
    
    <div class="quality-controls">
      <label for="quality-select">Quality Setting:</label>
      <select id="quality-select" bind:value={selectedQuality}>
        <option value="low">Low (320×240)</option>
        <option value="medium">Medium (640×480)</option>
        <option value="high">High (720p)</option>
        <option value="fullhd">Full HD (1080p)</option>
        <option value="ultra">Ultra HD (1080p/60fps)</option>
        <option value="custom">Custom</option>
      </select>
      
      <div class="codec-selection">
        <label for="codec-select">Preferred Codec:</label>
        <select id="codec-select" bind:value={preferredCodec}>
          <option value="auto">Auto (Browser Default)</option>
          <option value="h264">H.264</option>
          <option value="vp8">VP8</option>
        </select>
      </div>
      
      {#if showCustomControls}
        <div class="custom-controls">
          <div class="custom-control">
            <label for="custom-width">Width:</label>
            <input 
              type="number" 
              id="custom-width" 
              bind:value={videoWidth} 
              min="160" 
              max="1920"
              step="16"
            />
          </div>
          
          <div class="custom-control">
            <label for="custom-height">Height:</label>
            <input 
              type="number" 
              id="custom-height" 
              bind:value={videoHeight} 
              min="120" 
              max="1080"
              step="16"
            />
          </div>
          
          <div class="custom-control">
            <label for="custom-bitrate">Bitrate (kbps):</label>
            <input 
              type="number" 
              id="custom-bitrate" 
              bind:value={customBitrate} 
              min="500" 
              max="50000"
              step="500"
            />
          </div>
          
          <div class="custom-control">
            <label for="custom-framerate">Frame Rate:</label>
            <input 
              type="number" 
              id="custom-framerate" 
              bind:value={customFrameRate} 
              min="5" 
              max="60"
              step="5"
            />
          </div>
        </div>
        
        <button 
          class="toggle-advanced" 
          on:click={() => showAdvancedSettings = !showAdvancedSettings}
        >
          {showAdvancedSettings ? 'Hide' : 'Show'} Advanced Settings
        </button>
        
        {#if showAdvancedSettings}
          <div class="advanced-settings">
            <h4>H.264 Settings</h4>
            <div class="setting-row">
              <label for="h264-profile">Profile:</label>
              <select id="h264-profile" bind:value={codecSettings.h264.profile}>
                <option value="baseline">Baseline (Compatible)</option>
                <option value="main">Main (Balanced)</option>
                <option value="high">High (Best Quality)</option>
              </select>
            </div>
            
            <div class="setting-row">
              <label for="h264-level">Level:</label>
              <select id="h264-level" bind:value={codecSettings.h264.level}>
                <option value="3.1">3.1 (Mainstream)</option>
                <option value="4.2">4.2 (High Quality)</option>
                <option value="5.1">5.1 (Maximum Quality)</option>
              </select>
            </div>
            
            <h4>Encoder Strategy</h4>
            <div class="setting-row">
              <label for="quality-vs-speed">Optimize For:</label>
              <select id="quality-vs-speed" bind:value={codecSettings.general.qualityVsSpeed}>
                <option value="quality">Quality (Slower Encoding)</option>
                <option value="balanced">Balanced</option>
                <option value="speed">Speed (Lower Quality)</option>
              </select>
            </div>
          </div>
        {/if}
      {/if}
      
      <button 
        class="apply-button" 
        on:click={applyQualitySettings} 
        disabled={connectionStatus !== 'connected'}
      >
        Apply Quality Changes
      </button>
    </div>
    
    <div class="current-settings">
      <p>
        Requested: {currentQuality.width}×{currentQuality.height} @ {currentQuality.frameRate}fps, {currentQuality.bitrate}kbps
        {#if actualResolution}
          <br>
          Server: {actualResolution.width}×{actualResolution.height} @ {actualResolution.bitrate}kbps
        {/if}
      </p>
    </div>
    
    {#if connectionStats}
      <div class="connection-stats">
        <h4>Stream Statistics <span class="timestamp">({connectionStats.timestamp})</span></h4>
        <div class="stats-grid">
          <div class="stat">
            <span class="stat-label">Actual Bitrate:</span>
            <span class="stat-value">{connectionStats.actualBitrate || 0} kbps</span>
          </div>
          <div class="stat">
            <span class="stat-label">Codec:</span>
            <span class="stat-value">{connectionStats.codec || 'Unknown'}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Data Received:</span>
            <span class="stat-value">{formatBytes(connectionStats.bytesReceived || 0)}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Frame Rate:</span>
            <span class="stat-value">{connectionStats.frameRate || 0} fps</span>
          </div>
          <div class="stat">
            <span class="stat-label">Packets Lost:</span>
            <span class="stat-value">{connectionStats.packetsLost || 0}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Jitter:</span>
            <span class="stat-value">{Math.round((connectionStats.jitter || 0) * 1000)} ms</span>
          </div>
        </div>
      </div>
    {/if}
    
    {#if connectionStatus === 'error' && errorMessage.includes('CORS')}
      <div class="cors-info">
        <h3>CORS Issue Detected</h3>
        <p>This is likely a Cross-Origin Resource Sharing (CORS) issue. The backend server needs to allow requests from this origin.</p>
        <p>To fix this:</p>
        <ol>
          <li>Make sure the server is running with CORS enabled for {window.location.origin}</li>
          <li>Check that the server URL is correct: <code>{serverUrl}</code></li>
        </ol>
      </div>
    {/if}
  </div>
  
  <style>
    .webrtc-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      max-width: 100%;
      padding: 1rem;
    }
    
    .video-container {
      position: relative;
      background-color: #000;
      border-radius: 4px;
      overflow: hidden;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    video {
      display: block;
    }
    
    .status-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background-color: rgba(0, 0, 0, 0.7);
      color: white;
      z-index: 2;
      padding: 1rem;
      text-align: center;
    }
    
    .connecting {
      background-color: rgba(0, 0, 0, 0.5);
    }
    
    .error {
      background-color: rgba(204, 0, 0, 0.5);
    }
    
    .retry-message {
      font-size: 0.9rem;
      margin-top: 0.5rem;
    }
    
    .controls {
      display: flex;
      gap: 1rem;
      align-items: center;
      margin-bottom: 1rem;
    }
    
    button {
      padding: 0.5rem 1rem;
      background-color: #3498db;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: bold;
      transition: background-color 0.2s;
    }
    
    button:hover {
      background-color: #2980b9;
    }
    
    button:disabled {
      background-color: #95a5a6;
      cursor: not-allowed;
    }
    
    .status-text {
      font-size: 0.9rem;
      color: #555;
    }
    
    .codec-badge {
      font-size: 0.9rem;
      background-color: #2ecc71;
      color: white;
      padding: 0.2rem 0.4rem;
      border-radius: 3px;
    }
    
    .quality-controls {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: a.8rem;
      background-color: #f8f9fa;
      padding: 1rem;
      border-radius: 4px;
      width: 100%;
      max-width: 500px;
    }
    
    .quality-controls label {
      margin-right: 0.5rem;
      font-weight: bold;
    }
    
    .quality-controls select {
      padding: 0.3rem 0.5rem;
      border-radius: 4px;
      border: 1px solid #ced4da;
      background-color: white;
    }
    
    .codec-selection {
      margin-top: 0.8rem;
      display: flex;
      align-items: center;
    }
    
    .custom-controls {
      display: flex;
      flex-wrap: wrap;
      gap: 0.8rem;
      width: 100%;
      margin-top: 0.8rem;
    }
    
    .custom-control {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      flex: 1;
      min-width: 100px;
    }
    
    .custom-control input {
      padding: 0.3rem;
      border-radius: 4px;
      border: 1px solid #ced4da;
      width: 100%;
    }
    
    .toggle-advanced {
      margin-top: 0.8rem;
      background-color: #7f8c8d;
      font-size: 0.9rem;
    }
    
    .toggle-advanced:hover {
      background-color: #6c7a7d;
    }
    
    .advanced-settings {
      margin-top: 0.8rem;
      width: 100%;
      padding: 0.8rem;
      background-color: #ecf0f1;
      border-radius: 4px;
    }
    
    .advanced-settings h4 {
      margin: 0.5rem 0;
      font-size: 1rem;
      color: #2c3e50;
    }
    
    .setting-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 0.5rem 0;
      gap: 1rem;
    }
    
    .setting-row label {
      flex: 1;
    }
    
    .setting-row select {
      flex: 2;
    }
    
    .apply-button {
      margin-top: 1rem;
      background-color: #27ae60;
    }
    
    .apply-button:hover {
      background-color: #219653;
    }
    
    .current-settings {
      font-size: 0.9rem;
      color: #666;
      margin-top: 0.5rem;
    }
    
    .connection-stats {
      width: 100%;
      max-width: 500px;
      margin-top: 1rem;
      padding: 0.8rem;
      background-color: #f1f8ff;
      border: 1px solid #d1e5ff;
      border-radius: 4px;
    }
    
    .connection-stats h4 {
      margin: 0 0 0.8rem 0;
      font-size: 1rem;
      color: #2c3e50;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .timestamp {
      font-size: 0.8rem;
      font-weight: normal;
      color: #7f8c8d;
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 0.8rem;
    }
    
    .stat {
      display: flex;
      flex-direction: column;
    }
    
    .stat-label {
      font-size: 0.8rem;
      color: #7f8c8d;
    }
    
    .stat-value {
      font-size: 1rem;
      font-weight: bold;
      color: #2c3e50;
    }
    
    .cors-info {
      margin-top: 1rem;
      padding: 1rem;
      background-color: #fff3cd;
      border: 1px solid #ffeeba;
      border-radius: 4px;
      color: #856404;
      max-width: 640px;
    }
    
    .cors-info h3 {
      margin-top: 0;
    }
    
    .cors-info code {
      background-color: #f8f9fa;
      padding: 0.2rem 0.4rem;
      border-radius: 3px;
      color: #e83e8c;
    }
    
    @media (max-width: 600px) {
      .custom-controls {
        flex-direction: column;
      }
      
      .stats-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>