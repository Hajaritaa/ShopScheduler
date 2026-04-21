/**
 * app.js — Logique principale SPA : navigation, KPIs, toasts, alertes
 */

const API = {
  get: (url) => fetch(url).then(r => r.json()),
  post: (url, data) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(r => r.json()),
  put: (url, data) => fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(r => r.json()),
  del: (url) => fetch(url, { method: 'DELETE' }).then(r => r.json()),
};

// ── Pages metadata ────────────────────────────────────────────────────────
const PAGES = {
  dashboard:    'Tableau de bord',
  scheduler:    'Ordonnancement',
  gantt:        'Diagramme de Gantt',
  jobs:         'Jobs',
  machines:     'Machines',
  operations:   'Opérations',
  compare:      'Comparaison Algos',
  whatif:       'Simulation What-If',
  history:      'Historique',
  alerts:       'Alertes',
  import:       'Import / Export',
  contraintes:  'Contraintes',
};

// ══════════════════════════════════════════════════════════════════════════
// APP — Navigation & Core
// ══════════════════════════════════════════════════════════════════════════
const App = {
  currentPage: 'dashboard',
  confirmCallback: null,

  // ── Navigate ────────────────────────────────────────────────────────────
  navigate(page) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    // Show target
    const el = document.getElementById(`page-${page}`);
    if (el) el.classList.add('active');
    const nav = document.getElementById(`nav-${page}`);
    if (nav) nav.classList.add('active');

    // Breadcrumb
    document.getElementById('breadcrumb-current').textContent = PAGES[page] || page;
    this.currentPage = page;

    // Page-specific loaders
    const loaders = {
      dashboard: () => { App.refreshKpis(); DashboardCharts.loadJobsStatus(); },
      jobs: () => JobsCRUD.load(),
      machines: () => MachinesCRUD.load(),
      operations: () => OperationsCRUD.load(),
      history: () => HistoryPage.load(),
      alerts: () => AlertsPage.load(),
      gantt: () => GanttView.loadPlanningsList(),
      whatif: () => WhatIf.loadOps(),
      contraintes: () => ContraintesCRUD.load(),
    };
    if (loaders[page]) loaders[page]();
  },

  // ── KPIs ─────────────────────────────────────────────────────────────────
  async refreshKpis() {
    try {
      const kpis = await API.get('/api/kpis');
      document.getElementById('kpi-total-jobs').textContent = kpis.total_jobs;
      document.getElementById('kpi-jobs-sub').textContent = `${kpis.jobs_en_cours} en cours`;
      document.getElementById('kpi-jobs-termines').textContent = kpis.jobs_termines;
      document.getElementById('kpi-ops-sub').textContent = `${kpis.ops_completion_pct}% complétion ops`;
      document.getElementById('kpi-jobs-retard').textContent = kpis.jobs_retard;
      document.getElementById('kpi-retard-pct').textContent = `${kpis.taux_retard_pct}% taux retard`;
      document.getElementById('kpi-makespan').textContent = kpis.makespan ? `${kpis.makespan}` : '—';
      document.getElementById('kpi-algo').textContent = kpis.latest_algo !== '—' ? `via ${kpis.latest_algo}` : 'Aucun planning';
      document.getElementById('kpi-machines').textContent = `${kpis.machines_disponibles}/${kpis.total_machines}`;
      document.getElementById('kpi-machines-sub').textContent = 'disponibles';
      document.getElementById('kpi-completion').textContent = `${kpis.ops_completion_pct}%`;

      // Alert badge
      if (kpis.unread_alerts > 0) {
        document.getElementById('alerts-badge').textContent = kpis.unread_alerts;
        document.getElementById('alerts-badge').classList.remove('hidden');
        document.getElementById('alerts-topbadge').textContent = kpis.unread_alerts;
        document.getElementById('alerts-topbadge').classList.remove('hidden');
      } else {
        document.getElementById('alerts-badge').classList.add('hidden');
        document.getElementById('alerts-topbadge').classList.add('hidden');
      }

      // Dashboard jobs table
      const jobs = await API.get('/api/jobs');
      DashboardCharts.updateJobsStatus(jobs);
      App.renderDashboardJobs(jobs.slice(0, 6));

      // Machine utilization chart
      const plannings = await API.get('/api/plannings');
      if (plannings.length > 0) {
        const detail = await API.get(`/api/plannings/${plannings[0].id}`);
        DashboardCharts.updateMachineUtil(kpis);
        document.getElementById('util-algo-label').textContent = plannings[0].algorithme;
      }

    } catch (e) {
      console.error('KPI refresh error:', e);
    }
  },

  renderDashboardJobs(jobs) {
    const tbody = document.getElementById('dashboard-jobs-body');
    if (!jobs.length) {
      tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-title">Aucun job</div></div></td></tr>`;
      return;
    }
    tbody.innerHTML = jobs.map(j => `
      <tr>
        <td><span class="font-600">${j.nom}</span></td>
        <td>${App.prioriteBadge(j.priorite)}</td>
        <td>${j.date_due ? new Date(j.date_due).toLocaleDateString('fr-FR') : '<span class="text-muted">—</span>'}</td>
        <td>${App.statutBadge(j.statut)}</td>
        <td>${j.nb_operations}</td>
        <td>${j.duree_totale} min</td>
      </tr>`).join('');
  },

  // ── Badges ───────────────────────────────────────────────────────────────
  prioriteBadge(p) {
    const cfg = { 1: ['gray', 'Basse'], 2: ['accent', 'Normale'], 3: ['warning', 'Haute'], 4: ['danger', 'Critique'] };
    const [cls, label] = cfg[p] || ['gray', '?'];
    return `<span class="badge badge-${cls}">${label}</span>`;
  },

  statutBadge(s) {
    const cfg = {
      'en_attente': ['gray', '○ En attente'],
      'en_cours':   ['accent', '● En cours'],
      'terminé':    ['success', '✓ Terminé'],
      'retard':     ['danger', '⚠ Retard'],
    };
    const [cls, label] = cfg[s] || ['gray', s];
    return `<span class="badge badge-${cls}">${label}</span>`;
  },

  machineStatutBadge(s) {
    const cfg = {
      'disponible':   ['success', '• Disponible'],
      'occupée':      ['accent', '• Occupée'],
      'maintenance':  ['warning', '▲ Maintenance'],
    };
    const [cls, label] = cfg[s] || ['gray', s];
    return `<span class="badge badge-${cls}">${label}</span>`;
  },

  algoBadge(a) {
    const cfg = {
      'SPT':     'badge-accent',
      'LPT':     'badge-warning',
      'EDD':     'badge-success',
      'GENETIC': 'badge-violet',
    };
    return `<span class="badge ${cfg[a] || 'badge-gray'}">${a}</span>`;
  },

  // ── Confirm modal ─────────────────────────────────────────────────────────
  confirm(message, callback) {
    document.getElementById('confirm-message').textContent = message;
    this.confirmCallback = callback;
    document.getElementById('modal-confirm').classList.add('open');
  },
  closeConfirm() {
    this.confirmCallback = null;
    document.getElementById('modal-confirm').classList.remove('open');
  },
  executeConfirm() {
    if (this.confirmCallback) this.confirmCallback();
    this.closeConfirm();
  },

  // ── Toast ─────────────────────────────────────────────────────────────────
  toast(message, type = 'success', duration = 3500) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const icons = { success: '✓', warning: '⚠', error: '✕', info: 'ℹ' };
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || '•'}</span><span>${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => toast.classList.add('show'));
    });
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  // ── Export ────────────────────────────────────────────────────────────────
  exportExcel() {
    window.open('/api/export/excel', '_blank');
    App.toast('Export Excel en cours…', 'info');
  },
  exportPdf() {
    window.open('/api/export/pdf', '_blank');
    App.toast('Génération PDF en cours…', 'info');
  },
};

