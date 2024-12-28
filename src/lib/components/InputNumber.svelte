<!-- <script lang="ts">
    let inputValue: string = "";
    export let value: number = 1.0;
    export let label: string = "set";
    const onEnter = () => {
        if (inputValue.trim() !== "") {
            const num = parseFloat(inputValue);
            if (!isNaN(num)) {
                value = num;
            } else {
                alert("Not a valid number");
                inputValue = "";
            }
        } else {
            alert("Please enter a number");
        }
    };
</script>

<div class="flex items-center space-x-2">
    <div class="flex-none w-20">
        <label for="target">Target:</label>
    </div>
    <div class="flex-grow">
        <input bind:value={inputValue} class="text-black px-2 py-1 rounded w-full" />
    </div>
    <div class="flex-none">
        <button
            on:click={onEnter}
            class="bg-red-500 hover:bg-red-700 text-white px-5 rounded text-s text-center"
        >
            {label}
        </button>
    </div>
</div> -->