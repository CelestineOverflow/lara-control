/// <reference lib="webworker" />

import Chart from "chart.js/auto"; // adjust import if needed

let chart: Chart | null = null;

self.onmessage = (event) => {
  const { data } = event;

  switch (data.type) {
    case "init": {
      /**
       * The main thread sends:
       * { type: "init", canvas: offscreenCanvas }
       */
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
              backgroundColor: "rgba(105, 135, 255, 0.8)",
              borderColor: "rgba(105, 135, 255, 1)",
              borderWidth: 4,
              pointRadius: 0,
            },
            {
              label: "Target",
              data: [],
              backgroundColor: "rgba(182, 105, 255, 0.8)",
              borderColor: "rgba(182, 105, 255, 1)",
              borderWidth: 4,
              pointRadius: 0,
            },
          ],
        },
        options: {
          spanGaps: true,
          animation: false,
          responsive: false,   // OffscreenCanvas won't auto-resize
          maintainAspectRatio: false,
          scales: {
            y: {
              grid: {
                display: true,
                color: "rgba(255, 255, 255, 0.1)",
              },
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
      if (chart.data.labels) {
        chart.data.labels.push(dataIndex.toString());
      }
      chart.data.datasets[0].data.push(currentForce);
      chart.data.datasets[1].data.push(targetForce);

      // Remove old data points if limit is exceeded
      if (chart.data.labels && chart.data.labels.length > maxDataPoints) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
        chart.data.datasets[1].data.shift();
      }

      // Trigger a re-draw
      chart.update();
      break;
    }
  }
};
