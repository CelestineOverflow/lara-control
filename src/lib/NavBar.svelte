<script lang="ts">
</script>

<nav class="bg-gray-900 sticky top-0 z-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      <!-- Logo Section -->
      <div class="flex items-center">
        <img src="icon.jpg" alt="LabHandler Logo" class="h-8 w-8 mr-2" />
        <span class="text-white font-semibold text-lg">LabHandler</span>
      </div>

      <!-- Navigation Links -->
      <div class="hidden sm:block">
        <div class="flex space-x-4">
          <a
            href="/"
            
            class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
            >Dashboard</a
          >
          <a
            href="/settings"
            class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
            >Settings</a
          >
          <a
            href="/docs"
            on:click|preventDefault={() => selected.set(3)}
            class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
            >Docs</a
          >
        </div>
      </div>

      <!-- Mobile Menu Button -->
      <div class="sm:hidden">
        <button
          type="button"
          class="text-gray-300 hover:text-white focus:outline-none"
          on:click={() => (open = !open)}
        >
          <svg
            class="h-6 w-6"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            {#if open}
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            {:else}
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            {/if}
          </svg>
        </button>
      </div>
    </div>
  </div>


  <!-- Mobile Menu -->
  {#if open}
    <div class="sm:hidden bg-gray-800">
      <div class="px-2 pt-2 pb-3 space-y-1">
        <a
          href="/"
          on:click|preventDefault={() => (selected.set(1), (open = false))}
          class="block text-gray-300 hover:text-white px-3 py-2 rounded-md text-base font-medium"
          >ssDashboard</a
        >
        <a
          href="/"
          on:click|preventDefault={() => (selected.set(2), (open = false))}
          class="block text-gray-300 hover:text-white px-3 py-2 rounded-md text-base font-medium"
          >Settings</a
        >
        <a
          href="/"
          on:click|preventDefault={() => (selected.set(3), (open = false))}
          class="block text-gray-300 hover:text-white px-3 py-2 rounded-md text-base font-medium"
          >Usage</a
        >
      </div>
    </div>
  {/if}
</nav>

<style>
  nav {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
</style>