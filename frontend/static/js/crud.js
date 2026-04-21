/**
 * crud.js — CRUD complet pour Jobs, Machines, Opérations, Contraintes
 */

// ══════════════════════════════════════════════════════════════════════════
// JOBS CRUD
// ══════════════════════════════════════════════════════════════════════════
const JobsCRUD = {
  allJobs: [],

  async load() {
    const jobs = await API.get('/api/jobs');
    this.allJobs = jobs;
    document.getElementById('jobs-count').textContent = `Jobs (${jobs.length})`;
    this.render(jobs);
  },

  render(jobs) {
    const tbody = document.getElementById('jobs-table-body');
    if (!jobs.length) {
      tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-title">Aucun job</div>
        <div class="empty-state-text">Cliquez sur « Nouveau Job » pour commencer.</div>
      </div></td></tr>`;
      return;
    }
    tbody.innerHTML = jobs.map(j => `
      <tr>
        <td>#${j.id}</td>
        <td><span class="font-600">${j.nom}</span></td>
        <td>${App.prioriteBadge(j.priorite)}</td>
        <td>${j.date_due ? new Date(j.date_due).toLocaleDateString('fr-FR') : '<span class="text-muted">—</span>'}</td>
        <td>${App.statutBadge(j.statut)}</td>
        <td>${j.nb_operations}</td>
        <td>${j.duree_totale} min</td>
        <td class="td-actions">
          <button class="btn btn-secondary btn-xs" onclick="JobsCRUD.openEdit(${j.id})" title="Modifier">✏</button>
          <button class="btn btn-danger btn-xs" onclick="JobsCRUD.delete(${j.id})" title="Supprimer">✕</button>
        </td>
      </tr>`).join('');
  },

  search(q) {
    const filtered = this.allJobs.filter(j => j.nom.toLowerCase().includes(q.toLowerCase()));
    this.render(filtered);
  },

  openCreate() {
    document.getElementById('modal-job-title').textContent = 'Nouveau Job';
    document.getElementById('job-id').value = '';
    document.getElementById('job-nom').value = '';
    document.getElementById('job-priorite').value = '2';
    document.getElementById('job-statut').value = 'en_attente';
    document.getElementById('job-date-due').value = '';
    document.getElementById('modal-job').classList.add('open');
    document.getElementById('job-nom').focus();
  },

  async openEdit(id) {
    const job = await API.get(`/api/jobs/${id}`);
    document.getElementById('modal-job-title').textContent = 'Modifier le Job';
    document.getElementById('job-id').value = job.id;
    document.getElementById('job-nom').value = job.nom;
    document.getElementById('job-priorite').value = job.priorite;
    document.getElementById('job-statut').value = job.statut;
    if (job.date_due) {
      // Format for datetime-local input
      const dt = new Date(job.date_due);
      const local = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
      document.getElementById('job-date-due').value = local;
    } else {
      document.getElementById('job-date-due').value = '';
    }
    document.getElementById('modal-job').classList.add('open');
  },

  closeModal() {
    document.getElementById('modal-job').classList.remove('open');
  },

  async save() {
    const id = document.getElementById('job-id').value;
    const nom = document.getElementById('job-nom').value.trim();
    if (!nom) { App.toast('Le nom est obligatoire', 'error'); return; }

    const data = {
      nom,
      priorite: parseInt(document.getElementById('job-priorite').value),
      statut: document.getElementById('job-statut').value,
      date_due: document.getElementById('job-date-due').value || null,
    };

    try {
      if (id) {
        await API.put(`/api/jobs/${id}`, data);
        App.toast('Job modifié avec succès', 'success');
      } else {
        await API.post('/api/jobs', data);
        App.toast('Job créé avec succès', 'success');
      }
      this.closeModal();
      this.load();
      App.refreshKpis();
    } catch (e) {
      App.toast('Erreur lors de la sauvegarde', 'error');
    }
  },

  delete(id) {
    App.confirm('Supprimer ce job et toutes ses opérations ?', async () => {
      await API.del(`/api/jobs/${id}`);
      App.toast('Job supprimé', 'warning');
      this.load();
      App.refreshKpis();
    });
  },
};

// ══════════════════════════════════════════════════════════════════════════
// MACHINES CRUD
// ══════════════════════════════════════════════════════════════════════════
const MachinesCRUD = {
  async load() {
    const machines = await API.get('/api/machines');
    document.getElementById('machines-count').textContent = `Machines (${machines.length})`;
    const tbody = document.getElementById('machines-table-body');
    if (!machines.length) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">
        <div class="empty-state-icon">🏭</div>
        <div class="empty-state-title">Aucune machine</div>
        <div class="empty-state-text">Ajoutez vos premières machines.</div>
      </div></td></tr>`;
      return;
    }
    tbody.innerHTML = machines.map(m => `
      <tr>
        <td>#${m.id}</td>
        <td><span class="font-600">${m.nom}</span></td>
        <td><span class="badge badge-gray">${m.type}</span></td>
        <td>${m.capacite}</td>
        <td>${App.machineStatutBadge(m.statut)}</td>
        <td>${m.temps_setup}</td>
        <td class="td-actions">
          <button class="btn btn-secondary btn-xs" onclick="MachinesCRUD.openEdit(${m.id})">✏</button>
          <button class="btn btn-danger btn-xs" onclick="MachinesCRUD.delete(${m.id})">✕</button>
        </td>
      </tr>`).join('');
  },

  openCreate() {
    document.getElementById('modal-machine-title').textContent = 'Nouvelle Machine';
    document.getElementById('machine-id').value = '';
    document.getElementById('machine-nom').value = '';
    document.getElementById('machine-type').value = 'standard';
    document.getElementById('machine-statut').value = 'disponible';
    document.getElementById('machine-capacite').value = '1';
    document.getElementById('machine-setup').value = '0';
    document.getElementById('modal-machine').classList.add('open');
    document.getElementById('machine-nom').focus();
  },

  async openEdit(id) {
    const m = await API.get(`/api/machines/${id}`);
    document.getElementById('modal-machine-title').textContent = 'Modifier la Machine';
    document.getElementById('machine-id').value = m.id;
    document.getElementById('machine-nom').value = m.nom;
    document.getElementById('machine-type').value = m.type;
    document.getElementById('machine-statut').value = m.statut;
    document.getElementById('machine-capacite').value = m.capacite;
    document.getElementById('machine-setup').value = m.temps_setup;
    document.getElementById('modal-machine').classList.add('open');
  },

  closeModal() {
    document.getElementById('modal-machine').classList.remove('open');
  },

  async save() {
    const id = document.getElementById('machine-id').value;
    const nom = document.getElementById('machine-nom').value.trim();
    if (!nom) { App.toast('Le nom est obligatoire', 'error'); return; }

    const data = {
      nom,
      type: document.getElementById('machine-type').value,
      statut: document.getElementById('machine-statut').value,
      capacite: parseInt(document.getElementById('machine-capacite').value),
      temps_setup: parseFloat(document.getElementById('machine-setup').value),
    };

    try {
      if (id) {
        await API.put(`/api/machines/${id}`, data);
        App.toast('Machine modifiée', 'success');
      } else {
        await API.post('/api/machines', data);
        App.toast('Machine créée', 'success');
      }
      this.closeModal();
      this.load();
    } catch (e) {
      App.toast('Erreur lors de la sauvegarde', 'error');
    }
  },

  delete(id) {
    App.confirm('Supprimer cette machine ?', async () => {
      await API.del(`/api/machines/${id}`);
      App.toast('Machine supprimée', 'warning');
      this.load();
    });
  },
};

