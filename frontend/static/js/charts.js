/**
 * charts.js — Graphiques Chart.js
 * Dashboard, comparaison algorithmes, utilisation machines
 */

// ── Defaults Chart.js ──────────────────────────────────────────────────────
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748B';
Chart.defaults.plugins.legend.position = 'bottom';
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.plugins.legend.labels.usePointStyle = true;

const PALETTE = {
  accent:  '#2563EB',
  violet:  '#7C3AED',
  success: '#16A34A',
  warning: '#D97706',
  danger:  '#DC2626',
  gray:    '#94A3B8',
  cyan:    '#0891B2',
  pink:    '#D946EF',
};

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ══════════════════════════════════════════════════════════════════════════
// DASHBOARD CHARTS
// ══════════════════════════════════════════════════════════════════════════
const DashboardCharts = {
  jobsChart: null,
  machineChart: null,

  // ── Jobs Status Doughnut ───────────────────────────────────────────────
  async loadJobsStatus() {
    const jobs = await API.get('/api/jobs');
    this.updateJobsStatus(jobs);
  },

  updateJobsStatus(jobs) {
    const counts = {
      'En attente': 0,
      'En cours': 0,
      'Terminé': 0,
      'Retard': 0,
    };
    jobs.forEach(j => {
      if (j.statut === 'en_attente') counts['En attente']++;
      else if (j.statut === 'en_cours') counts['En cours']++;
      else if (j.statut === 'terminé') counts['Terminé']++;
      else if (j.statut === 'retard') counts['Retard']++;
      else counts['En attente']++;
    });

    const ctx = document.getElementById('chart-jobs-status');
    if (!ctx) return;

    if (this.jobsChart) this.jobsChart.destroy();
    this.jobsChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(counts),
        datasets: [{
          data: Object.values(counts),
          backgroundColor: [
            hexToRgba(PALETTE.gray, 0.8),
            hexToRgba(PALETTE.accent, 0.85),
            hexToRgba(PALETTE.success, 0.85),
            hexToRgba(PALETTE.danger, 0.85),
          ],
          borderColor: ['#fff', '#fff', '#fff', '#fff'],
          borderWidth: 3,
          hoverOffset: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: { position: 'right' },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.label}: ${ctx.raw} (${Math.round(ctx.raw / (ctx.chart.data.datasets[0].data.reduce((a,b)=>a+b,0) || 1) * 100)}%)`
            }
          }
        }
      }
    });
  },

  // ── Machine Utilization Bar ────────────────────────────────────────────
  async updateMachineUtil(kpis) {
    const ctx = document.getElementById('chart-machine-util');
    if (!ctx) return;

    // Get latest planning machine util
    const plannings = await API.get('/api/plannings');
    if (!plannings.length) return;

    // Use kpis object if it has utilisation_machines, otherwise fetch schedule
    // We'll do a quick compare call to get util data per machine
    let labels = [];
    let values = [];

    try {
      const result = await API.post('/api/schedule', { algorithme: plannings[0].algorithme.toLowerCase() });
      if (result.utilisation_machines) {
        labels = Object.keys(result.utilisation_machines);
        values = Object.values(result.utilisation_machines);
      }
    } catch {
      // fallback: show empty
    }

    if (this.machineChart) this.machineChart.destroy();
    this.machineChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Utilisation (%)',
          data: values,
          backgroundColor: values.map(v =>
            v >= 80 ? hexToRgba(PALETTE.danger, 0.8) :
            v >= 60 ? hexToRgba(PALETTE.warning, 0.8) :
            hexToRgba(PALETTE.accent, 0.8)
          ),
          borderColor: values.map(v =>
            v >= 80 ? PALETTE.danger :
            v >= 60 ? PALETTE.warning :
            PALETTE.accent
          ),
          borderWidth: 2,
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { callback: v => `${v}%` },
            grid: { color: '#F1F5F9' },
          },
          x: { grid: { display: false } }
        },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => ` Utilisation: ${ctx.raw}%` } }
        }
      }
    });
  },
};

// ══════════════════════════════════════════════════════════════════════════
// COMPARE CHARTS
// ══════════════════════════════════════════════════════════════════════════
const Compare = {
  makespanChart: null,
  retardChart: null,
  radarChart: null,

  async run() {
    document.getElementById('compare-loading').classList.remove('hidden');
    document.getElementById('compare-results').classList.add('hidden');

    try {
      const data = await API.post('/api/compare', {});
      this.displayResults(data);
    } catch (e) {
      App.toast('Erreur lors de la comparaison', 'error');
    } finally {
      document.getElementById('compare-loading').classList.add('hidden');
    }
  },

  displayResults(data) {
    document.getElementById('compare-results').classList.remove('hidden');

    const algos = Object.keys(data);
    const makespans = algos.map(a => data[a].makespan || 0);
    const retards = algos.map(a => data[a].taux_retard || 0);
    const utils = algos.map(a => data[a].utilisation_moy || 0);

    const colors = [
      hexToRgba(PALETTE.accent, 0.8),
      hexToRgba(PALETTE.warning, 0.8),
      hexToRgba(PALETTE.success, 0.8),
      hexToRgba(PALETTE.violet, 0.8),
    ];
    const borders = [PALETTE.accent, PALETTE.warning, PALETTE.success, PALETTE.violet];

    // ── Makespan Bar ─────────────────────────────────────────────────────
    const ctx1 = document.getElementById('chart-compare-makespan');
    if (this.makespanChart) this.makespanChart.destroy();
    this.makespanChart = new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: algos,
        datasets: [{
          label: 'Makespan (min)',
          data: makespans,
          backgroundColor: colors,
          borderColor: borders,
          borderWidth: 2,
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#F1F5F9' }, ticks: { callback: v => `${v} min` } },
          x: { grid: { display: false } }
        }
      }
    });

    // ── Retard Bar ───────────────────────────────────────────────────────
    const ctx2 = document.getElementById('chart-compare-retard');
    if (this.retardChart) this.retardChart.destroy();
    this.retardChart = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: algos,
        datasets: [{
          label: 'Taux retard (%)',
          data: retards,
          backgroundColor: retards.map(v => v > 50 ? hexToRgba(PALETTE.danger, 0.8) : hexToRgba(PALETTE.success, 0.8)),
          borderColor: retards.map(v => v > 50 ? PALETTE.danger : PALETTE.success),
          borderWidth: 2,
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, max: 100, grid: { color: '#F1F5F9' }, ticks: { callback: v => `${v}%` } },
          x: { grid: { display: false } }
        }
      }
    });

    // ── Radar ────────────────────────────────────────────────────────────
    const ctx3 = document.getElementById('chart-compare-radar');
    if (this.radarChart) this.radarChart.destroy();

    // Normalize for radar (higher = better)
    const maxMakespan = Math.max(...makespans) || 1;

    const radarDatasets = algos.map((algo, i) => ({
      label: algo,
      data: [
        Math.round((1 - makespans[i] / maxMakespan) * 100),   // Efficacité makespan
        Math.round(100 - retards[i]),                           // Ponctualité
        Math.round(utils[i]),                                    // Utilisation
        Math.round(100 - (data[algo].taux_retard || 0)),        // Fiabilité
      ],
      borderColor: borders[i],
      backgroundColor: colors[i].replace('0.8', '0.15'),
      borderWidth: 2,
      pointBackgroundColor: borders[i],
      pointRadius: 4,
    }));

    this.radarChart = new Chart(ctx3, {
      type: 'radar',
      data: {
        labels: ['Efficacité Makespan', 'Ponctualité', 'Utilisation Machines', 'Fiabilité'],
        datasets: radarDatasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            ticks: { stepSize: 25, callback: v => `${v}%`, font: { size: 10 } },
            grid: { color: '#E2E8F0' },
            pointLabels: { font: { size: 11, weight: '600' }, color: '#0F172A' },
            angleLines: { color: '#E2E8F0' },
          }
        },
        plugins: {
          legend: { position: 'bottom' },
          tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.raw}%` } },
        }
      }
    });

    // ── Tableau comparatif ────────────────────────────────────────────────
    const minMakespan = Math.min(...makespans);
    const minRetard = Math.min(...retards);

    const tbody = document.getElementById('compare-table-body');
    tbody.innerHTML = algos.map((algo, i) => {
      const isBest = makespans[i] === minMakespan && retards[i] === minRetard;
      const isFastest = makespans[i] === minMakespan;
      const isPunctual = retards[i] === minRetard;
      return `
        <tr style="${isBest ? 'background:var(--success-light)' : ''}">
          <td>${App.algoBadge(algo)}</td>
          <td class="font-600 ${isFastest ? 'text-success' : ''}">${makespans[i].toFixed(1)}</td>
          <td class="${isPunctual ? 'text-success' : ''}">${retards[i].toFixed(1)}%</td>
          <td>${utils[i].toFixed(1)}%</td>
          <td>${isBest ? '<span class="badge badge-success">✓ Optimal</span>' : isFastest ? '<span class="badge badge-accent">⚡ Rapide</span>' : isPunctual ? '<span class="badge badge-violet">📅 Ponctuel</span>' : '<span class="badge badge-gray">—</span>'}</td>
        </tr>`;
    }).join('');
  },
};

// CSS helper
const style = document.createElement('style');
style.textContent = `
  .text-success { color: var(--success) !important; }
  .text-danger { color: var(--danger) !important; }
`;
document.head.appendChild(style);
