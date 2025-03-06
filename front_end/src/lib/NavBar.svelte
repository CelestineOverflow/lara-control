<script lang="ts">
    import Popup from "./components/popup.svelte";

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
          <a data-sveltekit-reload
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
            class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
            >Docs</a
          >
        </div>
      </div>
    </div>
  </div>
</nav>

<Popup />

<style>
  nav {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
</style>