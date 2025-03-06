<script>
    import Simulation from "$lib/Simulation.svelte";
    import { selected } from "$lib/stores/generics";
    let menu = 1;
    selected.subscribe((value) => {
      menu = value;
    });
  </script>
  
  <Simulation />