<script lang="ts">
	import { onMount } from "svelte";
	import Modal from "$lib/components/Modal.svelte";
	import * as THREE from "three";
	// Define the Waypoint interface
	interface Waypoint {
		name: string;
		position: THREE.Vector3;
	}
	let showModal = false;
	// Define columns (A-H) and rows (1-21)
	const columns = Array.from({ length: 8 }, (_, index) =>
		String.fromCharCode(65 + index),
	).reverse(); // ['H', 'G', ..., 'A']
	const rows = Array.from({ length: 22 }, (_, index) => index).reverse();
	let tab_selected = 1;

	let customOffsetXmm = 0;
	let customOffsetYmm = 0;


    function moveToCell(arg0: string): any {
		let x = arg0.charCodeAt(0) - 65;
		let y = parseInt(arg0[1]);
		console.log(x, y);
		const response = fetch(`http://localhost:1442/moveToCell?row=${y}&col=${x}&offset_z=0`, {
			method: "POST",
			headers: {
				"accept": "application/json",
			},
		});
		console.log(response);
		
    }


    async function setSocket() {
		//
        const response = await fetch("http://localhost:1442/setSocket", {
			method: "POST",
			headers: {
				"accept": "application/json",
			},
		});
		const data = await response.json();
		console.log(data);
    }


    async function goToSocket() {
		const response = await fetch("http://localhost:1442/moveToSocket?offset_z=0", {
			method: "POST",
			headers: {
				"accept": "application/json",
			},
		});
		const data = await response.json();
		console.log(data);
    }
	//
// 	curl -X 'POST' \
//   'http://localhost:1442/TurnJogOff' \
//   -H 'accept: application/json' \
//   -d ''

	async function turnJogOff() {
		const response = await fetch("http://localhost:1442/TurnJogOff", {
			method: "POST",
			headers: {
				"accept": "application/json",
			},
		});
	}


    function generateWaypoints(event: MouseEvent & { currentTarget: EventTarget & HTMLButtonElement; }) {
        throw new Error("Function not implemented.");
    }
</script>

<!-- Trigger Button to Open Modal -->
<button
	on:click={() => (showModal = true)}
	class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
>
	Select Tray
</button>
<button
	on:click={() => (goToSocket())}
	class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
>
	Go to Socket
</button>
<button
	on:click={() => (setSocket())}
	class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
>
	Set Socket
</button>

<button
	on:click={() => (turnJogOff())}
	class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
>

	Turn Jog Off
</button>
<!-- Modal Component -->
<Modal bind:showModal>
	<div class="p-6 bg-white rounded shadow-lg">
		<!-- Tab Navigation -->
		<div class="flex mb-4">
			<button
				on:click={() => (tab_selected = 0)}
				class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mr-2"
				class:selected={tab_selected === 0}
			>
				Tray Configuration
			</button>
			<button
				on:click={() => (tab_selected = 1)}
				class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
				class:selected={tab_selected === 1}
			>
				Waypoints Table
			</button>
		</div>
		{#if tab_selected == 0}
		<h2 class="text-2xl font-bold mb-4">Tray Configuration</h2>
		<!-- Offset Inputs -->
		<div class="mb-4">
			<label
				class="block text-gray-700 text-sm font-bold mb-2"
				for="offsetX"
			>
				X Offset (mm)
			</label>
			<input
				id="offsetX"
				type="number"
				step="0.001"
				bind:value={customOffsetXmm}
				class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
				placeholder="Enter X offset"
			/>
		</div>
		<div class="mb-6">
			<label
				class="block text-gray-700 text-sm font-bold mb-2"
				for="offsetY"
			>
				Y Offset (mm)
			</label>
			<input
				id="offsetY"
				type="number"
				step="0.001"
				bind:value={customOffsetYmm}
				class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
				placeholder="Enter Y offset"
			/>
		</div>
		<!-- Generate Waypoints Button -->
		<button
			on:click={generateWaypoints}
			class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mb-6"
		>
			Generate Waypoints
		</button>
		{:else if tab_selected == 1}
		<!-- Waypoints Table -->
		<div class="overflow-x-auto">
			<table class="min-w-full bg-white">
				<caption class="text-lg font-semibold mb-2"
					>Current Tray Table</caption
				>
				<thead>
					<tr>
						{#each columns as column}
							<th
								class="px-2 py-2 border-b border-gray-200 bg-gray-100 text-left text-sm font-semibold text-gray-700"
							>
								{column}
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each rows as row}
						<tr class="hover:bg-gray-50">
							{#each columns as column}
								<td class="px-2 py-2 border-b border-gray-200">
									<button
										class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
										on:click={() =>
											moveToCell(`${column}${row}`)}
									>
										{column}{row}
									</button>
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		{/if}
	</div>
</Modal>
