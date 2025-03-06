<script lang="ts">
    import Stream from "$lib/Stream.svelte";
    import { Pane, Splitpanes } from "svelte-splitpanes";
    let hue: number = 0;
    let sat: number = 100;
    let light: number = 50;
</script>

<Splitpanes style="height: 92vh">
    <Pane minSize={50}>
        <Stream />
    </Pane>
    <Pane minSize={50}>
        <iframe
            src="http://192.168.2.209:1442/docs"
            style="width: 100%; height: 100%;"
        ></iframe>
    </Pane>
</Splitpanes>
