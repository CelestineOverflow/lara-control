<script lang="ts">
    import { onMount } from 'svelte';

    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D | null;
    let resolution = '';

    export function resizeCanvas() {
        if (canvas && canvas.parentElement) {
            // Get parent's dimensions.
            const { width, height } = canvas.parentElement.getBoundingClientRect();
            canvas.width = width;
            canvas.height = height;

            // Update resolution text.
            resolution = `Width: ${Math.round(width)} px, Height: ${Math.round(height)} px`;

            if (ctx) {
                // Fill the canvas with red.
                ctx.fillStyle = 'red';
                ctx.fillRect(0, 0, width, height);
                
                // Draw resolution text.
                ctx.font = '20px sans-serif';
                ctx.fillStyle = 'black';
                ctx.fillText(resolution, 10, 30);
            }
        }
    }

    onMount(() => {
        ctx = canvas.getContext('2d');
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Run resizeCanvas every 1 second on a loop.
        const intervalId = setInterval(resizeCanvas, 1000);

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            clearInterval(intervalId);
        };
    });
</script>

<style>
    canvas {
        border: 1px solid black;
        display: block;
        width: 100%;
        aspect-ratio: 16 / 9; /* Maintain a 16:9 aspect ratio */
    }
</style>

<canvas bind:this={canvas}></canvas>