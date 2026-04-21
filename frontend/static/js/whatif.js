/**
 * whatif.js — Simulation What-If
 * Modifie les durées et recalcule le scheduling sans sauvegarder
 */

const WhatIf = {
  allOps: [],

  // ── Charger les opérations pour l'affichage ────────────────────────────
  async loadOps() {
    try {
      const ops = await API.get('/api/operations');
      this.allOps = ops.filter(o => o.statut !== 'terminé');
      this.renderOpsList();
    } catch (e) {
      console.error('WhatIf loadOps error:', e);
    }
  },

  renderOpsList() {
    const container = document.getElementById('whatif-ops-list');
    if (!this.allOps.length) {
      container.innerHTML = '<div class="text-muted">Aucune opération disponible.</div>';
      return;
    }

    container.innerHTML = this.allOps.map(op => `
      <div class="whatif-op-row">
        <div class="whatif-op-label">
          <div class="font-600" style="font-size:12px">${op.job_nom}</div>
          <div class="text-muted">${op.machine_nom} — Ordre ${op.ordre}</div>
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <input
            type="number"
            class="whatif-op-input"
            id="whatif-op-${op.id}"
            value="${op.duree}"
            min="1"
            step="0.5"
            title="Durée originale: ${op.duree} min"
          />
          <span class="text-muted" style="font-size:11px">min</span>
        </div>
        <button
          class="btn btn-xs btn-secondary"
          onclick="document.getElementById('whatif-op-${op.id}').value=${op.duree}"
          title="Réinitialiser">
          ↺
        </button>
      </div>`).join('');
  },

  // ── Lancer la simulation ───────────────────────────────────────────────
  async simulate() {
    const algo = document.getElementById('whatif-algo').value;

    // Collect modified durations
    const durees = {};
    this.allOps.forEach(op => {
      const input = document.getElementById(`whatif-op-${op.id}`);
      if (input) {
        const val = parseFloat(input.value);
        if (!isNaN(val) && val !== op.duree) {
          durees[String(op.id)] = val;
        }
      }
    });

    const payload = {
      algorithme: algo,
      modifications: { durees },
    };

    // Show loading
    document.getElementById('whatif-empty').classList.add('hidden');
    document.getElementById('whatif-results').classList.remove('hidden');
    document.getElementById('whatif-makespan').textContent = '…';
    document.getElementById('whatif-retard').textContent = '…';
    document.getElementById('whatif-util').textContent = '…';

    try {
      const result = await API.post('/api/whatif', payload);

      document.getElementById('whatif-makespan').textContent = `${result.makespan}`;
      document.getElementById('whatif-retard').textContent = `${result.taux_retard.toFixed(1)}%`;

      const utilValues = Object.values(result.utilisation_machines || {});
      const utilMoy = utilValues.length > 0
        ? (utilValues.reduce((a, b) => a + b, 0) / utilValues.length).toFixed(1)
        : '—';
      document.getElementById('whatif-util').textContent = `${utilMoy}%`;

      // Color code results
      const makespan = result.makespan;
      const retard = result.taux_retard;
      document.getElementById('whatif-makespan').style.color =
        makespan > 300 ? 'var(--danger)' : makespan > 150 ? 'var(--warning)' : 'var(--success)';
      document.getElementById('whatif-retard').style.color =
        retard > 50 ? 'var(--danger)' : retard > 20 ? 'var(--warning)' : 'var(--success)';

      // Mini Gantt
      if (result.gantt && result.gantt.length > 0) {
        document.getElementById('whatif-gantt-card').style.display = '';
        GanttView.renderMini('whatif-gantt', result.gantt);
      }

      const modsCount = Object.keys(durees).length;
      App.toast(
        `Simulation terminée — ${modsCount} opération(s) modifiée(s). Makespan: ${makespan} min`,
        'info',
        4000
      );

    } catch (e) {
      App.toast('Erreur lors de la simulation', 'error');
      document.getElementById('whatif-makespan').textContent = 'Err';
      console.error(e);
    }
  },

  // ── Réinitialiser toutes les durées ────────────────────────────────────
  reset() {
    this.allOps.forEach(op => {
      const input = document.getElementById(`whatif-op-${op.id}`);
      if (input) input.value = op.duree;
    });
    document.getElementById('whatif-results').classList.add('hidden');
    document.getElementById('whatif-empty').classList.remove('hidden');
    document.getElementById('whatif-gantt-card').style.display = 'none';
  },
};
