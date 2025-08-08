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
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
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
                    }
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
                }
            }
        }
    });
}

function updateChart(chart, label, value) {
    if (chart.data.labels.length > 50) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    
    chart.data.labels.push(label.toFixed(1));
    chart.data.datasets[0].data.push(value);
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