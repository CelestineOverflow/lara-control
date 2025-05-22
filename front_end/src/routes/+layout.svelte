<script lang="ts">
	import LaraState from '$lib/LaraState.svelte';
	import { connect2Demon, connectApi } from '$lib/robotics/coordinate.svelte';
	import { apiSocketSetup, setupSocket } from '$lib/robotics/laraapi';

	import '../app.css';
	let { children } = $props();
	import { onMount } from 'svelte';
	import System from '$lib/System.svelte';
	import TestNotifications from '$lib/testNotifications.svelte';
	import NotificationList from '$lib/NotificationList.svelte';
	// import Notification from '$lib/Notification.svelte';

	onMount(async () => {
		
		await apiSocketSetup();
		await setupSocket();
		connectApi();
		connect2Demon();
		setTimeout(() => {
			window.location.reload();
		}, 1000 * 60 * 30); // 5 minutes
	});



</script>
<NotificationList />

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<!-- svelte-ignore a11y_missing_attribute -->
<div class="navbar bg-base text-primary-content">
	
	<div class="navbar-start">
		<a href="/" class="btn btn-ghost text-xl">LabHandler</a>
	</div>
	<div class="navbar-center">
		<System />
		<LaraState />
	</div>
	<div class="navbar-end">
		<div class="dropdown dropdown-end">
			<div tabindex="0" role="button" class="btn btn-ghost btn-circle">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 6h16M4 12h16M4 18h7"
					/>
				</svg>
			</div>
			<ul
				tabindex="0"
				class="menu menu-md dropdown-content bg-base-100 rounded-box z-1 mt-3 w-100 p-2 shadow-lg"
			>
				<li><a href="/">Dashboard</a></li>
				<li><a href="/docs">Docs</a></li>
			</ul>
		</div>
		
	</div>
</div>
{@render children()}
