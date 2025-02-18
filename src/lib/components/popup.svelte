<script>
  import Modal from './Modal.svelte';
  import { error, warning } from '$lib/coordinate';
  let error_showModal = false;
  let warning_showModal = false;
  error.subscribe((value) => {
    if (value) {
      error_showModal = true;
    }
  });
  warning.subscribe((value) => {
    if (value) {
      warning_showModal = true;
    }
  });

</script>
<Modal bind:showModal={error_showModal}>
    <h1>Error ❌</h1>
    <h1>Code: {$error.error_code}</h1>
    <p>{$error.error_message}</p>
</Modal>


<Modal bind:showModal={warning_showModal}>
    <h1>Warning ⚠️</h1>
    <h1>Code: {$warning.warning_code}</h1>
    <p>{$warning.warning_message}</p>
</Modal>