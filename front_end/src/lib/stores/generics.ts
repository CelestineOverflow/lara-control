import { writable } from 'svelte/store';

export const selected = writable(1);

export const opencv_loaded = writable(false);

export const settings = writable({
    "EnableTranslateControls": false
});
