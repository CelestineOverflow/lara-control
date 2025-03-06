<!-- <script lang="ts">
    import { onMount } from "svelte";
    import { basicSetup, EditorView } from "codemirror";
    let editor: EditorView;
    let code = "console.log('hello')\n";
    let parent: HTMLElement;

    onMount(() => {
        editor = new EditorView({
            doc: code,
            extensions: [basicSetup],
            parent,
        });
    });

</script>

<div bind:this={parent}></div> -->