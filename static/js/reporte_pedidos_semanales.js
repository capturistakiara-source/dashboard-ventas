(function () {
    const raw = document.getElementById("pedidos-data");
    const payload = raw ? JSON.parse(raw.textContent || "{}") : {};
    const weekStarts = payload.week_starts || [];
    const labels = payload.labels || [];
    const series = payload.series || {};

    const selectTipo = document.getElementById("selectTipo");
    const selectSucursales = document.getElementById("selectSucursales");
    const selectSemanas = document.getElementById("selectSemanas");
    const weekSelectionHelp = document.getElementById("weekSelectionHelp");
    const rangoTablaTexto = document.getElementById("rangoTablaTexto");
    const btnUltimas8Semanas = document.getElementById("btnUltimas8Semanas");
    const btnLimpiarSemanas = document.getElementById("btnLimpiarSemanas");

    const canvasTendencia = document.getElementById("graficaTendenciaSemanal");
    const canvasComparativa = document.getElementById("graficaComparativaMarca");
    const tablaBody = document.getElementById("tablaTotalesSemanalesBody");
    const tablaUberFinal = document.getElementById("tablaUberFinal");
    const tablaDidiFinal = document.getElementById("tablaDidiFinal");
    const tablaTotalFinal = document.getElementById("tablaTotalesSemanalesFinal");

    if (
        !selectTipo ||
        !selectSucursales ||
        !selectSemanas ||
        !canvasTendencia ||
        !canvasComparativa ||
        !tablaBody ||
        !tablaUberFinal ||
        !tablaDidiFinal ||
        !tablaTotalFinal
    ) {
        return;
    }

    let chartTendencia = null;
    let chartComparativa = null;
    const branchNames = Object.keys(series);
    const weekLabelByStart = {};

    function formatDate(dateObj) {
        const dd = String(dateObj.getDate()).padStart(2, "0");
        const mm = String(dateObj.getMonth() + 1).padStart(2, "0");
        const yyyy = dateObj.getFullYear();
        return dd + "/" + mm + "/" + yyyy;
    }

    function buildWeekRangeLabel(weekStart) {
        const start = new Date(weekStart + "T00:00:00");
        if (Number.isNaN(start.getTime())) {
            return weekStart;
        }
        const end = new Date(start);
        end.setDate(end.getDate() + 6);
        return formatDate(start) + " - " + formatDate(end);
    }

    weekStarts.forEach(function (start) {
        weekLabelByStart[start] = buildWeekRangeLabel(start);
    });

    function num(value) {
        return Number(value || 0);
    }

    function formatNumber(value) {
        return num(value).toLocaleString("es-MX", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    }

    function getSelectValues(selectEl) {
        return Array.from(selectEl.selectedOptions).map(function (opt) {
            return opt.value;
        });
    }

    function getSelectedWeeks() {
        return getSelectValues(selectSemanas).filter(function (w) {
            return weekStarts.includes(w);
        });
    }

    function getEffectiveBranches() {
        const selected = getSelectValues(selectSucursales).filter(function (name) {
            return branchNames.includes(name);
        });
        return selected.length ? selected : branchNames.slice();
    }

    function getWeekLabel(weekStart) {
        return weekLabelByStart[weekStart] || buildWeekRangeLabel(weekStart);
    }

    function getWeekIndex(weekStart) {
        return weekStarts.indexOf(weekStart);
    }

    function pickValue(branchName, weekIndex, type) {
        const branchData = series[branchName] || { uber: [], didi: [] };
        const uberVal = num(branchData.uber && branchData.uber[weekIndex]);
        const didiVal = num(branchData.didi && branchData.didi[weekIndex]);

        if (type === "uber") {
            return { uber: uberVal, didi: 0, total: uberVal };
        }
        if (type === "didi") {
            return { uber: 0, didi: didiVal, total: didiVal };
        }
        return { uber: uberVal, didi: didiVal, total: uberVal + didiVal };
    }

    function buildColor(index) {
        const palette = [
            "#00d1b2", "#60a5fa", "#f59e0b", "#f472b6", "#22d3ee",
            "#34d399", "#fb7185", "#a78bfa", "#f97316", "#eab308",
            "#4ade80", "#38bdf8", "#c084fc", "#f43f5e", "#2dd4bf"
        ];
        return palette[index % palette.length];
    }

    function buildTrendDatasets(selectedBranches, selectedWeeks, type) {
        return selectedBranches.map(function (branchName, idx) {
            return {
                label: branchName,
                data: selectedWeeks.map(function (weekStart) {
                    const weekIndex = getWeekIndex(weekStart);
                    return weekIndex < 0 ? 0 : pickValue(branchName, weekIndex, type).total;
                }),
                borderColor: buildColor(idx),
                backgroundColor: buildColor(idx),
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 2,
                fill: false
            };
        });
    }

    function buildBrandDatasets(selectedBranches, selectedWeeks, type) {
        const uberTotals = [];
        const didiTotals = [];

        selectedWeeks.forEach(function (weekStart) {
            const weekIndex = getWeekIndex(weekStart);
            let weekUber = 0;
            let weekDidi = 0;

            selectedBranches.forEach(function (branchName) {
                if (weekIndex < 0) {
                    return;
                }
                const branchData = series[branchName] || { uber: [], didi: [] };
                weekUber += num(branchData.uber && branchData.uber[weekIndex]);
                weekDidi += num(branchData.didi && branchData.didi[weekIndex]);
            });

            uberTotals.push(weekUber);
            didiTotals.push(weekDidi);
        });

        if (type === "uber") {
            return [{
                label: "Uber (nivel marca)",
                data: uberTotals,
                borderColor: "#14b8a6",
                backgroundColor: "rgba(20, 184, 166, 0.72)",
                borderWidth: 1
            }];
        }

        if (type === "didi") {
            return [{
                label: "Didi (nivel marca)",
                data: didiTotals,
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245, 158, 11, 0.72)",
                borderWidth: 1
            }];
        }

        return [
            {
                label: "Uber (nivel marca)",
                data: uberTotals,
                borderColor: "#14b8a6",
                backgroundColor: "rgba(20, 184, 166, 0.72)",
                borderWidth: 1
            },
            {
                label: "Didi (nivel marca)",
                data: didiTotals,
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245, 158, 11, 0.72)",
                borderWidth: 1
            }
        ];
    }

    function weekTotalByIndex(idx) {
        return branchNames.reduce(function (acc, branchName) {
            const branchData = series[branchName] || { uber: [], didi: [] };
            return acc + num(branchData.uber && branchData.uber[idx]) + num(branchData.didi && branchData.didi[idx]);
        }, 0);
    }

    function selectLast8WeeksWithData() {
        const options = Array.from(selectSemanas.options);
        if (!options.length) {
            return;
        }

        let selectedIndices = [];
        for (let i = options.length - 1; i >= 0; i -= 1) {
            if (weekTotalByIndex(i) > 0) {
                selectedIndices.push(i);
            }
            if (selectedIndices.length >= 8) {
                break;
            }
        }

        if (!selectedIndices.length) {
            for (let i = Math.max(0, options.length - 8); i < options.length; i += 1) {
                selectedIndices.push(i);
            }
        }

        const selectedSet = new Set(selectedIndices);
        options.forEach(function (opt, idx) {
            opt.selected = selectedSet.has(idx);
        });
        setWeekHelp("");
        renderAll();
    }

    function clearWeekSelection() {
        Array.from(selectSemanas.options).forEach(function (opt) {
            opt.selected = false;
        });
        setWeekHelp("");
        renderAll();
    }

    function updateTableRange(selectedWeeks) {
        if (!rangoTablaTexto) {
            return;
        }
        if (!selectedWeeks.length) {
            rangoTablaTexto.textContent = "Rango en tabla: sin semanas seleccionadas";
            return;
        }
        const text = selectedWeeks.map(getWeekLabel).join(" / ");
        rangoTablaTexto.textContent = "Rango en tabla: " + text;
    }

    function updateTable(selectedBranches, selectedWeeks, type) {
        tablaBody.innerHTML = "";
        updateTableRange(selectedWeeks);

        if (!selectedWeeks.length) {
            const row = document.createElement("tr");
            row.innerHTML = "<td colspan=\"4\" class=\"empty-table-message\">Selecciona semanas para mostrar datos.</td>";
            tablaBody.appendChild(row);
            tablaUberFinal.textContent = "0";
            tablaDidiFinal.textContent = "0";
            tablaTotalFinal.textContent = "0";
            return;
        }

        let finalUber = 0;
        let finalDidi = 0;

        selectedWeeks.forEach(function (weekStart) {
            const weekIndex = getWeekIndex(weekStart);
            let weekUber = 0;
            let weekDidi = 0;

            selectedBranches.forEach(function (branchName) {
                if (weekIndex < 0) {
                    return;
                }
                const values = pickValue(branchName, weekIndex, type);
                weekUber += values.uber;
                weekDidi += values.didi;
            });

            finalUber += weekUber;
            finalDidi += weekDidi;

            const row = document.createElement("tr");
            row.innerHTML = [
                "<td>" + getWeekLabel(weekStart) + "</td>",
                "<td class=\"text-end\">" + formatNumber(weekUber) + "</td>",
                "<td class=\"text-end\">" + formatNumber(weekDidi) + "</td>",
                "<td class=\"text-end\">" + formatNumber(weekUber + weekDidi) + "</td>"
            ].join("");
            tablaBody.appendChild(row);
        });

        tablaUberFinal.textContent = formatNumber(finalUber);
        tablaDidiFinal.textContent = formatNumber(finalDidi);
        tablaTotalFinal.textContent = formatNumber(finalUber + finalDidi);
    }

    function baseChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            resizeDelay: 120,
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: {
                    labels: { color: "#efefef", boxWidth: 24 }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ": " + formatNumber(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: "#d6d6d6", maxRotation: 25, minRotation: 25 },
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
        };
    }

    function renderAll() {
        const type = selectTipo.value;
        const selectedBranches = getEffectiveBranches();
        const selectedWeeks = getSelectedWeeks();
        const xLabels = selectedWeeks.map(getWeekLabel);

        if (chartTendencia) {
            chartTendencia.destroy();
        }
        if (chartComparativa) {
            chartComparativa.destroy();
        }

        chartTendencia = new Chart(canvasTendencia, {
            type: "line",
            data: {
                labels: xLabels,
                datasets: buildTrendDatasets(selectedBranches, selectedWeeks, type)
            },
            options: baseChartOptions()
        });

        chartComparativa = new Chart(canvasComparativa, {
            type: "bar",
            data: {
                labels: xLabels,
                datasets: buildBrandDatasets(selectedBranches, selectedWeeks, type)
            },
            options: baseChartOptions()
        });

        updateTable(selectedBranches, selectedWeeks, type);
    }

    function setWeekHelp(message) {
        if (weekSelectionHelp) {
            weekSelectionHelp.textContent = message || "";
        }
    }

    function createMultiSelectControl(cfg) {
        const root = document.querySelector('[data-control="' + cfg.controlName + '"]');
        if (!root || !cfg.selectEl) {
            return;
        }

        const trigger = root.querySelector("[data-trigger]");
        const label = root.querySelector("[data-label]");
        const panel = root.querySelector("[data-panel]");
        const search = root.querySelector("[data-search]");
        const optionsWrap = root.querySelector("[data-options]");

        function selectedCount() {
            return getSelectValues(cfg.selectEl).length;
        }

        function updateLabel() {
            const count = selectedCount();
            if (cfg.controlName === "sucursales") {
                label.textContent = count ? (count + " seleccionadas") : cfg.placeholder;
                return;
            }
            label.textContent = count ? (count + " seleccionadas") : cfg.placeholder;
        }

        function syncSelect(optionValue, checked) {
            Array.from(cfg.selectEl.options).forEach(function (opt) {
                if (opt.value === optionValue) {
                    opt.selected = checked;
                }
            });
        }

        function renderOptions(filterText) {
            const term = String(filterText || "").trim().toLowerCase();
            const options = Array.from(cfg.selectEl.options);
            optionsWrap.innerHTML = "";

            options.forEach(function (opt) {
                if (term && opt.text.toLowerCase().indexOf(term) === -1) {
                    return;
                }

                const item = document.createElement("label");
                item.className = "multi-select-option";

                const check = document.createElement("input");
                check.type = "checkbox";
                check.checked = opt.selected;
                check.value = opt.value;
                check.addEventListener("change", function () {
                    if (cfg.maxSelections && check.checked) {
                        const currentCount = selectedCount();
                        if (currentCount >= cfg.maxSelections) {
                            check.checked = false;
                            setWeekHelp("Maximo 8 semanas seleccionadas.");
                            return;
                        }
                    }

                    syncSelect(opt.value, check.checked);
                    if (!check.checked) {
                        setWeekHelp("");
                    }
                    updateLabel();
                    cfg.onChange();
                });

                const text = document.createElement("span");
                text.textContent = opt.text;

                item.appendChild(check);
                item.appendChild(text);
                optionsWrap.appendChild(item);
            });
        }

        trigger.addEventListener("click", function () {
            const isOpen = panel.classList.contains("open");
            document.querySelectorAll(".multi-select-panel.open").forEach(function (p) {
                p.classList.remove("open");
            });
            if (!isOpen) {
                panel.classList.add("open");
                if (search) {
                    search.focus();
                }
            }
        });

        if (search) {
            search.addEventListener("input", function () {
                renderOptions(search.value);
            });
        }

        cfg.selectEl.addEventListener("change", function () {
            updateLabel();
            renderOptions(search ? search.value : "");
            cfg.onChange();
        });

        updateLabel();
        renderOptions("");
    }

    document.addEventListener("click", function (event) {
        if (!event.target.closest(".multi-select-control")) {
            document.querySelectorAll(".multi-select-panel.open").forEach(function (p) {
                p.classList.remove("open");
            });
        }
    });

    weekStarts.forEach(function (weekStart, idx) {
        const opt = document.createElement("option");
        opt.value = weekStart;
        opt.textContent = buildWeekRangeLabel(weekStart);
        selectSemanas.appendChild(opt);
    });

    createMultiSelectControl({
        controlName: "sucursales",
        selectEl: selectSucursales,
        placeholder: "Selecciona sucursales",
        maxSelections: 0,
        onChange: renderAll
    });

    createMultiSelectControl({
        controlName: "semanas",
        selectEl: selectSemanas,
        placeholder: "Selecciona semanas",
        maxSelections: 8,
        onChange: renderAll
    });

    if (btnUltimas8Semanas) {
        btnUltimas8Semanas.addEventListener("click", selectLast8WeeksWithData);
    }
    if (btnLimpiarSemanas) {
        btnLimpiarSemanas.addEventListener("click", clearWeekSelection);
    }

    selectTipo.addEventListener("change", renderAll);
    renderAll();
})();
