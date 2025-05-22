<script lang="ts">
	import { onMount } from 'svelte';
	import { loadcell_value, threshold, unblock_pressure_flag } from '$lib/robotics/coordinate.svelte';
	import ChartWorker from './ChartWorker.ts?worker';
	import { press } from '$lib/robotics/laraapi';

	let canvas: HTMLCanvasElement;
	let dataIndex = 0;
	const MAX_DATA_POINTS = 1000;

	let current_pressure_in_grams = 0.0;
	let target_pressure_in_grams = 0.0;

	onMount(() => {
		const worker = new ChartWorker();
		const offscreen = canvas.transferControlToOffscreen();
		worker.postMessage(
			{
				type: 'init',
				canvas: offscreen
			},
			[offscreen]
		);
		const unsubscribe = loadcell_value.subscribe((value) => {
			const tempTarget = value;
			const tempCurrent = value;
			if (isNaN(tempTarget) || isNaN(tempCurrent)) {
				return;
			}

			current_pressure_in_grams = tempCurrent;
			target_pressure_in_grams = tempTarget;

			worker.postMessage({
				type: 'updateData',
				payload: {
					currentForce: current_pressure_in_grams,
					targetForce: target_pressure_in_grams,
					dataIndex,
					maxDataPoints: MAX_DATA_POINTS
				}
			});
			dataIndex++;
		});

		return () => {
			unsubscribe();
			worker.terminate();
		};
	});

	let inputPressure: string = '';

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
</script>
<!-- 
<div class="stats bg-base-100 border border-base-300">
	<div class="stat">
	  <div class="stat-title">Force</div>
	  <div class="stat-value">{current_pressure_in_grams.toFixed(0)} g </div>
	  <div class="stat-actions">
		<button class="btn btn-xs btn-success">Add funds</button>
	  </div>
	</div>
  
	<div class="stat">
	  <div class="stat-title">Preset</div>
	  <div class="stat-value"> {target_pressure_in_grams.toFixed(0)} g</div>
	  <div class="stat-actions">
		<button class="btn btn-xs">Withdrawal</button>
		<button class="btn btn-xs">Deposit</button>
	  </div>
	</div>
  </div> -->

<div class="round flex h-full flex-col bg-gray-800 p-4 text-white">
	<h2 class="text-right text-2xl font-bold text-white">Force</h2>
	<h2 class="text-right text-xl font-bold text-gray-400">
		Current: {current_pressure_in_grams.toFixed(0)} g | Preset: {target_pressure_in_grams.toFixed(
			0
		)} g
	</h2>

	
	<canvas bind:this={canvas}></canvas>

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
	<li>
		<span class="text-sm">Max Force: {$threshold}</span>
	</li>
	<!-- <li>
		<span class="text-sm">Unblocked: {$unblock_pressure_flag}</span>
	</li> -->
	
	</div>
	
</div>
