<script lang="ts">
    import { Pane, Splitpanes } from "svelte-splitpanes";

    import ComponentTest from "./components/ComponentTest.svelte";
    import TemperatureChart from "./components/temperatureChart.svelte";
    import PressureChart from "./components/pressureChart.svelte";
    import ControlPad from "./ControlPad.svelte";
    import Camera from "./Camera.svelte";
    import Terminal from "./Terminal.svelte";
    import Simulation from "./Simulation.svelte";
    import Gimbal from "./Gimbal.svelte";
    import Stream from "./Stream.svelte";
    let lineChartHandler0: any;
    let lineChartHandler1: any;
</script>

<Splitpanes horizontal={true}>
    <Pane size={50}>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <TemperatureChart bind:this={lineChartHandler0} />
            <PressureChart bind:this={lineChartHandler1} />
            <div class="col-span-2">
                <Terminal />
            </div>
        </div>
    </Pane>
</Splitpanes>
