<script lang="ts">
	import LaraState from '$lib/LaraState.svelte';
	import { connectApi } from '$lib/robotics/coordinate';
	import { setupSocket } from '$lib/robotics/laraapi';
	import { error, warning } from '$lib/robotics/coordinate';
	import '../app.css';
	let { children } = $props();
	import { onMount } from 'svelte';
	import Notification from '$lib/Notification.svelte';

	onMount(async () => {
		await setupSocket();
		connectApi();
	});

	// let notification_type = 'success';
	let notification_type = $state("success");
	// let notification_message = 'test';
	let notification_message = $state("test");
	// let show_notification = false;
	let show_notification = $state(false);

	$effect(() => {
		if ($error) {
			notification_type = 'error';
			notification_message = "wsws";
			show_notification = true;
		}
		if ($warning) {
			notification_type = 'warning';
			notification_message = "wsws";
			show_notification = true;
		}
	});
	

</script>

<!-- <Notification bind:type={notification_type} bind:content={notification_message} bind:show={show_notification} /> -->


<div class="navbar bg-base-100 shadow-sm">
	<div class="flex-none">
	  <!-- svelte-ignore a11y_consider_explicit_label -->
	  <button class="btn btn-square btn-ghost">
		<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block h-5 w-5 stroke-current"> <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path> </svg>
	  </button>
	</div>
	<div class="flex-1">
	  <!-- svelte-ignore a11y_missing_attribute -->
	  <a class="btn btn-ghost text-xl">LabHandler</a>
	</div>
	<div class="">
		<LaraState />
	</div>
	<div class="flex-none">
	  <!-- svelte-ignore a11y_consider_explicit_label -->
	  <button class="btn btn-square btn-ghost">
		<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block h-5 w-5 stroke-current"> <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"></path> </svg>
	  </button>
	</div>
  </div>
{@render children()}