// ══════════════════════════════════════════════════════════════════════════
// SCHEDULER
// ══════════════════════════════════════════════════════════════════════════
const Scheduler = {
  selectedAlgo: 'spt',
  lastResult: null,

  selectAlgo(algo, btn) {
    this.selectedAlgo = algo;
    document.querySelectorAll('.algo-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
  },

  async run() {
    const btn = document.getElementById('btn-run-schedule');
    const status = document.getElementById('schedule-status');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Calcul en cours…';
    status.textContent = '';

    try {
      const result = await API.post('/api/schedule', { algorithme: this.selectedAlgo });
      if (result.error) {
        App.toast(result.error, 'error');
        return;
      }
      this.lastResult = result;
      this.displayResults(result);
      App.toast(`Planning ${result.algorithme} calculé ! Makespan: ${result.makespan} min`, 'success');
      App.refreshKpis();
      // Reload gantt list
      GanttView.loadPlanningsList();
    } catch (e) {
      App.toast('Erreur lors du calcul', 'error');
      console.error(e);
    } finally {
      btn.disabled = false;
      btn.innerHTML = '▶ Lancer l\'ordonnancement';
    }
  },

  displayResults(r) {
    document.getElementById('schedule-results').classList.remove('hidden');
    document.getElementById('sched-makespan').textContent = `${r.makespan} min`;
    document.getElementById('sched-retard').textContent = `${(r.taux_retard * 100).toFixed(1)}%`;
    document.getElementById('sched-algo').textContent = r.algorithme;

    // Mini Gantt
    GanttView.renderMini('sched-gantt-container', r.gantt);

    // Table
    const tbody = document.getElementById('schedule-table-body');
    tbody.innerHTML = r.schedule.map((s, i) => `
      <tr>
        <td>${i + 1}</td>
        <td class="font-600">${s.job_nom}</td>
        <td>${s.machine_nom}</td>
        <td>${s.start.toFixed(1)}</td>
        <td>${s.end.toFixed(1)}</td>
        <td>${s.duree.toFixed(1)} min</td>
      </tr>`).join('');
  },
};

// ══════════════════════════════════════════════════════════════════════════
// HISTORY PAGE
// ══════════════════════════════════════════════════════════════════════════
const HistoryPage = {
  async load() {
    const plannings = await API.get('/api/plannings');
    document.getElementById('history-count').textContent = `Plannings (${plannings.length})`;
    const tbody = document.getElementById('history-table-body');
    if (!plannings.length) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">🕐</div><div class="empty-state-title">Aucun planning généré</div><div class="empty-state-text">Lancez un ordonnancement pour créer votre premier planning.</div></div></td></tr>`;
      return;
    }
    tbody.innerHTML = plannings.map(p => `
      <tr>
        <td>#${p.id}</td>
        <td>${p.nom}</td>
        <td>${App.algoBadge(p.algorithme)}</td>
        <td class="font-600">${p.makespan}</td>
        <td>${p.taux_retard}%</td>
        <td>${new Date(p.date_creation).toLocaleString('fr-FR')}</td>
        <td class="td-actions">
          <button class="btn btn-secondary btn-xs" onclick="GanttView.loadFromHistory(${p.id})">📊 Gantt</button>
          <button class="btn btn-danger btn-xs" onclick="HistoryPage.delete(${p.id})">✕</button>
        </td>
      </tr>`).join('');
  },

  async delete(id) {
    App.confirm('Supprimer ce planning ?', async () => {
      await API.del(`/api/plannings/${id}`);
      App.toast('Planning supprimé', 'warning');
      this.load();
    });
  },
};

