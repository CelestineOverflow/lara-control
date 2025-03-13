<script lang="ts">
    export let show: boolean;
    let dialog: HTMLDialogElement;
    $: if (dialog && show) dialog.show();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
<dialog
    bind:this={dialog}
    on:close={() => (show = false)}
    on:click|self={() => dialog.close()}
    class="dark-modal"
>
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div on:click|stopPropagation>
        <slot name="content" />
        <slot />
    </div>
</dialog>

<style>
    dialog {

        border-radius: 0.2em;
        border: none;
        padding: 0;
        background-color: transparent;
        color: #e5e7eb; /* gray-200 */
        position: fixed;
        top: 10%;
        left: 50%;
        transform: translate(-50%, -50%);
        margin: 0;
    }
    
    dialog::backdrop {
        background: rgba(0, 0, 0, 0.5);
    }
    
    dialog > div {
        padding: 0.25em;
    }
    
    dialog[open] {
        animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    
    @keyframes zoom {
        from {
            transform: translate(-50%, -50%) scale(0.95);
        }
        to {
            transform: translate(-50%, -50%) scale(1);
        }
    }
    
    dialog[open]::backdrop {
        animation: fade 0.2s ease-out;
    }
    
    @keyframes fade {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    button.close-btn {
        display: block;
        margin-top: 0.5em;
        padding: 0.25em 0.75em;
        background-color: #4b5563; /* gray-600 */
        color: #f9fafb; /* gray-50 */
        border: none;
        border-radius: 0.2em;
        cursor: pointer;
        font-size: 0.875rem;
    }
    
    button.close-btn:hover {
        background-color: #6b7280; /* gray-500 */
    }
    
    button.close-btn:active {
        background-color: #374151; /* gray-700 */
    }
</style>