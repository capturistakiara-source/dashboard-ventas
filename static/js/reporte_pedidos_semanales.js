(function () {
    const raw = document.getElementById("pedidos-data");
    const payload = raw ? JSON.parse(raw.textContent || "{}") : {};
    const labels = payload.labels || [];
    const series = payload.series || {};

    const selectSucursal = document.getElementById("selectSucursal");
    const selectTipo = document.getElementById("selectTipo");
    const canvas = document.getElementById("graficaPedidosSemanales");
    const tablaTotalesSemanalesBody = document.getElementById("tablaTotalesSemanalesBody");
    const tablaTotalesSemanalesFinal = document.getElementById("tablaTotalesSemanalesFinal");

    if (!selectSucursal || !selectTipo || !canvas || !labels.length) {
        return;
    }

    let chartPedidos = null;
    const branchNames = Object.keys(series);

    function sumArray(values) {
        return (values || []).reduce(function (acc, value) {
            return acc + (value || 0);
        }, 0);
    }

    function formatNumber(value) {
        return (value || 0).toLocaleString("es-MX", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    }

    function getWeeklyTotalsAllBranches() {
        return labels.map(function (_, weekIndex) {
            return branchNames.reduce(function (acc, branchName) {
                const branchData = series[branchName] || { uber: [], didi: [] };
                const uberVal = branchData.uber && branchData.uber[weekIndex] ? branchData.uber[weekIndex] : 0;
                const didiVal = branchData.didi && branchData.didi[weekIndex] ? branchData.didi[weekIndex] : 0;
                return acc + uberVal + didiVal;
            }, 0);
        });
    }

    function renderWeeklyTotalsTable() {
        if (!tablaTotalesSemanalesBody || !tablaTotalesSemanalesFinal) {
            return;
        }

        const weeklyTotals = getWeeklyTotalsAllBranches();
        const totalFinal = sumArray(weeklyTotals);

        tablaTotalesSemanalesBody.innerHTML = "";

        labels.forEach(function (weekLabel, idx) {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${weekLabel}</td>
                <td class="text-end">${formatNumber(weeklyTotals[idx])}</td>
            `;
            tablaTotalesSemanalesBody.appendChild(row);
        });

        tablaTotalesSemanalesFinal.textContent = formatNumber(totalFinal);
    }

    function getTotalsByBranch() {
        return branchNames.map(function (branchName) {
            const branchData = series[branchName] || { uber: [], didi: [] };
            const uberTotal = sumArray(branchData.uber);
            const didiTotal = sumArray(branchData.didi);
            return {
                uber: uberTotal,
                didi: didiTotal,
                total: uberTotal + didiTotal
            };
        });
    }

    function buildAllBranchesDatasets(tipo) {
        const totalsByBranch = getTotalsByBranch();

        if (tipo === "uber") {
            return [{
                label: "Uber (Total del rango)",
                data: totalsByBranch.map(function (item) { return item.uber; }),
                borderColor: "#10b981",
                backgroundColor: "rgba(16, 185, 129, 0.65)",
                borderWidth: 1
            }];
        }

        if (tipo === "didi") {
            return [{
                label: "Didi (Total del rango)",
                data: totalsByBranch.map(function (item) { return item.didi; }),
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245, 158, 11, 0.65)",
                borderWidth: 1
            }];
        }

        return [
            {
                label: "Uber (Total del rango)",
                data: totalsByBranch.map(function (item) { return item.uber; }),
                borderColor: "#10b981",
                backgroundColor: "rgba(16, 185, 129, 0.65)",
                borderWidth: 1
            },
            {
                label: "Didi (Total del rango)",
                data: totalsByBranch.map(function (item) { return item.didi; }),
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245, 158, 11, 0.65)",
                borderWidth: 1
            },
            {
                label: "Total Pedidos (Rango)",
                data: totalsByBranch.map(function (item) { return item.total; }),
                borderColor: "#60a5fa",
                backgroundColor: "rgba(96, 165, 250, 0.65)",
                borderWidth: 1
            }
        ];
    }

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
        const isAllBranches = sucursal === "__todas__";
        const dataSucursal = series[sucursal] || { uber: [], didi: [] };
        const datasets = isAllBranches
            ? buildAllBranchesDatasets(tipo)
            : buildDatasets(tipo, dataSucursal);
        const chartType = isAllBranches ? "bar" : "line";
        const chartLabels = isAllBranches ? branchNames : labels;

        if (chartPedidos) {
            chartPedidos.destroy();
        }

        chartPedidos = new Chart(canvas, {
            type: chartType,
            data: {
                labels: chartLabels,
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
                        stacked: false,
                        ticks: { color: "#d6d6d6" },
                        grid: { color: "rgba(255,255,255,0.07)" }
                    },
                    y: {
                        stacked: false,
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
    renderWeeklyTotalsTable();
    renderChart();
})();
