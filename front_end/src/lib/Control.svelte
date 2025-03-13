<script lang="ts">
	import CartesianPad from "$lib/CartesianPad.svelte";
	import { autonomous_control } from "./robotics/coordinate";
	import { goToSocket, setSocket, setTray, togglePump } from "./robotics/laraapi";
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
	const heater = 25; // Mock value
	const leds = Array(7).fill(0); // Mock LED array
	const setLeds = () => console.log('Setting LEDs:', leds);

</script>
<div class="w-full h-full">
  {#if $autonomous_control}
  {:else}
  {/if}
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

