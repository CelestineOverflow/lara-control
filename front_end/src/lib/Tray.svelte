<script lang="ts">
	import Modal from './Modal.svelte';
	import { onMount } from 'svelte';
	import Prism from 'prismjs';
	import 'prismjs/components/prism-python';
	import 'prismjs/themes/prism-tomorrow.css';
	
	// Define the Waypoint interface
	let showModal = false;
	// Define columns (A-H) and rows (1-21)
	const columns = Array.from({ length: 8 }, (_, index) =>
		String.fromCharCode(65 + index)
	).reverse(); // ['H', 'G', ..., 'A']
	const rows = Array.from({ length: 21 }, (_, index) => index).reverse();
	let customOffsetXmm = 0;
	let customOffsetYmm = 0;
	
	// Developer mode toggle
	let devMode = false;
	
	// Array to store selected cells
	let selectedCells: {column: string, row: number}[] = [];
	
	// To store highlighted code
	let highlightedCode = '';
	
	// Drag selection state
	let isDragging = false;
	let dragMode: 'select' | 'deselect' = 'select';
	let startCell: {column: string, row: number} | null = null;
	

	$: pythonCode = `import arm_api
cells = [${(() => {
	const groups = [];
	const arr = selectedCells.map(cell => `"${cell.column}${cell.row}"`);
	for (let i = 0; i < arr.length; i += 4) {
		groups.push(arr.slice(i, i + 4).join(', '));
	}
	return groups.join(',\n');
})()}]

@arm_api.labhandler_sequence
def testers_code():
	print(f"cell at coordinates {cell.x}, {cell.y}")
	# This function will be called for each cell in the grid
	# it will be called on every cell
	# you can define your own logic here
	# down forget to turn on and off the power supplies!!
	
# Running tests over cells
for cell in cells:
	testers_code(cell)
`;

	
	
	// Update highlighted code whenever the Python code changes
	$: {
		if (typeof window !== 'undefined' && Prism) {
			highlightedCode = Prism.highlight(pythonCode, Prism.languages.python, 'python');
		} else {
			highlightedCode = pythonCode;
		}
	}
	
	// Mouse event handlers for drag selection
	function handleMouseDown(column: string, row: number, event: MouseEvent) {
		if (!devMode || !isMouseEvent(event)) return;
		
		isDragging = true;
		startCell = { column, row };
		
		// Determine drag mode based on the initial cell's selection state
		const isInitialCellSelected = isCellSelected(column, row);
		dragMode = isInitialCellSelected ? 'deselect' : 'select';
		
		// Toggle the clicked cell's selection state based on mode
		if (dragMode === 'select') {
			addToSelection(column, row);
		} else {
			removeFromSelectionByPosition(column, row);
		}
		
		// Prevent default behavior
		event.preventDefault();
	}
	
	function handleMouseMove(column: string, row: number, event: MouseEvent) {
		if (!devMode || !isDragging || !startCell || !isMouseEvent(event)) return;
		
		// Only toggle if this is a different cell than the last one we toggled
		const lastToggled = document.querySelector('[data-last-toggled="true"]');
		if (lastToggled) {
			lastToggled.removeAttribute('data-last-toggled');
		}
		
		// Add or remove based on drag mode
		if (dragMode === 'select') {
			if (!isCellSelected(column, row)) {
				addToSelection(column, row);
			}
		} else {
			if (isCellSelected(column, row)) {
				removeFromSelectionByPosition(column, row);
			}
		}
		
		// Mark this as the last toggled cell
		const currentCell = document.querySelector(`[data-column="${column}"][data-row="${row}"]`);
		if (currentCell) {
			currentCell.setAttribute('data-last-toggled', 'true');
		}
		
		event.preventDefault();
	}
	
	function handleMouseUp(event: MouseEvent) {
		if (!devMode || !isMouseEvent(event)) return;
		
		isDragging = false;
		startCell = null;
		
		// Prevent default behavior
		event.preventDefault();
	}
	
	// Utility to check if the event is from a mouse and not touch
	function isMouseEvent(event: MouseEvent) {
		return event.pointerType !== 'touch' && !('touches' in event);
	}
	
	// Helper functions for cell selection
	function toggleCellSelection(column: string, row: number) {
		if (isCellSelected(column, row)) {
			removeFromSelectionByPosition(column, row);
		} else {
			addToSelection(column, row);
		}
	}
	
	function addToSelection(column: string, row: number) {
		if (!isCellSelected(column, row)) {
			selectedCells = [...selectedCells, { column, row }];
		}
	}
	
	function removeFromSelectionByPosition(column: string, row: number) {
		selectedCells = selectedCells.filter(cell => !(cell.column === column && cell.row === row));
	}
	
	function removeFromSelection(index: number) {
		selectedCells = selectedCells.filter((_, i) => i !== index);
	}
	
	function isCellSelected(column: string, row: number) {
		return selectedCells.some(cell => cell.column === column && cell.row === row);
	}
	
	// Handle cell click (for both modes)
	function handleCellClick(column: string, row: number, event: MouseEvent) {
		// For touch devices or non-dev mode, maintain original behavior
		if (!devMode || event.pointerType === 'touch') {
			if (devMode) {
				toggleCellSelection(column, row);
			} else {
				moveToCell(column, row);
			}
			return;
		}
		
		// For mouse in dev mode, the drag handlers will take care of selection
	}
	
	// Clear selections
	function clearSelections() {
		selectedCells = [];
	}


	
	function moveToCell(x: string, y: number) {
		const _x = x.charCodeAt(0) - 65;
		console.log(x, y);
		const response = fetch(`http://192.168.2.209:1442/moveToCellSmart?row=${_x}&col=${y}&offset_z=0`, {
			method: 'POST',
			headers: {
				accept: 'application/json'
			}
		});
		console.log(response);
		
	}
	
	function generateWaypoints(
		event: MouseEvent & { currentTarget: EventTarget & HTMLButtonElement }
	) {
		throw new Error('Function not implemented.');
	}
	
	// Copy code to clipboard
	function copyToClipboard() {
		navigator.clipboard.writeText(pythonCode);
		
		// Visual feedback for copy
		const copyBtn = document.getElementById('copy-btn');
		if (copyBtn) {
			const originalText = copyBtn.textContent;
			copyBtn.textContent = 'Copied!';
			setTimeout(() => {
				copyBtn.textContent = originalText;
			}, 2000);
		}
	}
	
	// Handle global mouse up to cancel dragging even if outside cells
	function handleGlobalMouseUp(event: MouseEvent) {
		if (isDragging && devMode) {
			handleMouseUp(event);
		}
	}
	
	// Highlight code when component mounts and whenever devMode is toggled
	onMount(() => {
		if (typeof window !== 'undefined' && Prism) {
			highlightedCode = Prism.highlight(pythonCode, Prism.languages.python, 'python');
			Prism.highlightAll();
		}
		
		// Add global mouseup event listener
		window.addEventListener('mouseup', handleGlobalMouseUp);
		
		// Cleanup event listener on component destruction
		return () => {
			window.removeEventListener('mouseup', handleGlobalMouseUp);
		};
	});
