const socket = io();
let simulationRunning = false;
let charts = {};
let stopSimulationFlag = false;
let currentRunId = null; // store globally in this script

document.addEventListener("DOMContentLoaded", function () {
  // Initialize charts
  charts.pdr = initChart(
    "pdrChart",
    "line",
    "rgba(54, 162, 235, 1)",
    "PDR (%)"
  );
  charts.delay = initChart(
    "delayChart",
    "line",
    "rgba(255, 99, 132, 1)",
    "Delay (ms)"
  );
  charts.throughput = initChart(
    "throughputChart",
    "line",
    "rgba(75, 192, 192, 1)",
    "Throughput (kbps)"
  );
  charts.energy = initChart(
    "energyChart",
    "line",
    "rgba(153, 102, 255, 1)",
    "Energy (J)"
  );
  charts.battery = initChart(
    "batteryChart",
    "doughnut",
    [
      "rgba(75, 192, 192, 0.6)",
      "rgba(54, 162, 235, 0.6)",
      "rgba(255, 206, 86, 0.6)",
      "rgba(255, 99, 132, 0.6)",
    ],
    "Battery Levels"
  );

  // Button handlers
  document
    .getElementById("btnStart")
    .addEventListener("click", startSimulation);
  document.getElementById("btnStop").addEventListener("click", stopSimulation);
  document
    .getElementById("btnPredict")
    .addEventListener("click", predictProtocol);

  // Socket listeners
  socket.on("sim_update", handleSimulationUpdate);
  socket.on("sim_complete", handleSimulationComplete);
  socket.on("sim_error", handleSimulationError);
  socket.on("sim_stopped", handleSimulationStopped);

  // Load history
  fetch("/get_history")
    .then((res) => res.json())
    .then(renderHistory);
});

function initChart(canvasId, type, bgColor, yLabel) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const labelText =
    typeof yLabel !== "undefined" ? yLabel : canvasId.replace("Chart", "");
  return new Chart(ctx, {
    type: type,
    data: {
      labels: [],
      datasets: [
        {
          label: labelText,
          data: [],
          backgroundColor: Array.isArray(bgColor) ? bgColor : bgColor,
          borderColor: Array.isArray(bgColor)
            ? bgColor.map((c) => {
                try {
                  return c.replace("0.6", "1");
                } catch (e) {
                  return c;
                }
              })
            : bgColor,
          borderWidth: 2,
          fill : false,
          tension: 0.4, // smoother curves (0.4 is natural-looking)
          showLine: true, // ensures curves render even with numeric x values
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 200 },
      scales:
        type !== "doughnut"
          ? {
              x: {
                type: "linear",
                position: "bottom",
                title: { display: true, text: "Time (s)" },
                min: 0,
              },
              y: {
                beginAtZero: true,
                title: { display: true, text: labelText },
              },
            }
          : {},
      plugins: {
        legend: { display: type === "doughnut" },
        tooltip: { mode: "index", intersect: false },
      },
    },
  });
}

function startSimulation() {
  if (simulationRunning) return;

  const config = {
    protocol: document.getElementById("protocol").value,
    numNodes: +document.getElementById("numNodes").value,
    simTime: +document.getElementById("simTime").value,
    areaSize: 1000,
    nodeSpeed: +document.getElementById("nodeSpeed").value,
    txRange: +document.getElementById("txRange").value,
    pauseTime: +document.getElementById("pauseTime").value,
    trafficLoad: +document.getElementById("trafficLoad").value,
  };

  simulationRunning = true;
  stopSimulationFlag = false;

  document.getElementById("btnStart").disabled = true;
  document.getElementById("btnStop").disabled = false;

  // Reset charts
  Object.values(charts).forEach((chart) => {
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    if (chart.options.scales?.x) {
      chart.options.scales.x.suggestedMax = config.simTime;
    }
    chart.update();
  });

  fetch("/start_simulation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  })
    .then((res) => res.json())
    .then((data) => {
      // server returns { status: 'started', run_id: '...' }
      window.currentRunId = data.run_id;
      console.log("Started run", window.currentRunId);
    })
    .catch((err) => {
      console.error("Error starting simulation:", err);
      simulationRunning = false;
      document.getElementById("btnStart").disabled = false;
    });
}

function stopSimulation() {
  stopSimulationFlag = true;
  fetch("/stop_simulation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  }).then(() => {
    document.getElementById("btnStop").disabled = true;
    simulationRunning = false;
    document.getElementById("btnStart").disabled = false;
  });
}

