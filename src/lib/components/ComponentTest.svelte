<script lang="ts">
    export let title = "";
</script>

<div
    class={`card p-4 rounded text-gray-100 bg-gray-800 dark:bg-gray-200 dark:text-gray-800`}
>
    <div class="card-body">
        {#if title}
            <h5 class="card-title text-xl font-bold">
                {title}
            </h5>
        {/if}
        <slot />
    </div>
</div>
