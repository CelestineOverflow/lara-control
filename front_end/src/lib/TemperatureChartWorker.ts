/// <reference lib="webworker" />
import Chart from "chart.js/auto";
let chart: Chart | null = null;

self.onmessage = (event) => {
  const { data } = event;

  switch (data.type) {
    case "init": {
      if (chart) {
        chart.destroy();
        chart = null;
      }
      const { canvas } = data;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // Create the Chart instance in the Worker
      chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: [],
          datasets: [
            {
              label: "Current",
              data: [],
              backgroundColor: "rgb(255, 255, 255)",
              borderColor: "rgb(255, 255, 255)",
              borderWidth: 1,
              pointRadius: 0,
            },
            {
              label: "Target",
              data: [],
              backgroundColor: "rgba(115, 255, 0, 0.8)",
              borderColor: "rgb(85, 255, 0)",
              borderWidth: 1,
              pointRadius: 0,
            },
          ],
        },
        options: {
          spanGaps: true,
          animation: false,
          responsive: true,   
          maintainAspectRatio: false,
          scales: {
            y: {
              grid: {
                display: true,
                color: "rgba(255, 255, 255, 0.1)",
              },
            },
            x: {
              ticks: {
                display: false,
              },
              grid: {
                display: false,
              }
            },
          },
          plugins: {
            legend: { position: "top" },
            title: { display: false },
          },
        },
      });
      break;
    }

    case "updateData": {
      /**
       * The main thread sends:
       * {
       *   type: "updateData",
       *   payload: { currentForce, targetForce, dataIndex, maxDataPoints }
       * }
       */
      if (!chart) return;

      const { currentForce, targetForce, dataIndex, maxDataPoints } = data.payload;

      // Add new data point
      chart.data.labels?.push(dataIndex.toString());
      chart.data.datasets[0].data.push(currentForce);
      chart.data.datasets[1].data.push(targetForce);

      // Remove old data points in a single splice to avoid memory leaks
      const excess = (chart.data.labels?.length ?? 0) - maxDataPoints;
      if (excess > 0) {
      chart.data.labels?.splice(0, excess);
      chart.data.datasets.forEach(ds => {
        ds.data.splice(0, excess);
      });
      }

      // Trigger a re-draw
      chart.update();
      break;
    }
  }
};
