<script lang="ts">
  import CameraControl from "$lib/CameraControl.svelte";
  import CartesianPad from "$lib/CartesianPad.svelte";
  import PressureChart from "$lib/components/pressureChart.svelte";
  import TemperatureChart from "$lib/components/temperatureChart.svelte";
  import { heater, leds, setHeater, setLeds, setTray } from "$lib/robotics/laraapi";
  import Stream from "$lib/Stream.svelte";
  import Tray from "$lib/Tray.svelte";
  import Accordion from "$lib/Accordion.svelte";
  import { Pane, Splitpanes } from "svelte-splitpanes";
  let hue: number = 0;
  let sat: number = 100;
  let light: number = 50;
</script>

<Splitpanes style="height: 92vh">
  <Pane minSize={50}>
    <Stream />
  </Pane>
  <Pane>
    <Splitpanes horizontal={true}>
      <Pane minSize={10}>
        <PressureChart />
      </Pane>
      <Pane>
        <TemperatureChart />
      </Pane>
    </Splitpanes>
  </Pane>
  <Pane minSize={5}>
    <Accordion>
      <span slot="head">Temperature 🌡️</span>
      <div slot="details">
        <div class="mb-4">
          <input 
              type="text" 
              on:input={e => setHeater(parseInt(e.target.value))} 
              on:keypress={e => { if (e.key === 'Enter') setHeater(parseInt(e.target.value)); }} 
              class="input" 
          />
          <button 
              on:click={() => setHeater((heater))} 
              class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
              Set
          </button>
      </div>
      
      </div>
    </Accordion>

    <Accordion open={false}>
      <span slot="head">Light Control 🚦</span>
      <div slot="details">

      <div class="mb-4">
        <label for="led-control" class="block text-gray-700 text-sm font-bold mb-2">LED Control</label>
        <div class="grid grid-cols-7 gap-2">
            {#each leds as led, i}
            <label class="flex items-center space-x-2">
                <input
                    type="checkbox"
                    checked={led === 1}
                    on:change={() => {
                        leds[i] = leds[i] ? 0 : 1;
                        setLeds();
                    }}
                    class="form-checkbox text-purple-500"
                />
                <span class="text-sm text-gray-700">LED {i + 1}</span>
            </label>
            {/each}
        </div>
    </div>
      <div class="mb-4">
        <label for="hue" class="block text-gray-700 text-sm font-bold mb-2">Hue</label>
        <input
        type="range"
        min="0"
        max="360"
        step="1"
        value={hue}
        on:input={e => { hue = parseInt(e.target.value); setHSL(hue, sat, light); }}
        class="slider"
        />
    </div>


      <div class="mb-4">
        <label for="saturation" class="block text-gray-700 text-sm font-bold mb-2">Saturation</label>
        <input
        type="range"
        min="0"
        max="100"
        step="1"
        value={sat}
        on:input={e => { sat = parseInt(e.target.value); setHSL(hue, sat, light); }}
        class="slider"
        />
    </div>

      <div class="mb-4">
        <label for="lightness" class="block text-gray-700 text-sm font-bold mb-2">Lightness</label>
        <input
        type="range"
        min="0"
        max="100"
        step="1"
        value={light}
        on:input={e => { light = parseInt(e.target.value); setHSL(hue, sat, light); }}
        class="slider"
        />
    </div>
    </Accordion>

    <Accordion>
      <span slot="head">Arm Control 🦾</span>
      <div slot="details">
        <CartesianPad />
      </div>
    </Accordion>

    <Accordion>
      <span slot="head">Camera Control 📷</span>
      <div slot="details">
        <CameraControl />
      </div>
    </Accordion>

    <Accordion>
      <span slot="head">Go to </span>
      <div slot="details">
        <Tray />
        <button
        class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        on:click={setTray}
      >
        Generate Tray
      </button>
      </div>
    </Accordion>

    
    

  </Pane>
</Splitpanes>
