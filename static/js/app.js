const socket = io();
let simulationRunning = false;
let charts = {};
let stop_simulation = false;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    charts.pdr = initChart('pdrChart', 'line', 'rgba(54, 162, 235, 1)');
    charts.delay = initChart('delayChart', 'line', 'rgba(255, 99, 132, 1)');
    charts.throughput = initChart('throughputChart', 'line', 'rgba(75, 192, 192, 1)');
    charts.energy = initChart('energyChart', 'line', 'rgba(153, 102, 255, 1)');
    charts.battery = initChart('batteryChart', 'doughnut', [
        'rgba(75, 192, 192, 0.6)',
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(255, 99, 132, 0.6)'
    ]);
    
    // Button handlers
    document.getElementById('btnStart').addEventListener('click', startSimulation);
    document.getElementById('btnStop').addEventListener('click', stopSimulation);
    document.getElementById('btnPredict').addEventListener('click', predictProtocol);
    
    // Socket listeners
    socket.on('sim_update', handleSimulationUpdate);
    socket.on('sim_complete', handleSimulationComplete);
    socket.on('sim_error', handleSimulationError);
    socket.on('sim_stopped', handleSimulationStopped);
    
    // Load history
    fetch('/get_history')
        .then(response => response.json())
        .then(renderHistory);
});

function initChart(canvasId, type, bgColor) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: type,
        data: {
            labels: [],
            datasets: [{
                label: canvasId.replace('Chart', ''),
                data: [],
                backgroundColor: Array.isArray(bgColor) ? bgColor : bgColor,
                borderColor: Array.isArray(bgColor) ? bgColor.map(c => c.replace('0.6', '1')) : bgColor,
                borderWidth: 1,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,  // This is crucial
            animation: {
                duration: 200
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'Time (s)'
                    },
                    min: 0,
                    suggestedMax: 60
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: canvasId.replace('Chart', '')
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });
}

function startSimulation() {
    if (simulationRunning) return;

         document.getElementById('btnStart').disabled = true;

    const config = {
        protocol: document.getElementById('protocol').value,
        numNodes: parseInt(document.getElementById('numNodes').value),
        simTime: parseInt(document.getElementById('simTime').value),
        areaSize: 1000,
        nodeSpeed: parseInt(document.getElementById('nodeSpeed').value),
        txRange: parseInt(document.getElementById('txRange').value),
        pauseTime: parseInt(document.getElementById('pauseTime').value),
        trafficLoad: parseInt(document.getElementById('trafficLoad').value)
    };
    
    simulationRunning = true;
    document.getElementById('btnStart').disabled = true;
    document.getElementById('btnStop').disabled = false;
    
    // Reset charts
    Object.values(charts).forEach(chart => {
        chart.data.labels = [];
        chart.data.datasets[0].data = [];
        chart.options.scales.x.suggestedMax = config.simTime;
        chart.update();
    });
    
    // Send request to backend
    fetch('/start_simulation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(config)
    })
    .catch(error => {
        console.error('Error starting simulation:', error);
        simulationRunning = false;
        document.getElementById('btnStart').disabled = false;
    });
}

function stopSimulation() {
    stop_simulation = true;
    fetch('/stop_simulation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(() => {
        document.getElementById('btnStop').disabled = true;
        simulationRunning = false;
        document.getElementById('btnStart').disabled = false;
    });
}

function predictProtocol() {
    const params = {
        numNodes: parseInt(document.getElementById('numNodes').value),
        nodeSpeed: parseInt(document.getElementById('nodeSpeed').value),
        areaSize: 1000,
        trafficLoad: parseInt(document.getElementById('trafficLoad').value),
        txRange: parseInt(document.getElementById('txRange').value)
    };
    
    fetch('/predict_protocol', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(params)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('predictionResult').innerHTML = `
            Recommended protocol: <strong>${data.protocol}</strong>
            <button class="btn btn-sm btn-success ms-2" 
                    onclick="document.getElementById('protocol').value='${data.protocol}'">
                Use This
            </button>
        `;
    });
}

