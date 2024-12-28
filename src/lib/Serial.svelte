<script lang="ts">
    let isConnected = true;
    let errorMessage: string | null = null;
    let pumpValue: boolean = false;
    async function togglePump(){
        if (!isConnected) {
            errorMessage = "Serial port is not connected.";
            return;
        }
        pumpValue = !pumpValue;
        const command = JSON.stringify({
            pump: pumpValue
        }) + "\n"; // Append newline as Arduino expects it
        fetch(`http://localhost:1442/togglePump?boolean=${pumpValue}`, {
            method: "POST",
            headers: {
                "accept": "application/json",
            },
        });

    }


//     curl -X 'POST' \
//   'http://localhost:1442/setBrightness?newBrightness=127' \
//   -H 'accept: application/json' \
//   -d ''

    async function setBrightness(newBrightness: number){
        if (!isConnected) {
            errorMessage = "Serial port is not connected.";
            return;
        }
        const command = JSON.stringify({
            brightness: newBrightness
        }) + "\n"; // Append newline as Arduino expects it
        fetch(`http://localhost:1442/setBrightness?newBrightness=${newBrightness}`, {
            method: "POST",
            headers: {
                "accept": "application/json",
            },
        });
    }
 </script>
 <style>
    .control-group {
        margin-bottom: 1rem;
    }
    .control-group label {
        display: block;
        margin-bottom: 0.5rem;
    }
    .slider {
        width: 100%;
    }
    .incoming-data {
        width: 100%;
        height: 200px;
        resize: none;
    }
 </style>


 <div class="max-w-sm rounded overflow-hidden shadow-lg">
    <div class="px-6 py-4">
      <div class="font-bold text-xl mb-2">Plunger Serial Control</div>
      {#if isConnected}
      <p class="text-green-600 mb-4">✅ Connected to serial port</p>
      {:else}
      <p class="text-red-600 mb-4">❌ Not connected</p>
      {/if}
      {#if errorMessage}
      <p class="text-red-500 mb-4">{errorMessage}</p>
      {/if}
      <div class="flex space-x-4 mb-4">
      </div>
      <div class="mb-4">
         <button
         on:click={togglePump}
         disabled={!isConnected}
         class="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
         >
         {pumpValue == true ? "Turn Off Pump" : "Turn On Pump"}
         </button>
      </div>
      <div class="mb-4">
        <label for="brightness" class="block text-gray-700 text-sm font-bold mb-2">Brightness</label>
        <input
        type="range"
        min="0"
        max="255"
        step="1"
        on:input={e => setBrightness(parseInt(e.target.value))}
        class="slider"
        />
        </div>
      
    </div>
  </div>

  