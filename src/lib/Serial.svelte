<script lang="ts">
    let isConnected = true;
    let errorMessage: string | null = null;
    let pumpValue: boolean = false;
    let hue: number = 0;
    let sat: number = 100;
    let light: number = 50;

    let leds = [0, 0, 0, 0, 0, 0, 0]; // Initialize LED states

    async function togglePump() {
        if (!isConnected) {
            errorMessage = "Serial port is not connected.";
            return;
        }
        pumpValue = !pumpValue;
        fetch(`http://localhost:1442/togglePump?boolean=${pumpValue}`, {
            method: "POST",
            headers: {
                "accept": "application/json",
            },
        });
    }

    async function setBrightness(newBrightness: number) {
        if (!isConnected) {
            errorMessage = "Serial port is not connected.";
            return;
        }
        fetch(`http://localhost:1442/setBrightness?newBrightness=${newBrightness}`, {
            method: "POST",
            headers: {
                "accept": "application/json",
            },
        });
    }


    async function setHeater(newHeat: number) {
        if (!isConnected) {
            errorMessage = "Serial port is not connected.";
            return;
        }
        fetch(`http://localhost:1442/setHeater?newHeat=${newHeat}`, {
            method: "POST",
            headers: {
                "accept": "application/json",
            },
        });
    }

    

    async function setLeds() {
        if (!isConnected) {
            errorMessage = "Serial port is not connected.";
            return;
        }

        fetch(`http://localhost:1442/setLeds`, {
            method: "POST",
            headers: {
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ leds }),
        });
    }

    async function setHSL(hue: number, sat: number, light: number) {
        if (!isConnected) {
            errorMessage = "Serial port is not connected.";
            return;
        }
        fetch(`http://localhost:1442/setHSL?hue=${hue}&sat=${sat}&light=${light}`, {
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

        <div class="mb-4">
            <label for="heater" class="block text-gray-700 text-sm font-bold mb-2">Heater</label>
            <input 
                type="text" 
                on:input={e => setHeater(parseInt(e.target.value))} 
                on:keypress={e => { if (e.key === 'Enter') setHeater(parseInt(e.target.value)); }} 
                class="input" 
            />
        </div>


        <div class="mb-4">
            <button
            on:click={togglePump}
            disabled={!isConnected}
            class="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
            >
            {pumpValue ? "Turn Off Pump" : "Turn On Pump"}
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
        <div class="mb-4">
            <label for="led-control" class="block text-gray-700 text-sm font-bold mb-2">LED Control</label>
            <div class="grid grid-cols-7 gap-2">
                {#each leds as led, i}
                <label class="flex items-center space-x-2">
                    <input
                        type="checkbox"
                        checked={led}
                        on:change={() => {
                            leds[i] = leds[i] ? 0 : 1;
                            setLeds();
                        }}
                        class="form-checkbox text-purple-500"
                    />
                    <span class="text-sm text-gray-700">LED {i + 1}</span>
                </label>
                {/each}
            </div>
        </div>
        <div class="mb-4">
            <label for="hue" class="block text-gray-700 text-sm font-bold mb-2">Hue</label>
            <input
            type="range"
            min="0"
            max="360"
            step="1"
            value={hue}
            on:input={e => { hue = parseInt(e.target.value); setHSL(hue, sat, light); }}
            class="slider"
            />
        </div>
        <div class="mb-4">
            <label for="saturation" class="block text-gray-700 text-sm font-bold mb-2">Saturation</label>
            <input
            type="range"
            min="0"
            max="100"
            step="1"
            value={sat}
            on:input={e => { sat = parseInt(e.target.value); setHSL(hue, sat, light); }}
            class="slider"
            />
        </div>
        <div class="mb-4">
            <label for="lightness" class="block text-gray-700 text-sm font-bold mb-2">Lightness</label>
            <input
            type="range"
            min="0"
            max="100"
            step="1"
            value={light}
            on:input={e => { light = parseInt(e.target.value); setHSL(hue, sat, light); }}
            class="slider"
            />
        </div>
    </div>
</div>
