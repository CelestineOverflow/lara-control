<script>
    import CartesianPad from '$lib/CartesianPad.svelte';
    import PressureChart from '$lib/components/pressureChart.svelte';
    import TemperatureChart from '$lib/components/temperatureChart.svelte';
    import { data } from '$lib/coordinate';
    import LaraSettings from '$lib/LaraSettings.svelte';
    import { setTray, getTray } from '$lib/robotics/laraapi';
    import Serial from '$lib/Serial.svelte';
  import Stream from '$lib/Stream.svelte';
    import Tray from '$lib/Tray.svelte';
import { Pane, Splitpanes } from 'svelte-splitpanes';
</script>

<Splitpanes style="height: 92vh">
  <Pane minSize={20}>
    <Stream/>
  </Pane>
  <Pane>
    <Splitpanes horizontal={true}>
      <Pane minSize={15}>
        <PressureChart/>
      </Pane>
      <Pane>
        <TemperatureChart/>
    </Pane>
    </Splitpanes>
  </Pane>
  <Pane>
    <Serial/>
    <Tray/>
    <LaraSettings/>
    <button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded" on:click={setTray}>
        Generate Tray
    </button>
    <button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded" on:click={getTray}>
        Show Tray
    </button>
    <CartesianPad/>
  </Pane>
</Splitpanes>