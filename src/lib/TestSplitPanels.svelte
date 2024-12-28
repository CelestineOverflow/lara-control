<!-- <script lang="ts">
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Base from "$lib/base.svelte";
  import ComponentTest from "./components/ComponentTest.svelte";
  import TemperatureChart from "./components/temperatureChart.svelte";
  import PressureChart from "./components/pressureChart.svelte";
    import ControlPad from "./ControlPad.svelte";
  let lineChartHandler0: any;
  let lineChartHandler1: any;
</script>

<Splitpanes >
  <Pane minSize={25}>
    <ComponentTest title={`Camera`}></ComponentTest>
    <a
  </Pane>
  <Pane>
    <Splitpanes horizontal={true}>
      <Pane minSize={15}>
        <ComponentTest>
          <div class="grid grid-cols-1 md:grid-cols-2">
            <TemperatureChart bind:this={lineChartHandler0} />
            <PressureChart bind:this={lineChartHandler1} />
            <button
              on:click={() =>
                lineChartHandler0.addData({
                  label: String(new Date().getSeconds()),
                  values: [Math.random() * 100, Math.random() * 100],
                })}>Add Data</button
            >
            <button
              on:click={() =>
                lineChartHandler1.addData({
                  label: String(new Date().getSeconds()),
                  values: [Math.random() * 100, Math.random() * 100],
                })}>Add Data</button
            >
          </div>
        </ComponentTest>
      </Pane>
    </Splitpanes>
  </Pane>
  <Pane minSize={5}>
    <ComponentTest title={`Controls`}>
      <ControlPad />
  </ComponentTest>
  </Pane>
</Splitpanes> -->
