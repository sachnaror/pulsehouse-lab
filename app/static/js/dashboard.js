let trafficChart;

async function getJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to fetch ${url}`);
    }
    return response.json();
}

function renderOverview(data) {
    document.getElementById("totalRequests").textContent = data.total_requests.toLocaleString();
    document.getElementById("errorRate").textContent = `${data.error_rate}%`;
    document.getElementById("avgDuration").textContent = `${data.avg_duration_ms} ms`;
    document.getElementById("peakRpm").textContent = data.peak_rpm;
    document.getElementById("peakWindow").textContent = `peak at ${data.peak_window}`;
    document.getElementById("modeBadge").textContent = data.mode === "clickhouse" ? "Live ClickHouse" : "Sample Mode";
}

function renderChart(rows) {
    const ctx = document.getElementById("trafficChart");
    const labels = rows.map((row) => row.minute);
    const requests = rows.map((row) => row.requests);
    const errors = rows.map((row) => row.errors);

    if (trafficChart) {
        trafficChart.destroy();
    }

    trafficChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Requests",
                    data: requests,
                    borderColor: "#77e0c6",
                    backgroundColor: "rgba(119, 224, 198, 0.16)",
                    tension: 0.35,
                    fill: true,
                },
                {
                    label: "Errors",
                    data: errors,
                    borderColor: "#ff6b6b",
                    backgroundColor: "rgba(255, 107, 107, 0.08)",
                    tension: 0.35,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: "#dbe7f4",
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: "#99a9bc" },
                    grid: { color: "rgba(255,255,255,0.06)" },
                },
                y: {
                    ticks: { color: "#99a9bc" },
                    grid: { color: "rgba(255,255,255,0.06)" },
                },
            },
        },
    });
}

function renderTopEndpoints(rows) {
    const body = document.getElementById("topEndpointsBody");
    body.innerHTML = rows.map((row) => `
        <tr>
            <td>${row.endpoint}</td>
            <td>${row.requests}</td>
            <td>${row.avg_duration_ms}</td>
            <td>${row.server_errors}</td>
        </tr>
    `).join("");
}

function renderAnomalies(rows) {
    const list = document.getElementById("anomalyList");
    list.innerHTML = rows.map((row) => `
        <div class="anomaly-item">
            <strong>${row.service}</strong>
            <div>Latency: ${row.avg_latency_ms} ms</div>
            <div>Error rate: ${row.error_rate}%</div>
        </div>
    `).join("");
}

async function bootstrapDashboard() {
    const [overview, timeseries, endpoints, anomalies, explanation] = await Promise.all([
        getJson("/api/overview"),
        getJson("/api/timeseries"),
        getJson("/api/top-endpoints"),
        getJson("/api/anomalies"),
        getJson("/api/explain"),
    ]);

    renderOverview(overview);
    renderChart(timeseries);
    renderTopEndpoints(endpoints);
    renderAnomalies(anomalies);
    document.getElementById("explanationBox").textContent = explanation.message;
}

bootstrapDashboard().catch((error) => {
    document.getElementById("explanationBox").textContent = error.message;
});