// ══════════════════════════════════════════════════════════════════════════
// ALERTS PAGE
// ══════════════════════════════════════════════════════════════════════════
const AlertsPage = {
  async load() {
    const alerts = await API.get('/api/alerts/all');
    const el = document.getElementById('alerts-list');
    if (!alerts.length) {
      el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🔔</div><div class="empty-state-title">Aucune alerte</div><div class="empty-state-text">Tout est nominal.</div></div>`;
      return;
    }
    el.innerHTML = alerts.map(a => `
      <div class="alert-item alert-${a.type}" style="${a.lu ? 'opacity:0.6' : ''}">
        <div class="alert-dot"></div>
        <div class="alert-text">
          ${a.message}
          <div class="alert-time">${new Date(a.date).toLocaleString('fr-FR')}</div>
        </div>
        ${!a.lu ? `<button class="alert-read-btn" onclick="AlertsPage.markRead(${a.id})">Marquer lu</button>` : '<span class="badge badge-gray" style="font-size:10px">Lu</span>'}
      </div>`).join('');
  },

  async markRead(id) {
    await API.post(`/api/alerts/${id}/read`, {});
    this.load();
    App.refreshKpis();
  },

  async readAll() {
    await API.post('/api/alerts/read-all', {});
    App.toast('Toutes les alertes marquées comme lues', 'success');
    this.load();
    App.refreshKpis();
  },
};

// ══════════════════════════════════════════════════════════════════════════
// IMPORT/EXPORT
// ══════════════════════════════════════════════════════════════════════════
const ImportExport = {
  async handleFile(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    const result = document.getElementById('import-result');
    result.classList.remove('hidden');
    result.innerHTML = '<div class="spinner dark" style="display:inline-block;margin-right:8px"></div> Import en cours…';

    try {
      const res = await fetch('/api/import-csv', { method: 'POST', body: fd });
      const data = await res.json();
      if (data.error) {
        result.innerHTML = `<div style="color:var(--danger)">❌ ${data.error}</div>`;
      } else {
        result.innerHTML = `<div style="color:var(--success)">✅ ${data.imported} jobs importés</div>
          ${data.errors.length ? `<div style="color:var(--warning);font-size:12px;margin-top:4px">${data.errors.join('<br>')}</div>` : ''}`;
        App.toast(`${data.imported} jobs importés avec succès`, 'success');
        App.refreshKpis();
      }
    } catch (e) {
      result.innerHTML = `<div style="color:var(--danger)">❌ Erreur d'import</div>`;
    }
  },
};

// Drag & drop zone
document.addEventListener('DOMContentLoaded', () => {
  const zone = document.getElementById('drop-zone');
  if (zone) {
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) ImportExport.handleFile(file);
    });
  }

  // Start app
  App.navigate('dashboard');

  // Poll alerts every 30s
  setInterval(() => App.refreshKpis(), 30000);
});
