<script>
    import { onMount } from "svelte";
    import NavBar from "$lib/NavBar.svelte";
    import "../app.css";
    import { setupSocket } from "$lib/robotics/laraapi";

    onMount(() =>  {
        setupSocket();
    });
</script>

<NavBar />

<slot />

<style>
    @import url("https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap");
</style>