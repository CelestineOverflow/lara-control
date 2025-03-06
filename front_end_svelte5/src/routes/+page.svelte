<script lang="ts">
	import { Pane, Splitpanes } from 'svelte-splitpanes';
	import Control from '$lib/Control.svelte';
	import Stream from '$lib/Stream.svelte';
</script>
<Stream />
<Splitpanes style="height: 92vh">
	<!-- Video Stream Panel -->
	<Pane size={50} snapSize={10}>
		<div class="stream-container">
			<div class="flex h-full items-center justify-center bg-gray-200">
				<p class="text-2xl text-gray-500">Stream</p>
			</div>
		</div>
	</Pane>

	<!-- Charts Panel -->
	<Pane>
		<Splitpanes horizontal={true}>
			<!-- Pressure Chart -->
			<Pane minSize={10}>
				<div class="chart-container">
					<div class="flex h-full items-center justify-center bg-gray-200">
						<p class="text-xl text-gray-500">Pressure Chart</p>
					</div>
				</div>
			</Pane>

			<!-- Temperature Chart -->
			<Pane>
				<div class="chart-container">
					<div class="flex h-full items-center justify-center bg-gray-200">
						<p class="text-xl text-gray-500">Temperature Chart</p>
					</div>
				</div>
			</Pane>
		</Splitpanes>
	</Pane>
	<Pane size={15} snapSize={10}>
		<Control />
	</Pane>
</Splitpanes>

<style>
	/* Import splitpanes styling */
	:global(.splitpanes) {
		background-color: white;
	}

	:global(.splitpanes__pane) {
		box-sizing: border-box;
	}

	:global(.splitpanes--vertical > .splitpanes__splitter) {
		min-width: 6px;
		background-color: #e9ecef;
	}

	:global(.splitpanes--horizontal > .splitpanes__splitter) {
		min-height: 6px;
		background-color: #e9ecef;
	}

	/* Container styling */
	.stream-container,
	.chart-container {
		height: 100%;
		width: 100%;
		overflow: hidden;
	}
</style>
