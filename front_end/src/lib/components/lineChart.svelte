<script lang="ts">
    import Chart from 'chart.js/auto';
    import { onMount, onDestroy } from 'svelte';

    let canvas : HTMLCanvasElement;
    let chart : Chart;

    export let MAX_DATA_POINTS : number = 10;

    function randColor() {
        return '#' + Math.floor(Math.random()*16777215).toString(16);
    }

    export let data = {
        labels: ['9'],
        datasets: [{
            label: 'My First Dataset',
            data: [65],
            fill: false,
            borderColor: randColor(),
            tension: 0.1
        }, {
            label: 'My Second Dataset',
            data: [65],
            fill: false,
            borderColor: randColor(),
            tension: 0.1
        }]
    };

    export function addData(dataPoint : {label?: string, values: [number]}) {
        if (!dataPoint){
            console.error('No data point provided');
            return;
        }
        if (!dataPoint.values){
            console.error('No values provided');
            return;
        }
        if (data.labels.length >= MAX_DATA_POINTS) {
            console.log('Max data points reached');
            if (dataPoint.label){
                data.labels.shift();
                data.labels.push(dataPoint.label);
            }
            
            data.datasets[0].data.shift();
            data.datasets[0].data.push(dataPoint.value);
        }else{
            if (dataPoint.label){
                data.labels.push(dataPoint.label);
            }
            data.datasets[0].data.push(dataPoint.value);
            
        }
        chart.update();
    }

    onMount(() => {
        const ctx :any = canvas.getContext('2d');
        if (!ctx) {
            console.error('Could not get canvas context');
            return;
        }
        chart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,

            }
        });

        return () => {
            chart.destroy();
        };
    });

    onDestroy(() => {
        if (chart) {
            chart.destroy();
        }
    });
</script>

<style>
    canvas {
        width: 100%;
        height: 100%;
    }

    .chart-container {
        position: relative;
        width: 100%;
        height: 400px; /* Adjust the height as needed */
    }
</style>

<div class="chart-container">
    <canvas bind:this={canvas}></canvas>
</div>