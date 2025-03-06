<script lang="ts">
    import { Pane, Splitpanes } from "svelte-splitpanes";
    import Editor from "$lib/editor.svelte";
    import ProcessesManager from "$lib/ProcessesManager.svelte";
    import FileManager from "$lib/FileManager.svelte";
    import Terminal from "$lib/Terminal.svelte";
</script>

<Splitpanes style="height: 400px">
    <Pane minSize={15}>
        <FileManager />
    </Pane>
    <Pane minSize={20}>
        <Editor />
    </Pane>
    <Pane minSize={20}>
        <Terminal />
    </Pane>
    <Pane minSize={15}>
        <ProcessesManager />
    </Pane>
</Splitpanes>
