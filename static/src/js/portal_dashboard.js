import { loadBundle } from "@web/core/assets";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

class TritonDashboardChart extends Interaction {
    static selector = ".o_triton_dashboard-chart";

    async willStart() {
        await loadBundle("web.chartjs_lib");
    }

    start() {
        const labels = JSON.parse(this.el.dataset.chartLabels || "[]");
        const values = JSON.parse(this.el.dataset.chartValues || "[]");
        if (!labels.length || !values.length) {
            return;
        }

        const kind = this.el.dataset.chartKind;
        const horizontal = kind === "cpl";
        const isDistribution = kind === "grades";
        this.chart = new window.Chart(this.el, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: horizontal ? "#F2D15B" : "#123F59",
                    borderRadius: 4,
                    maxBarThickness: 34,
                }],
            },
            options: {
                indexAxis: horizontal ? "y" : "x",
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true },
                },
                scales: horizontal
                    ? {
                        x: { beginAtZero: true, max: 100, ticks: { callback: (value) => `${value}%` } },
                        y: { grid: { display: false } },
                    }
                    : {
                        x: { grid: { display: false } },
                        y: {
                            beginAtZero: true,
                            suggestedMax: isDistribution ? undefined : 100,
                            ticks: { precision: 0 },
                        },
                    },
            },
        });
        this.registerCleanup(() => this.chart.destroy());
    }
}

registry.category("public.interactions").add("erpobe.dashboard_chart", TritonDashboardChart);
