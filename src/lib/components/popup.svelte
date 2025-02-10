<script>
  import Modal from './Modal.svelte';
  import { error } from '$lib/coordinate';
  let showModal = false;
  error.subscribe((value) => {
    console.log("Error: ", value);
    if (value) {
      showModal = true;
    }
  });
</script>
<Modal bind:showModal>
    <h1>Error ❌</h1>
    <h1>Code: {$error.error_code}</h1>
    <p>{$error.error_message}</p>
</Modal>
<!-- 
<Modal bind:showModal>
    <h1>Success ✅</h1>
    <p>Code: {$error.error_code}</p>
    <p>{$error.error_message}</p>
</Modal> -->