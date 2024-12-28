<script>
  import { selected } from "$lib/stores/generics";
  let menu = 1;
  selected.subscribe((value) => {
    menu = value;
  });
</script>