<script lang="ts">
	import { temperature } from '$lib/robotics/coordinate';
  import { onMount } from "svelte";
  import ChartWorker from './ChartWorker.ts?worker'; // or wherever your worker is

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
</div>