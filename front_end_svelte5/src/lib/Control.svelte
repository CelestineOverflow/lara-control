<script lang="ts">
	// State variables
	let hue: number = 0;
	let sat: number = 100;
	let light: number = 50;
	let force: number = 1000;
	let on_off: boolean = false;
	// Mock API functions
	const tare = () => console.log('Tare force probe');
	const press = (f: number) => console.log(`Pressing with force: ${f}g`);
	const setHeater = (temp: number) => console.log(`Setting heater to: ${temp}`);
	const setHSL = (h: number, s: number, l: number) =>
		console.log(`Setting HSL: (${h}, ${s}%, ${l}%)`);
	const togglePump = (state: boolean) => {
		console.log(`${state ? 'Turning off' : 'Turning on'} pump`);
		return Promise.resolve(state);
	};
	const goToSocket = () => console.log('Going to socket');
	const setSocket = () => console.log('Setting socket waypoint');
	const setTray = () => console.log('Generating tray');
	const heater = 25; // Mock value
	const leds = Array(7).fill(0); // Mock LED array
	const setLeds = () => console.log('Setting LEDs:', leds);
	// Mock autonomous control
	const autonomous_control = { subscribe: () => ({ unsubscribe: () => {} }) };
</script>

<div class="p-4">
  <div class="join join-vertical bg-base-100">
    <!-- Pressure Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="radio" name="controls-accordion" checked="checked" />
      <div class="collapse-title font-semibold">Pressure 🧊</div>
      <div class="collapse-content">
        <div class="mb-4">
          <button
            on:click={() => tare()}
            class="btn rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
          >
            Tare force probe
          </button>
          <p class="mb-2 text-sm font-bold text-gray-700">Current Force Target: {force} g</p>
          <label for="force" class="mb-2 block text-sm font-bold text-gray-700">Force (g)</label>
          <input
            type="number"
            value={force}
            on:input={(e) => (force = parseInt(e.target.value))}
            class="input w-full rounded border px-3 py-2 text-gray-700"
          />
          <button
            on:click={() => press(force)}
            class="btn mt-2 rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
          >
            Press
          </button>
        </div>
      </div>
    </div>

    <!-- Temperature Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="radio" name="controls-accordion" />
      <div class="collapse-title font-semibold">Temperature 🌡️</div>
      <div class="collapse-content">
        <div class="mb-4">
          <input
            type="text"
            value={heater}
            on:input={(e) => setHeater(parseInt(e.target.value))}
            on:keypress={(e) => {
              if (e.key === 'Enter') setHeater(parseInt(e.target.value));
            }}
            class="input w-full rounded border px-3 py-2 text-gray-700"
          />
          <button
            on:click={() => setHeater(heater)}
            class="btn mt-2 rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
          >
            Set
          </button>
        </div>
      </div>
    </div>

    <!-- Light Control Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="radio" name="controls-accordion" />
      <div class="collapse-title font-semibold">Light Control 🚦</div>
      <div class="collapse-content">
        <div class="mb-4">
          <label for="led-control" class="mb-2 block text-sm font-bold text-gray-700">LED Control</label>
          <div class="grid grid-cols-4 gap-2">
            {#each leds as led, i}
              <label class="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={led === 1}
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
          <label for="hue" class="mb-2 block text-sm font-bold text-gray-700">Hue</label>
          <input
            type="range"
            min="0"
            max="360"
            step="1"
            value={hue}
            on:input={(e) => {
              hue = parseInt(e.target.value);
              setHSL(hue, sat, light);
            }}
            class="slider w-full"
          />
        </div>
        <div class="mb-4">
          <label for="saturation" class="mb-2 block text-sm font-bold text-gray-700">Saturation</label>
          <input
            type="range"
            min="0"
            max="100"
            step="1"
            value={sat}
            on:input={(e) => {
              sat = parseInt(e.target.value);
              setHSL(hue, sat, light);
            }}
            class="slider w-full"
          />
        </div>
        <div class="mb-4">
          <label for="lightness" class="mb-2 block text-sm font-bold text-gray-700">Lightness</label>
          <input
            type="range"
            min="0"
            max="100"
            step="1"
            value={light}
            on:input={(e) => {
              light = parseInt(e.target.value);
              setHSL(hue, sat, light);
            }}
            class="slider w-full"
          />
        </div>
      </div>
    </div>

    <!-- Arm Control Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="radio" name="controls-accordion" />
      <div class="collapse-title font-semibold">Arm Control 🦾</div>
      <div class="collapse-content">
        <div class="mb-2 flex h-20 items-center justify-center bg-gray-200">
          <p class="text-gray-500">Cartesian Pad</p>
        </div>
      </div>
    </div>

    <!-- Camera Control Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="radio" name="controls-accordion" />
      <div class="collapse-title font-semibold">Camera Control 📷</div>
      <div class="collapse-content">
        <div class="mb-2 flex h-20 items-center justify-center bg-gray-200">
          <p class="text-gray-500">Camera Control</p>
        </div>
      </div>
    </div>

    <!-- Go to Waypoint Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="radio" name="controls-accordion" />
      <div class="collapse-title font-semibold">Go to Waypoint</div>
      <div class="collapse-content">
        <div class="mb-2 flex h-20 items-center justify-center bg-gray-200">
          <p class="text-gray-500">Tray</p>
        </div>
        <button
          on:click={() => goToSocket()}
          class="btn rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
        >
          Go to Socket
        </button>
        <button
          on:click={() => togglePump(on_off).then(() => (on_off = !on_off))}
          class="btn mt-2 rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
        >
          {on_off ? 'Turn Off Pump' : 'Turn On Pump'}
        </button>
      </div>
    </div>

    <!-- Set Waypoints Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="radio" name="controls-accordion" />
      <div class="collapse-title font-semibold">Set Waypoints</div>
      <div class="collapse-content">
        <button
          class="btn rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
          on:click={setTray}
        >
          Generate Tray
        </button>
        <button
          on:click={() => setSocket()}
          class="btn ml-2 rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
        >
          Set Socket
        </button>
      </div>
    </div>
  </div>
</div>