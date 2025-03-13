<script lang="ts">
    export let showModal: boolean;
    let dialog: HTMLDialogElement;
    $: if (dialog && showModal) dialog.showModal();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
<dialog
    bind:this={dialog}
    on:close={() => (showModal = false)}
    on:click|self={() => dialog.close()}
    class="dark-modal"
>
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div on:click|stopPropagation>
        <slot name="header" />
        <slot />
        <!-- svelte-ignore a11y-autofocus -->
        <button autofocus on:click={() => dialog.close()} class="btn btn-soft btn-error">Close</button>
    </div>
</dialog>



<!-- this style  -->


<div role="alert" class="alert alert-info">
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="h-6 w-6 shrink-0 stroke-current">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>
    <span>New software update available.</span>
  </div>

  <div role="alert" class="alert alert-success">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span>Your purchase has been confirmed!</span>
  </div>

  <div role="alert" class="alert alert-warning">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <span>Warning: Invalid email address!</span>
  </div>

  <div role="alert" class="alert alert-error">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span>Error! Task failed successfully.</span>
  </div>


<style>
    dialog {

        border-radius: 0.2em;
        border: none;
        padding: 0;
        background-color: #1f2937; /* gray-800 */
        color: #e5e7eb; /* gray-200 */
        position: fixed;
        top: 50%;
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



