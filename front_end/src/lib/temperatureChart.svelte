<script lang="ts">
	import { temperature } from '$lib/robotics/coordinate.svelte';
	import { onMount } from 'svelte';
	import ChartWorker from './TemperatureChartWorker.ts?worker';
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
				type: 'init',
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

<div class="round bg-transparent p-4 text-white">
	<div class="grid grid-cols-2 gap-2">
		<h2 class="text-right text-xl font-bold text-white" style="-webkit-text-stroke: 1px black;">
			Heater: {heater_percentage} | Current: {current_pressure_in_grams.toFixed(0)} c° | Preset: {target_pressure_in_grams.toFixed(
				0
			)} c°
		</h2>
	</div>
	<canvas
		bind:this={canvas}
		class="bg-transparent"
		style="background-color: transparent;"
	></canvas>
</div>
