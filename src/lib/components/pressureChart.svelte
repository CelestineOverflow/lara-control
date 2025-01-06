<script lang="ts">
  import { onMount } from "svelte";
  import { loadcell_value } from "$lib/coordinate";
  import ChartWorker from "./ChartWorker.ts?worker";

  let canvas: HTMLCanvasElement;
  let dataIndex = 0;
  const MAX_DATA_POINTS = 100;

  let current_pressure_in_grams = 0.0;
  let target_pressure_in_grams = 0.0;

  onMount(() => {
    // 1) Create a new worker (same worker file as your temperature chart)
    const worker = new ChartWorker();

    // 2) Transfer this new canvas to OffscreenCanvas
    const offscreen = canvas.transferControlToOffscreen();
    worker.postMessage(
      {
        type: "init",
        canvas: offscreen
      },
      [offscreen]
    );

    // 3) Subscribe to your store and send updates to this Worker
    const unsubscribe = loadcell_value.subscribe((value) => {
      const tempTarget = value; // or parse if needed
      const tempCurrent = value; // or parse if needed

      if (isNaN(tempTarget) || isNaN(tempCurrent)) {
        return;
      }

      current_pressure_in_grams = tempCurrent;
      target_pressure_in_grams = tempTarget;

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
      unsubscribe();
      worker.terminate();
    };
  });
</script>

<div class="bg-gray-800 text-white h-full flex flex-col p-4 round">
  <h2 class="text-2xl text-white font-bold text-right">Force</h2>
  <h2 class="text-xl text-gray-400 font-bold text-right">
    Current: {current_pressure_in_grams.toFixed(0)} g | Preset: {target_pressure_in_grams.toFixed(0)} g
  </h2>
  <canvas bind:this={canvas}></canvas>
</div>
