<script lang="ts">
	import CartesianPad from '$lib/CartesianPad.svelte';
	import { autonomous_control } from './robotics/coordinate.svelte';
	import { goToSocket, setSocket, setTray, togglePump } from './robotics/laraapi';
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


</script>

<div class="h-full w-full">
	{#if $autonomous_control}{:else}{/if}
	<div class="join join-vertical bg-base-100 w-full">
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
				checked={openSections.armControl}
				on:change={() => toggleSection('Plunger')}
			/>
			<div class="collapse-title font-semibold">Plunger </div>
			<div class="collapse-content">
				<button
					on:click={() => togglePump(on_off).then(() => (on_off = !on_off))}
					class="btn mt-2 rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700"
				>
					{on_off ? 'Turn On Pump' : 'Turn Off Pump'}
				</button>
			</div>
		</div>
	</div>
</div>
