<script lang="ts">
    import Chart from "chart.js/auto";
    import { onMount } from "svelte";
    // import { loadcell_value } from "$lib/stores/serial";
    import { loadcell_value } from "$lib/coordinate";
    let canvas: HTMLCanvasElement;
    let chart: Chart;
    let dataIndex = 0;
    const MAX_DATA_POINTS = 100; // Limit the number of data points
    let current_pressure_in_grams = 0.0;
    let target_pressure_in_grams = 0.0;
  
    onMount(() => {
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        console.error("Could not get canvas context");
        return;
      }
      chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: [],
          datasets: [
            {
              label: "Current",
              data: [] as number[],
              backgroundColor: "rgba(255, 99, 132, 0.5)",
              borderColor: "rgba(255, 99, 132, 1)",
              borderWidth: 4,
              pointRadius: 0, // Optional: Remove data point circles
            },
            {
              label: "Target",
              data: [] as number[],
              backgroundColor: "rgba(54, 162, 235, 0.5)",
              borderColor: "rgba(54, 162, 235, 1)",
              borderWidth: 4,
              pointRadius: 0, // Optional: Remove data point circles
            },
          ],
        },
        options: {
          
          animation: {
            duration: 0, // Disable animations
          },
          responsive: true,
          maintainAspectRatio: false, // Allow the chart to fill its container
          scales: {
            y: {
              grid: {
                display: true,
                color: "rgba(255, 255, 255, 0.1)",
              },
            },
            
          },
          plugins: {
            legend: {
              position: "top",
            },
            title: {
              display: false,
            },
          },
  
        },
      });
  
      const updateChart = (currentForce: number, targetForce: number) => {
        current_pressure_in_grams = currentForce;
        target_pressure_in_grams = targetForce;
        // Add new data point
        if (chart.data.labels) {
          chart.data.labels.push(dataIndex.toString());
        }
        chart.data.datasets[0].data.push(currentForce);
        chart.data.datasets[1].data.push(targetForce);
  
        // Remove old data points if limit is exceeded
        if (chart.data.labels && chart.data.labels.length > MAX_DATA_POINTS) {
          chart.data.labels.shift();
          chart.data.datasets[0].data.shift();
          chart.data.datasets[1].data.shift();
        }
  
        chart.update();
        dataIndex++;
      };
  
    //   Subscribe to the loadcell_value store
      const unsubscribe = loadcell_value.subscribe((value) => {
        let tempTarget_pressure = value;
        let tempCurrentForce = value;
  
        if (isNaN(tempTarget_pressure) || isNaN(tempCurrentForce)) {
          return;
        }
  
        updateChart(tempCurrentForce, tempTarget_pressure);
      });
  
      return () => {
        chart.destroy();
        unsubscribe(); // Unsubscribe from the store when the component is destroyed
      };
    });
  </script>
  
  <div class="bg-gray-800 text-white h-full flex flex-col p-4 round">
      <h2 class="text-2xl text-white font-bold text-right">Force </h2>
      <h2 class="text-xl text-gray-400 font-bold text-right">Current: {current_pressure_in_grams.toFixed(0)} g | Preset: {target_pressure_in_grams.toFixed(0)} g</h2>
      <canvas bind:this={canvas}></canvas>
  </div>