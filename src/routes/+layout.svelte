<script>
    import NavBar from "$lib/NavBar.svelte";
    import "../app.css";
</script>

<NavBar />

<slot />

<style>
    @import url("https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap");
</style>
<!-- 
<svelte:head>
    <script src="https://docs.opencv.org/4.5.4/opencv.js" async></script>
</svelte:head> -->