</script>
<!-- Trigger Button to Open Modal -->
<button on:click={() => (showModal = true)} class="btn btn-soft btn-primary">Tray</button>
<!-- Modal Component -->
<Modal bind:showModal>
	<!-- Remove any fixed width constraints and make sure content fills the modal -->
	<div class="rounded bg-gray-900 p-4 shadow-lg text-gray-200 w-full h-full max-w-none">
		<!-- Developer Mode Toggle -->
		<div class="flex justify-between items-center mb-4">
			<h2 class="text-lg font-semibold">Tray Selection</h2>
			<label class="flex items-center cursor-pointer">
				<span class="mr-2 text-sm font-medium">Developer Mode</span>
				<div class="relative">
					<input type="checkbox" bind:checked={devMode} class="sr-only" />
					<div class="w-10 h-5 bg-gray-700 rounded-full"></div>
					<div class:transform={devMode} class:translate-x-5={devMode} class="absolute left-0.5 top-0.5 bg-white w-4 h-4 rounded-full transition"></div>
				</div>
			</label>
		</div>
		
		<!-- Instructions based on mode -->
		<p class="text-sm text-gray-400 mb-4">
			{#if devMode}
				Click or drag to select cells. Drag over selected cells to deselect them. Code updates automatically.
				{#if selectedCells.length > 0}
					<button 
						on:click={clearSelections}
						class="ml-2 text-xs bg-red-600 px-2 py-0.5 rounded hover:bg-red-700 transition-colors"
					>
						Clear All
					</button>
				{/if}
			{:else}
				Click on a cell to move the robot to that position.
			{/if}
		</p>
		
		<!-- Layout changes for full width -->
		<div class="{devMode ? 'grid grid-cols-1 lg:grid-cols-2 gap-4' : 'w-full'}">
			<!-- Waypoints Table - no width constraints, let it fill naturally -->
			<div class="overflow-x-auto">
				<table class="w-full bg-gray-800 text-sm select-none">
					<caption class="mb-2 text-base font-semibold text-gray-200"> Tray </caption>
					<tbody>
						{#each rows as row}
							<tr class="hover:bg-gray-700">
								{#each columns as column}
									{@const isSelected = devMode && isCellSelected(column, row)}
									<td class="border-b border-gray-700 px-1 py-1 text-center">
										<button
											data-column={column}
											data-row={row}
											class="rounded {isSelected ? 'bg-green-600' : 'bg-indigo-600'} h-6 w-10 text-xs font-medium text-white hover:opacity-80 flex items-center justify-center transition-colors duration-200"
											on:click={(e) => handleCellClick(column, row, e)}
											on:mousedown={(e) => handleMouseDown(column, row, e)}
											on:mouseover={(e) => handleMouseMove(column, row, e)}
											on:focus={() => {}}
										>
											<span class="inline-block">{column}{row}</span>
										</button>
									</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			
			<!-- Code Display (only in dev mode) - no width constraints -->
			{#if devMode}
				<div>
					<div class="bg-gray-800 rounded-lg overflow-hidden">
						<div class="bg-gray-700 px-4 py-2 flex justify-between items-center">
							<div class="flex items-center">
								<span class="text-sm font-medium">Python Code</span>
								<span class="ml-2 text-xs text-gray-400">({selectedCells.length} cells selected)</span>
							</div>
							<button 
								id="copy-btn"
								class="text-xs bg-blue-600 px-2 py-1 rounded hover:bg-blue-700 transition-colors"
								on:click={copyToClipboard}
							>
								Copy
							</button>
						</div>
						<pre class="text-gray-200 p-4 text-sm overflow-auto h-[500px] max-h-[calc(100vh-500px)]"><code class="language-python">{@html highlightedCode}</code></pre>
					</div>
				</div>
			{/if}
		</div>
	</div>
</Modal>
<style>
  /* Additional styles for Prism if needed */
  :global(.token.comment) {
    color: #6A9955;
  }
  
  :global(.token.string) {
    color: #CE9178;
  }
  
  :global(.token.keyword) {
    color: #569CD6;
  }
  
  /* Prevent text selection during drag */
  .select-none {
    user-select: none;
    -webkit-user-select: none;
  }
</style>