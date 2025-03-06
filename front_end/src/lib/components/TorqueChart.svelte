<script lang="ts">
    import { onMount } from 'svelte';
    import { torques } from '$lib/coordinate';
    import Chart from "chart.js/auto";
    
    let canvas: HTMLCanvasElement;
    let chart: Chart;
    let torques_arr = [0, 0, 0, 0, 0, 0];

    onMount(() => {
        const ctx = canvas.getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Torque 1', 'Torque 2', 'Torque 3', 'Torque 4', 'Torque 5', 'Torque 6'],
                datasets: [{
                    label: 'Torque Values',
                    backgroundColor: 'rgb(255, 99, 132)',
                    borderColor: 'rgb(255, 99, 132)',
                    data: torques_arr
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Torque'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Value'
                        },
                        min: -100,
                        max: 100
                    }
                }
            }
        });
    });

    torques.subscribe((value) => {
        torques_arr = value;
        if (chart) {
            chart.data.datasets[0].data = torques_arr;
            chart.update();
        }
    });
</script>

<h1> Torque Chart </h1>
<ul>
    <li> Torque 1: {torques_arr[0]} </li>
    <li> Torque 2: {torques_arr[1]} </li>
    <li> Torque 3: {torques_arr[2]} </li>
    <li> Torque 4: {torques_arr[3]} </li>
    <li> Torque 5: {torques_arr[4]} </li>
    <li> Torque 6: {torques_arr[5]} </li>
</ul>
<canvas bind:this={canvas} />