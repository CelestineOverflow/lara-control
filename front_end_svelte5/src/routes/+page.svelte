<script lang="ts">
	import { Pane, Splitpanes } from 'svelte-splitpanes';
	import Control from '$lib/Control.svelte';
	import Render from '$lib/Render.svelte';
	import PressureChart from '$lib/pressureChart.svelte';
	import TemperatureChart from '$lib/temperatureChart.svelte';
	import Overlay from '$lib/Overlay.svelte';
</script>

<Splitpanes style="height: 92vh" theme="invisible-theme">
	<Pane size={60} snapSize={10}>
		<Splitpanes horizontal={true} theme="invisible-theme">
		<!-- Render View Panel -->
		<Pane size={50} snapSize={30}>
			<Render />
		</Pane>
		<!-- Video Stream Panel -->
		<Pane size={50} snapSize={30}>
			<Overlay />
		</Pane>
		</Splitpanes>
	</Pane>
	<!-- Charts Panel -->
	<Pane size={25} snapSize={10}>
		<Splitpanes horizontal={true} theme="invisible-theme">
			<!-- Pressure Chart -->
			<Pane minSize={10}>
				<PressureChart />
			</Pane>
			<!-- Temperature Chart -->
			<Pane>
				<TemperatureChart />
			</Pane>
		</Splitpanes>
	</Pane>
	<Pane size={14} snapSize={10}>
		<Control />
	</Pane>
</Splitpanes>

<style>
  /* Make panes seamlessly connect */
  :global(.invisible-theme .splitpanes__pane) {
    background-color: #f8f8f8 !important;
  }
  
  /* Make splitters completely invisible */
  :global(.invisible-theme .splitpanes__splitter) {
    background-color: transparent !important;
    border: none !important;
    position: relative !important;
    z-index: 10 !important;
  }
  
  /* Vertical splitters - zero width with hover effect */
  :global(.invisible-theme.splitpanes--vertical > .splitpanes__splitter),
  :global(.invisible-theme .splitpanes--vertical > .splitpanes__splitter) {
    width: 15px !important; /* Invisible but wide enough to grab */
    margin: 0 -7px !important; /* Center it so it appears to have zero width */
    cursor: col-resize !important;
  }
  
  /* Horizontal splitters - zero height with hover effect */
  :global(.invisible-theme.splitpanes--horizontal > .splitpanes__splitter),
  :global(.invisible-theme .splitpanes--horizontal > .splitpanes__splitter) {
    height: 15px !important; /* Invisible but tall enough to grab */
    margin: -7px 0 !important; /* Center it so it appears to have zero height */
    cursor: row-resize !important;
  }
  
  /* Hover indicator for vertical splitters */
  :global(.invisible-theme.splitpanes--vertical > .splitpanes__splitter::after),
  :global(.invisible-theme .splitpanes--vertical > .splitpanes__splitter::after) {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 4px !important;
    height: 100% !important;
    background-color: rgba(0, 120, 215, 0) !important; /* Start transparent */
    transition: background-color 0.2s ease-in-out !important;
    border-radius: 2px !important;
  }
  
  /* Hover indicator for horizontal splitters */
  :global(.invisible-theme.splitpanes--horizontal > .splitpanes__splitter::after),
  :global(.invisible-theme .splitpanes--horizontal > .splitpanes__splitter::after) {
    content: '' !important;
    position: absolute !important;
    left: 0 !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    height: 4px !important;
    width: 100% !important;
    background-color: rgba(0, 120, 215, 0) !important; /* Start transparent */
    transition: background-color 0.2s ease-in-out !important;
    border-radius: 2px !important;
  }
  
  /* Show indicator on hover */
  :global(.invisible-theme .splitpanes__splitter:hover::after) {
    background-color: rgba(0, 120, 215, 0.6) !important; /* Semi-transparent blue */
  }
  
  /* Show indicator when active */
  :global(.invisible-theme .splitpanes__splitter.splitpanes__splitter__active::after) {
    background-color: rgba(0, 120, 215, 0.8) !important; /* More opaque blue when active */
  }
</style>