// ══════════════════════════════════════════════════════════════════════════
// OPERATIONS CRUD
// ══════════════════════════════════════════════════════════════════════════
const OperationsCRUD = {
  allOps: [],

  async load() {
    const [ops, jobs, machines] = await Promise.all([
      API.get('/api/operations'),
      API.get('/api/jobs'),
      API.get('/api/machines'),
    ]);
    this.allOps = ops;
    document.getElementById('ops-count').textContent = `Opérations (${ops.length})`;

    // Populate filter
    const filterSel = document.getElementById('ops-filter-job');
    filterSel.innerHTML = '<option value="">Tous les jobs</option>' +
      jobs.map(j => `<option value="${j.id}">${j.nom}</option>`).join('');

    // Populate modal selects
    document.getElementById('op-job-id').innerHTML = jobs.map(j =>
      `<option value="${j.id}">${j.nom}</option>`).join('');
    document.getElementById('op-machine-id').innerHTML = machines.map(m =>
      `<option value="${m.id}">${m.nom}</option>`).join('');

    this.render(ops);
  },

  render(ops) {
    const tbody = document.getElementById('ops-table-body');
    if (!ops.length) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">
        <div class="empty-state-icon">⚡</div>
        <div class="empty-state-title">Aucune opération</div>
        <div class="empty-state-text">Ajoutez des opérations à vos jobs.</div>
      </div></td></tr>`;
      return;
    }
    tbody.innerHTML = ops.map(o => `
      <tr>
        <td>#${o.id}</td>
        <td class="font-600">${o.job_nom}</td>
        <td>${o.machine_nom}</td>
        <td><span class="badge badge-gray">${o.ordre}</span></td>
        <td>${o.duree} min</td>
        <td>${App.statutBadge(o.statut)}</td>
        <td class="td-actions">
          <button class="btn btn-secondary btn-xs" onclick="OperationsCRUD.openEdit(${o.id})">✏</button>
          <button class="btn btn-danger btn-xs" onclick="OperationsCRUD.delete(${o.id})">✕</button>
        </td>
      </tr>`).join('');
  },

  filterByJob(jobId) {
    if (!jobId) this.render(this.allOps);
    else this.render(this.allOps.filter(o => o.job_id == jobId));
  },

  openCreate() {
    document.getElementById('modal-op-title').textContent = 'Nouvelle Opération';
    document.getElementById('op-id').value = '';
    document.getElementById('op-duree').value = '30';
    document.getElementById('op-ordre').value = '1';
    document.getElementById('op-statut').value = 'en_attente';
    document.getElementById('modal-operation').classList.add('open');
  },

  async openEdit(id) {
    const op = await API.get(`/api/operations/${id}`);
    document.getElementById('modal-op-title').textContent = 'Modifier l\'Opération';
    document.getElementById('op-id').value = op.id;
    document.getElementById('op-job-id').value = op.job_id;
    document.getElementById('op-machine-id').value = op.machine_id;
    document.getElementById('op-duree').value = op.duree;
    document.getElementById('op-ordre').value = op.ordre;
    document.getElementById('op-statut').value = op.statut;
    document.getElementById('modal-operation').classList.add('open');
  },

  closeModal() {
    document.getElementById('modal-operation').classList.remove('open');
  },

  async save() {
    const id = document.getElementById('op-id').value;
    const data = {
      job_id: parseInt(document.getElementById('op-job-id').value),
      machine_id: parseInt(document.getElementById('op-machine-id').value),
      duree: parseFloat(document.getElementById('op-duree').value),
      ordre: parseInt(document.getElementById('op-ordre').value),
      statut: document.getElementById('op-statut').value,
    };

    if (!data.job_id || !data.machine_id || !data.duree) {
      App.toast('Tous les champs sont obligatoires', 'error');
      return;
    }

    try {
      if (id) {
        await API.put(`/api/operations/${id}`, data);
        App.toast('Opération modifiée', 'success');
      } else {
        await API.post('/api/operations', data);
        App.toast('Opération créée', 'success');
      }
      this.closeModal();
      this.load();
    } catch (e) {
      App.toast('Erreur lors de la sauvegarde', 'error');
    }
  },

  delete(id) {
    App.confirm('Supprimer cette opération ?', async () => {
      await API.del(`/api/operations/${id}`);
      App.toast('Opération supprimée', 'warning');
      this.load();
    });
  },
};

// ══════════════════════════════════════════════════════════════════════════
// CONTRAINTES CRUD
// ══════════════════════════════════════════════════════════════════════════
const ContraintesCRUD = {
  async load() {
    const items = await API.get('/api/contraintes');
    const tbody = document.getElementById('contraintes-table-body');
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state">
        <div class="empty-state-icon">🔒</div>
        <div class="empty-state-title">Aucune contrainte</div>
      </div></td></tr>`;
      return;
    }
    const typeBadge = { 'priorité': 'badge-violet', 'délai': 'badge-warning', 'machine': 'badge-accent', 'autre': 'badge-gray' };
    tbody.innerHTML = items.map(c => `
      <tr>
        <td>#${c.id}</td>
        <td><span class="badge ${typeBadge[c.type] || 'badge-gray'}">${c.type}</span></td>
        <td class="font-600">${c.valeur}</td>
        <td>${c.description || '<span class="text-muted">—</span>'}</td>
        <td><button class="btn btn-danger btn-xs" onclick="ContraintesCRUD.delete(${c.id})">✕</button></td>
      </tr>`).join('');
  },

  openCreate() {
    document.getElementById('contrainte-type').value = 'priorité';
    document.getElementById('contrainte-valeur').value = '';
    document.getElementById('contrainte-desc').value = '';
    document.getElementById('modal-contrainte').classList.add('open');
  },

  closeModal() {
    document.getElementById('modal-contrainte').classList.remove('open');
  },

  async save() {
    const data = {
      type: document.getElementById('contrainte-type').value,
      valeur: document.getElementById('contrainte-valeur').value.trim(),
      description: document.getElementById('contrainte-desc').value.trim(),
    };
    await API.post('/api/contraintes', data);
    App.toast('Contrainte ajoutée', 'success');
    this.closeModal();
    this.load();
  },

  delete(id) {
    App.confirm('Supprimer cette contrainte ?', async () => {
      await API.del(`/api/contraintes/${id}`);
      App.toast('Contrainte supprimée', 'warning');
      this.load();
    });
  },
};

// Close modals on overlay click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// Keyboard ESC to close modals
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  }
});
