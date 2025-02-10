<script lang="ts">
  let isConnected = true;
  let errorMessage: string | null = null;
  let leds = [0, 0, 0, 0, 0, 0, 0]; // Initialize LED states
  async function setLeds() {
    if (!isConnected) {
      errorMessage = "Serial port is not connected.";
      return;
    }

    fetch(`http://192.168.2.209:1442/setLeds`, {
      method: "POST",
      headers: {
        accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ leds }),
    });
  }
</script>

<div class="mb-4">
  <label for="led-control" class="block text-gray-700 text-sm font-bold mb-2"
    >LED Control</label
  >
  <div class="grid grid-cols-7 gap-2">
    {#each leds as led, i}
      <label class="flex items-center space-x-2">
        <input
          type="checkbox"
          checked={led}
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
