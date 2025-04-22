import { writable } from 'svelte/store';
export type ToastType = 'information' | 'warning' | 'error';
export interface Toast {
    id: number;
    type: ToastType;
    message: string;
    duration: number;
}
const DEFAULT_DURATION = 3000; // ms
let counter = 0;
export const toastStore = writable<Toast[]>([]);
export function send(type: ToastType, message: string, duration = DEFAULT_DURATION) {
    const id = ++counter;
    toastStore.update((toasts) => [...toasts, { id, type, message, duration }]);
    setTimeout(() => remove(id), duration);
}
export function information(message: string, duration?: number) {
    send('information', message, duration);
}
export function warning(message: string, duration?: number) {
    send('warning', message, duration);
}
export function error(message: string, duration?: number) {
    send('error', message, duration);
}
export function remove(id: number) {
    toastStore.update((toasts) => toasts.filter((t) => t.id !== id));
}
