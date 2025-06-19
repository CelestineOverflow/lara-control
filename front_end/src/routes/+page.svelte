<script lang="ts">
	import Control from '$lib/Control.svelte';
	import OverlayWebrtc from '$lib/Overlay_webrtc.svelte';
	import PressureChart from '$lib/pressureChart.svelte';
	import RobotData from '$lib/RobotData.svelte';
	import TemperatureChart from '$lib/temperatureChart.svelte';
</script>

<div class="flex">
	<div class="relative w-4/5">
		<OverlayWebrtc />
		<div style="position: absolute; bottom: 0px; left: 0px; color: white; z-index: 10;">
			<div class="grid grid-cols-2 gap-0">
				<PressureChart />
				<TemperatureChart />
			</div>
		</div>
		<div style="position: absolute; bottom: 10px; right: 10px; color: white; z-index: 10;">
			<RobotData />
		</div>
	</div>
	<div class="w-1/5">
		<Control />
	</div>
</div>
