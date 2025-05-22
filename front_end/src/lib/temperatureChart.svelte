<script lang="ts">
	import { temperature } from '$lib/robotics/coordinate.svelte';
  import { onMount } from "svelte";
  import ChartWorker from './ChartWorker.ts?worker'; 
	import { setHeater } from './robotics/laraapi';

  let canvas: HTMLCanvasElement;
  let dataIndex = 0;
  const MAX_DATA_POINTS = 1000;

  let current_pressure_in_grams = 0.0;
  let target_pressure_in_grams = 0.0;
  let heater_percentage = 0;

  onMount(() => {
    // 1) Create the Worker
    const worker = new ChartWorker();

    // 2) Transfer the canvas to OffscreenCanvas and send to the worker
    const offscreenCanvas = canvas.transferControlToOffscreen();
    worker.postMessage(
      {
        type: "init",
        canvas: offscreenCanvas
      },
      [offscreenCanvas] // transfer ownership
    );

    // 3) Subscribe to temperature store
    const unsubscribe = temperature.subscribe((value) => {
      if (value.current === null) return;

      current_pressure_in_grams = parseFloat(value.current);
      target_pressure_in_grams = value.target ? parseFloat(value.target) : 0;
      heater_percentage = value.heater;

      // Post the data to the worker for chart update
      worker.postMessage({
        type: "updateData",
        payload: {
          currentForce: current_pressure_in_grams,
          targetForce: target_pressure_in_grams,
          dataIndex,
          maxDataPoints: MAX_DATA_POINTS,
        }
      });
      dataIndex++;
    });

    return () => {
      // Cleanup
      unsubscribe();
      worker.terminate();
    };
  });
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


</script>

<!-- HTML Layout -->
<div class="bg-gray-800 text-white h-full flex flex-col p-4 round" >
  <h2 class="text-2xl text-white font-bold text-right">Temperature</h2>
  <h2 class="text-xl text-gray-400 font-bold text-right">
    Heater: {heater_percentage} | 
    Current: {current_pressure_in_grams.toFixed(0)} c° | 
    Preset: {target_pressure_in_grams.toFixed(0)} c°
  </h2>
  <!-- The chart is rendered in the Worker via OffscreenCanvas -->
  <canvas bind:this={canvas}></canvas>
  <div class="grid grid-cols-4 gap-1">
		<input
			type="text"
			class="col-span-3 text-black text-sm p-2"
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
</div>