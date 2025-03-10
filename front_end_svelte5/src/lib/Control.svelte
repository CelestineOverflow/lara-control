<script lang="ts">
	import CartesianPad from "$lib/CartesianPad.svelte";
	import Tray from "./Tray.svelte";

	// State variables
	let hue: number = 0;
	let sat: number = 100;
	let light: number = 50;
	let force: number = 1000;
	let on_off: boolean = false;
	
	// Track open/closed state for each accordion section
	let openSections = {
		waypoint: false,
		setWaypoints: false,
		pressure: false,
		temperature: false,
		lightControl: false,
		armControl: false,
		cameraControl: false
	};
	
	// Toggle function for accordion sections
	const toggleSection = (section: string) => {
		openSections[section] = !openSections[section];
	};
	
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
<div class="w-full h-full">
  <div class="join join-vertical bg-base-100 w-full">
    <!-- Go to Waypoint Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="checkbox" checked={openSections.waypoint} on:change={() => toggleSection('waypoint')} />
      <div class="collapse-title font-semibold">Go to Waypoints</div>
      <div class="collapse-content">
        <Tray />
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
      <input type="checkbox" checked={openSections.setWaypoints} on:change={() => toggleSection('setWaypoints')} />
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
 
    
    <!-- Light Control Section -->
    <div class="collapse collapse-arrow join-item border-base-300 border">
      <input type="checkbox" checked={openSections.lightControl} on:change={() => toggleSection('lightControl')} />
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
      <input type="checkbox" checked={openSections.armControl} on:change={() => toggleSection('armControl')} />
      <div class="collapse-title font-semibold">Arm Control 🦾</div>
      <div class="collapse-content">
        <CartesianPad />
      </div>
    </div>
    
  </div>
</div>