function predictProtocol() {
  const params = {
    numNodes: +document.getElementById("numNodes").value,
    nodeSpeed: +document.getElementById("nodeSpeed").value,
    areaSize: 1000,
    trafficLoad: +document.getElementById("trafficLoad").value,
    txRange: +document.getElementById("txRange").value,
  };

  fetch("/predict_protocol", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
    .then((res) => res.json())
    .then((data) => {
      document.getElementById("predictionResult").innerHTML = `
                Recommended protocol: <strong>${data.protocol}</strong>
                (Confidence: ${(data.confidence * 100).toFixed(1)}%)
                <button class="btn btn-sm btn-success ms-2"
                        onclick="document.getElementById('protocol').value='${
                          data.protocol
                        }'">
                    Use This
                </button>
            `;
    });
}

function handleSimulationUpdate(data) {
  // if run_id present and not equal to current, ignore update
  if (
    window.currentRunId &&
    data.run_id &&
    data.run_id !== window.currentRunId
  ) {
    // stale update, ignore
    return;
  }
  if (data.type === "metrics") {
    updateChart(charts.pdr, data.time, data.pdr);
    updateChart(charts.delay, data.time, data.delay);
    updateChart(charts.throughput, data.time, data.throughput);
    updateChart(charts.energy, data.time, data.energy);
    updateBatteryChart(charts.battery, data.nodes);
    updateNetworkVisualization(data);
  }
}

function handleSimulationComplete(data) {
  simulationRunning = false;
  document.getElementById("btnStart").disabled = false;
  document.getElementById("btnStop").disabled = true;
  renderHistoryItem(data);
}

function handleSimulationError(data) {
  console.error("Simulation error:", data.error);
  alert(`Simulation error: ${data.error}`);
  simulationRunning = false;
  document.getElementById("btnStart").disabled = false;
  document.getElementById("btnStop").disabled = true;
}

function handleSimulationStopped(data) {
  console.log("Simulation stopped:", data.message);
  simulationRunning = false;
  document.getElementById("btnStart").disabled = false;
  document.getElementById("btnStop").disabled = true;
}

function updateChart(chart, label, value) {
  // ensure label is numeric (safe fallback)
  const t = typeof label === "number" ? label : Number(label) || 0;

  if (chart.data.labels.length >= 100) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }

  chart.data.labels.push(Number(t.toFixed ? t.toFixed(1) : t));
  chart.data.datasets[0].data.push(value === undefined ? null : value);

  // If x-scale present, update suggestedMax defensively
  if (chart.options.scales && chart.options.scales.x && typeof t === "number") {
    if (t > (chart.options.scales.x.suggestedMax || 0)) {
      chart.options.scales.x.suggestedMax = Math.ceil(t / 10) * 10;
    }
  }

  chart.update();
}

function updateBatteryChart(chart, nodes = []) {
  const energyLevels = {
    high: nodes.filter((n) => n.energy > 70).length,
    medium: nodes.filter((n) => n.energy > 30 && n.energy <= 70).length,
    low: nodes.filter((n) => n.energy > 10 && n.energy <= 30).length,
    critical: nodes.filter((n) => n.energy <= 10).length,
  };

  chart.data.datasets[0].data = [
    energyLevels.high,
    energyLevels.medium,
    energyLevels.low,
    energyLevels.critical,
  ];
  chart.update();
}

function updateNetworkVisualization(data) {
  const container = document.getElementById("network-canvas");
  const width = container.clientWidth;
  const height = container.clientHeight;

  const svg = d3
    .select("#network-canvas")
    .selectAll("svg")
    .data([null])
    .join("svg")
    .attr("width", width)
    .attr("height", height);

  const xScale = d3
    .scaleLinear()
    .domain([0, data.areaSize[0]])
    .range([50, width - 50]);
  const yScale = d3
    .scaleLinear()
    .domain([0, data.areaSize[1]])
    .range([50, height - 50]);

  svg
    .selectAll(".link")
    .data(data.links)
    .join("line")
    .attr("class", "link")
    .attr("x1", (d) => xScale(data.nodes.find((n) => n.id === d.source).x))
    .attr("y1", (d) => yScale(data.nodes.find((n) => n.id === d.source).y))
    .attr("x2", (d) => xScale(data.nodes.find((n) => n.id === d.target).x))
    .attr("y2", (d) => yScale(data.nodes.find((n) => n.id === d.target).y))
    .attr("stroke", "#999")
    .attr("stroke-width", 1.5);

  const node = svg
    .selectAll(".node")
    .data(data.nodes, (d) => d.id)
    .join("g")
    .attr("class", "node")
    .attr("transform", (d) => `translate(${xScale(d.x)},${yScale(d.y)})`);

  node
    .selectAll("circle")
    .data((d) => [d])
    .join("circle")
    .attr("r", 10)
    .attr("fill", (d) =>
      d.energy > 70 ? "#4CAF50" : d.energy > 30 ? "#FFC107" : "#F44336"
    )
    .attr("stroke", "#333")
    .attr("stroke-width", 1);

  node
    .selectAll("text")
    .data((d) => [d])
    .join("text")
    .attr("dy", 4)
    .attr("text-anchor", "middle")
    .attr("font-size", "10px")
    .attr("fill", "white")
    .text((d) => d.id);
}

function renderHistory(simulations) {
  const historyList = document.getElementById("historyList");
  historyList.innerHTML = "";
  simulations.forEach(renderHistoryItem);
}

function renderHistoryItem(sim) {
  const historyList = document.getElementById("historyList");
  const item = document.createElement("div");
  item.className = "list-group-item simulation-card";
  item.innerHTML = `
        <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1 protocol">${sim.protocol}</h5>
            <small>${sim.timestamp}</small>
        </div>
        <div class="metrics">
            <span>PDR: ${sim.pdr.toFixed(2)}</span>
            <span>Delay: ${sim.avg_delay.toFixed(2)} ms</span>
            <span>Throughput: ${sim.throughput.toFixed(2)} kbps</span>
        </div>
    `;
  historyList.insertBefore(item, historyList.firstChild);
}