function handleSimulationUpdate(data) {
    if (data.type === 'metrics') {
        updateChart(charts.pdr, data.time, data.pdr);
        updateChart(charts.delay, data.time, data.delay);
        updateChart(charts.throughput, data.time, data.throughput);
        updateChart(charts.energy, data.time, data.energy);
        
        // Update network visualization
        updateNetworkVisualization(data);
        
        // Update battery chart
        updateBatteryChart(charts.battery, data.nodes);
    }
}

function handleSimulationComplete(data) {
    simulationRunning = false;
    document.getElementById('btnStart').disabled = false;
    document.getElementById('btnStop').disabled = true;
    
    // Add to history
    renderHistoryItem(data);
}

function handleSimulationError(data) {
    console.error("Simulation error:", data.error);
    simulationRunning = false;
    document.getElementById('btnStart').disabled = false;
    document.getElementById('btnStop').disabled = true;
    alert(`Simulation error: ${data.error}`);
}

function handleSimulationStopped(data) {
    console.log("Simulation stopped:", data.message);
    simulationRunning = false;
    document.getElementById('btnStart').disabled = false;
    document.getElementById('btnStop').disabled = true;
}

function updateChart(chart, time, value) {
    // Limit to 100 data points
    if (chart.data.labels.length >= 100) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    
    // Add new data
    chart.data.labels.push(time.toFixed(1));
    chart.data.datasets[0].data.push(value);
    
    // Update X-axis max if needed
    if (time > chart.options.scales.x.suggestedMax) {
        chart.options.scales.x.suggestedMax = Math.ceil(time / 10) * 10;
    }
    
    chart.update();
}

function updateBatteryChart(chart, nodes) {
    const energyLevels = {
        high: nodes.filter(n => n.energy > 70).length,
        medium: nodes.filter(n => n.energy > 30 && n.energy <= 70).length,
        low: nodes.filter(n => n.energy > 10 && n.energy <= 30).length,
        critical: nodes.filter(n => n.energy <= 10).length
    };
    
    chart.data.datasets[0].data = [
        energyLevels.high,
        energyLevels.medium,
        energyLevels.low,
        energyLevels.critical
    ];
    
    chart.update();
}

function updateNetworkVisualization(data) {
    const container = document.getElementById('network-canvas');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Clear existing visualization
    d3.select("#network-canvas").selectAll("*").remove();
    
    const svg = d3.select("#network-canvas")
        .append("svg")
        .attr("width", width)
        .attr("height", height);
    
    // Scale positions to fit container
    const xScale = d3.scaleLinear()
        .domain([0, data.areaSize[0]])
        .range([50, width - 50]);
    
    const yScale = d3.scaleLinear()
        .domain([0, data.areaSize[1]])
        .range([50, height - 50]);
    
    // Draw links
    svg.selectAll(".link")
        .data(data.links)
        .enter()
        .append("line")
        .attr("class", "link")
        .attr("x1", d => xScale(data.nodes.find(n => n.id === d.source).x))
        .attr("y1", d => yScale(data.nodes.find(n => n.id === d.source).y))
        .attr("x2", d => xScale(data.nodes.find(n => n.id === d.target).x))
        .attr("y2", d => yScale(data.nodes.find(n => n.id === d.target).y))
        .attr("stroke", "#999")
        .attr("stroke-width", 1.5);
    
    // Draw nodes
    const node = svg.selectAll(".node")
        .data(data.nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${xScale(d.x)},${yScale(d.y)})`);
    
    node.append("circle")
        .attr("r", 10)
        .attr("fill", d => {
            if (d.energy > 70) return "#4CAF50"; // Green
            if (d.energy > 30) return "#FFC107"; // Yellow
            return "#F44336"; // Red
        })
        .attr("stroke", "#333")
        .attr("stroke-width", 1);
    
    node.append("text")
        .attr("dy", 4)
        .attr("text-anchor", "middle")
        .attr("font-size", "10px")
        .attr("fill", "white")
        .text(d => d.id);
}

function renderHistory(simulations) {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '';
    
    simulations.forEach(sim => {
        const item = document.createElement('div');
        item.className = 'list-group-item simulation-card';
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
        historyList.appendChild(item);
    });
}

function renderHistoryItem(sim) {
    const historyList = document.getElementById('historyList');
    const item = document.createElement('div');
    item.className = 'list-group-item simulation-card';
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