<script lang="ts">
	import { onMount } from 'svelte';
	import {
		loadcell_value,
		loadcell_target,
		unblock_pressure_flag
	} from '$lib/robotics/coordinate.svelte';
	import ChartWorker from './ChartWorker.ts?worker';
	import { keepForce, press, stopKeepForce } from '$lib/robotics/laraapi';

	let canvas: HTMLCanvasElement;
	let dataIndex = 0;
	const MAX_DATA_POINTS = 1000;
	const downsample = 10;
	let index = 0;

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
			index++;
			if (index > downsample) {
				index = 0;
				return; // Skip this update to downsample

			}
			
			const tempTarget = $loadcell_target;
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
	async function setKeepForce() {
		const val = Number(inputPressure);
		if (!isNaN(val)) {
			let result = await keepForce(val);
		} else {
			console.error('Invalid pressure value');
		}
	}
</script>

<div class="round bg-transparent p-4 text-white">
	<div class="grid grid-cols-2">
		<h2 class="text-xl text-right font-bold text-white" style="-webkit-text-stroke: 1px black;">
			Force Current: {current_pressure_in_grams.toFixed(0)} g | Target: {target_pressure_in_grams.toFixed(
				0
			)} g
		</h2>
	</div>

	<canvas bind:this={canvas}></canvas>
</div>
