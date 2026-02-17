(function () {
    const raw = document.getElementById("pedidos-data");
    const payload = raw ? JSON.parse(raw.textContent || "{}") : {};
    const labels = payload.labels || [];
    const series = payload.series || {};

    const selectSucursal = document.getElementById("selectSucursal");
    const selectTipo = document.getElementById("selectTipo");
    const canvas = document.getElementById("graficaPedidosSemanales");

    if (!selectSucursal || !selectTipo || !canvas || !labels.length) {
        return;
    }

    let chartPedidos = null;

    function buildDatasets(tipo, dataSucursal) {
        const uber = dataSucursal.uber || [];
        const didi = dataSucursal.didi || [];

        if (tipo === "uber") {
            return [{
                label: "Pedidos Uber",
                data: uber,
                borderColor: "#10b981",
                backgroundColor: "rgba(16, 185, 129, 0.2)",
                tension: 0.3,
                fill: true
            }];
        }

        if (tipo === "didi") {
            return [{
                label: "Pedidos Didi",
                data: didi,
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245, 158, 11, 0.2)",
                tension: 0.3,
                fill: true
            }];
        }

        return [
            {
                label: "Pedidos Uber",
                data: uber,
                borderColor: "#10b981",
                backgroundColor: "rgba(16, 185, 129, 0.2)",
                tension: 0.3,
                fill: false
            },
            {
                label: "Pedidos Didi",
                data: didi,
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245, 158, 11, 0.2)",
                tension: 0.3,
                fill: false
            }
        ];
    }

    function renderChart() {
        const sucursal = selectSucursal.value;
        const tipo = selectTipo.value;
        const dataSucursal = series[sucursal] || { uber: [], didi: [] };
        const datasets = buildDatasets(tipo, dataSucursal);

        if (chartPedidos) {
            chartPedidos.destroy();
        }

        chartPedidos = new Chart(canvas, {
            type: "line",
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false
                },
                plugins: {
                    legend: {
                        labels: { color: "#efefef" }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `${context.dataset.label}: ${Math.round(context.parsed.y)} pedidos`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: "#d6d6d6" },
                        grid: { color: "rgba(255,255,255,0.07)" }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: "#d6d6d6",
                            precision: 0
                        },
                        grid: { color: "rgba(255,255,255,0.07)" }
                    }
                }
            }
        });
    }

    selectSucursal.addEventListener("change", renderChart);
    selectTipo.addEventListener("change", renderChart);
    renderChart();
})();
