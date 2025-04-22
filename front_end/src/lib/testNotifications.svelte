<script>
import {error, information, warning} from './NotificationsLib'
</script>

<!-- import toast from '$lib/notificationlib.svelte.ts';
// information
toast.information('Data saved successfully!');
// warning
toast.warning('Your session is about to expire.', 5000);
// error
toast.error('Failed to load user profile.'); -->

<button on:click={() => (error("hi", 1000))} class="btn btn-soft btn-primary">error trigger</button>
<button on:click={() => (warning("hi", 1000))} class="btn btn-soft btn-primary">error trigger</button>
<button on:click={() => (information("hi", 1000))} class="btn btn-soft btn-primary">error trigger</button>