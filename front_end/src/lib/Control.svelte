<script lang="ts">
	import CartesianPad from '$lib/CartesianPad.svelte';
	import { autonomous_control } from './robotics/coordinate.svelte';
	import { goToSocket, keepForce, press, setHeater, setSocket, setTray, stopKeepForce, togglePump } from './robotics/laraapi';
	import Tray from './Tray.svelte';

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
		actuatorControl: false,
		cameraControl: false,
    plunger: false,
	};

	// Toggle function for accordion sections
	const toggleSection = (section: string) => {
		openSections[section] = !openSections[section];
	};


  let isProgressSocket = false;
  async function goToSocketTrigger() {
    isProgressSocket = true;
    await goToSocket();
    isProgressSocket = false;
    
  }
	let isCurrentlyHeating = false;
	let inputTemperature = '';

  	async function setTemperature() {
		const val = Number(inputTemperature);
		if (!isNaN(val)) {
			// Prevent multiple requests
			if (isCurrentlyHeating) {
				console.error('Already heating');
				return;
			}
			isCurrentlyHeating = true;
			let result = await setHeater(val);
			isCurrentlyHeating = false;
		} else {
			console.error('Invalid pressure value');
		}
	}
	let inputPressure = '';
	let threshold = 10000; // Default threshold value
	let isCurrentlyPressing = false;

	async function setPressure() {
		const val = Number(inputPressure);
		if (!isNaN(val)) {
      if (isCurrentlyPressing) {
        console.error('Already pressing');
        return;
      }
      isCurrentlyPressing = true;
			let result = await press(val);
      isCurrentlyPressing = false;
		} else {
			console.error('Invalid pressure value');
		}
	}
	async function setKeepForce() {
		const val = Number(inputPressure);
		if (!isNaN(val)) {
			let result = await keepForce(val);
		} else {
			console.error('Invalid pressure value');
		}
	}


</script>

<div class="h-full w-full">
	{#if $autonomous_control}{:else}{/if}
	<div class="join join-vertical bg-base-100 w-full rounded-2xl">
		<!-- Go to Waypoint Section -->
		<div class="collapse-arrow join-item border-base-300 collapse border">
			<input
				type="checkbox"
				checked={openSections.waypoint}
				on:change={() => toggleSection('waypoint')}
			/>
			<div class="collapse-title font-semibold">Go to Positions</div>
			<div class="collapse-content">
				<Tray />
				{#if isProgressSocket}
        <!-- svelte-ignore a11y_consider_explicit_label -->
        <button class="btn btn-disabled" tabindex="-1" role="button" aria-disabled="true">
          <span class="loading loading-spinner text-primary"></span>
        </button>
        {:else}
        <button on:click={() => goToSocketTrigger()} class="btn btn-soft btn-secondary">Socket</button>
        {/if}
			</div>
		</div>
		<!-- Set Waypoints Section -->
		<div class="collapse-arrow join-item border-base-300 collapse border">
			<input
				type="checkbox"
				checked={openSections.setWaypoints}
				on:change={() => toggleSection('setWaypoints')}
			/>
			<div class="collapse-title font-semibold">Set Positions</div>
			<div class="collapse-content">
				<div class="lg:tooltip" data-tip="Set current Position as tray origin">

          <button on:click={setTray} class="btn btn-soft btn-primary">Tray</button>

				</div>
        <div class="lg:tooltip" data-tip="Set current position as socket">
          <button on:click={() => setSocket()} class="btn btn-soft btn-secondary">Socket</button>
        </div>
        
			</div>
		</div>

		<!-- Arm Control Section -->
		<div class="collapse-arrow join-item border-base-300 collapse border">
			<input
				type="checkbox"
				checked={openSections.armControl}
				on:change={() => toggleSection('armControl')}
			/>
			<div class="collapse-title font-semibold">Arm Control 🦾</div>
			<div class="collapse-content">
				<CartesianPad />
			</div>
		</div>
    <div class="collapse-arrow join-item border-base-300 collapse border">
			<input
				type="checkbox"
				checked={openSections.actuatorControl}
				on:change={() => toggleSection('Plunger')}
			/>
			<div class="collapse-title font-semibold">Actuator </div>
			<div class="collapse-content">
				<button
					on:click={() => togglePump(on_off).then(() => (on_off = !on_off))}
					class="btn mt-2 rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
				>
					{on_off ? 'Turn On Pump' : 'Turn Off Pump'}
				</button>
					<div class="grid grid-cols-4 gap-1">
		<input
			type="text"
			class="col-span-3 p-2 text-sm text-black"
			required
			placeholder="Type a number between 0° to 250°"
			bind:value={inputTemperature}
			title="Must be between be 1 to 10"
			on:keyup={(e) => {
				if (e.key === 'Enter') {
					setTemperature();
				}
			}}
		/>
		{#if isCurrentlyHeating}
			<span class="loading loading-spinner text-primary"></span>
		{:else}
			<button on:click={setTemperature} class="btn btn-outline btn-success">Set</button>
		{/if}
	</div>
	<div class="grid grid-cols-4 gap-1">
		<input
			type="text"
			class="col-span-3 text-black text-sm p-2"
			required
			placeholder="Type a number between 1000.0 to 10000.0"
			bind:value={inputPressure}
			title="Must be between be 1 to 10"
			on:keyup={(e) => {
				if (e.key === 'Enter') {
					setPressure();
				}
			}}
		/>
		{#if isCurrentlyPressing}
			<span class="loading loading-spinner text-primary"></span>
		{:else}
			<button on:click={setPressure} class="btn btn-outline btn-success">Set</button>
		{/if}
		<button on:click={setKeepForce} class="btn btn-outline btn-warning">Keep</button>
		<button on:click={stopKeepForce} class="btn btn-outline btn-error">Stop Keep</button>

	</div>
			</div>
		</div>
	</div>
</div>
