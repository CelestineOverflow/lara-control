<script lang="ts">
	import { onDestroy } from 'svelte';
	import { fade } from 'svelte/transition';
	import { toastStore, type Toast } from './NotificationsLib';
	let toasts: Toast[] = [];
	const unsubscribe = toastStore.subscribe((arr) => (toasts = arr));
	onDestroy(unsubscribe);
</script>

<div class="fixed right-5 top-5 z-50 flex flex-col space-y-2">
	{#each toasts as toast (toast.id)}
		<div
			in:fade={{ duration: 200 }}
			out:fade={{ duration: 200 }}
			class="flex items-start justify-between rounded px-4 py-3 text-white shadow-md"
			class:bg-blue-500={toast.type === 'information'}
			class:bg-yellow-500={toast.type === 'warning'}
			class:bg-red-500={toast.type === 'error'}
		>
			<div class="mr-4 flex-1">
				<p class="font-semibold capitalize">{toast.type}</p>
				<p class="text-sm">{toast.message}</p>
			</div>
			<button
				class="text-xl leading-none focus:outline-none"
				on:click={() => toastStore.remove(toast.id)}
				aria-label="Dismiss"
			>
				&times;
			</button>
		</div>
	{/each}
</div>
