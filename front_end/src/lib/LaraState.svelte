<script lang="ts">
	import {
		lara_robot_power_status,
		lara_collision_status,
		powerOnOff,
		resetCollision,
		lara_simulated_status,
		simulateReal



	} from '$lib/robotics/laraapi';
</script>

<ul class="menu menu-vertical lg:menu-horizontal bg-base-200 rounded-box">
	{#if $lara_robot_power_status}
		<li>
			<button class="btn btn-success" on:click={() => powerOnOff(false)}>Robot On</button>
		</li>
	{:else}
		<li>
			<button class="btn btn-error" on:click={() => powerOnOff(true)}>Robot Off</button>
		</li>
	{/if}
	{#if $lara_collision_status}
		<li>
			<button class="btn btn-error" on:click={() => resetCollision()}>Collision</button>
		</li>
	{:else}
		<li>
			<button class="btn btn-success">No Collision</button>
		</li>
	{/if}
	{#if $lara_simulated_status}
		<li>
			<button class="btn btn-success">Real</button>
		</li>
	{:else}
		<li>
			<button on:click={() => simulateReal(true)} class="btn btn-warning">Simulated</button>
		</li>
	{/if}
	

</ul>
