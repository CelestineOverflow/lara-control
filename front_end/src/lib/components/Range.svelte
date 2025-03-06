<script lang="ts">
    import { createEventDispatcher } from "svelte";
    export let min: number;
    export let max: number = 1;
    export let value: number = 0;
    export let step: number = 0.1;

    const dispatch = createEventDispatcher();

    // Bind the local value to update whenever the input changes
    let localValue = value;

    function handleInput(event: Event) {
        localValue = +(event.target as HTMLInputElement).value;
        dispatch("input", localValue); // Dispatch the value as the event detail
    }
</script>

<div>
    <input
        type="range"
        {min}
        {max}
        {step}
        bind:value={localValue}
        on:input={handleInput}
    />
</div>