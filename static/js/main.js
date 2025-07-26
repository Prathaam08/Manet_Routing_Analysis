document.getElementById('simForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    // ✅ Get values from all form fields, including the new ones
    const params = {
        num_nodes: document.getElementById('num_nodes').value,
        area: document.getElementById('area').value,
        sim_time: document.getElementById('sim_time').value,
        mobility: document.getElementById('mobility').value,
        traffic_load: document.getElementById('traffic_load').value,
        energy: document.getElementById('energy').value,
        protocol: document.getElementById('protocol').value,
    };

    // Show loading state and clear old results
    document.getElementById('results').style.display = 'block';
    const mlPredictionDiv = document.getElementById('mlPrediction');
    const resultCardsDiv = document.getElementById('resultCards');
    mlPredictionDiv.innerHTML = 'Running simulation, please wait... 🧠';
    resultCardsDiv.innerHTML = '';

    // Send data to backend API
    const response = await fetch('/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
    });
    const data = await response.json();

    // Display results
    mlPredictionDiv.innerHTML = `🤖 <strong>ML Prediction:</strong> The optimal protocol for this scenario is likely <strong>${data.predicted_protocol}</strong>.`;

    for (const proto in data.simulation_results) {
        const result = data.simulation_results[proto];
        let metricsHtml = '<ul>';
        for (const metric in result.metrics) {
            metricsHtml += `<li><strong>${metric}:</strong> ${result.metrics[metric]}</li>`;
        }
        metricsHtml += '</ul>';

        const cardHtml = `
            <div class="col-md-4">
                <div class="card mb-3">
                    <div class="card-header">${proto}</div>
                    <img src="${result.plot_path}?t=${new Date().getTime()}" class="card-img-top" alt="Plot for ${proto}">
                    <div class="card-body">
                        <h5 class="card-title">Performance Metrics</h5>
                        ${metricsHtml}
                    </div>
                </div>
            </div>`;
        resultCardsDiv.innerHTML += cardHtml;
    }
});