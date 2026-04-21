/**
 * gantt_view.js — Diagramme de Gantt interactif
 * Utilise frappe-gantt + rendu canvas personnalisé pour mini-gantt
 */

const GanttView = {
  ganttInstance: null,
  currentTask: [],
  viewMode: 'Day',

  // ── Charger la liste des plannings dans le select ──────────────────────
  async loadPlanningsList() {
    const plannings = await API.get('/api/plannings');
    const sel = document.getElementById('gantt-planning-select');
    sel.innerHTML = '<option value="">— Sélectionner un planning —</option>' +
      plannings.map(p => `<option value="${p.id}">${p.nom} (${p.algorithme})</option>`).join('');

    // Auto-load latest
    if (plannings.length > 0) {
      sel.value = plannings[0].id;
      await this.loadPlanning(plannings[0].id);
    }
  },

  // ── Charger et afficher un planning ───────────────────────────────────
  async loadPlanning(planningId) {
    if (!planningId) return;

    const container = document.getElementById('gantt-container');
    container.innerHTML = '<div style="text-align:center;padding:40px"><div class="spinner dark" style="width:28px;height:28px;margin:0 auto 8px"></div><div class="text-muted">Chargement du Gantt…</div></div>';

    try {
      const detail = await API.get(`/api/plannings/${planningId}`);
      const ops = detail.operations;

      if (!ops || !ops.length) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📊</div><div class="empty-state-title">Planning vide</div></div>';
        return;
      }

      // Build frappe-gantt tasks
      const tasks = this.buildTasks(ops);
      this.currentTasks = tasks;
      this.renderFrappeGantt(container, tasks);
    } catch (e) {
      container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚠</div><div class="empty-state-title">Erreur de chargement</div></div>';
      console.error(e);
    }
  },

  // ── Depuis l'historique ────────────────────────────────────────────────
  async loadFromHistory(planningId) {
    App.navigate('gantt');
    setTimeout(async () => {
      await this.loadPlanningsList();
      document.getElementById('gantt-planning-select').value = planningId;
      await this.loadPlanning(planningId);
    }, 100);
  },

  // ── Build frappe-gantt task list ───────────────────────────────────────
  buildTasks(ops) {
    const COLORS = [
      '#2563EB', '#7C3AED', '#16A34A', '#D97706',
      '#DC2626', '#0891B2', '#D946EF', '#EA580C', '#0D9488'
    ];
    const jobColors = {};
    let colorIdx = 0;
    const baseDate = new Date();
    baseDate.setHours(0, 0, 0, 0);

    return ops.map((op, i) => {
      if (!jobColors[op.job_nom]) {
        jobColors[op.job_nom] = COLORS[colorIdx++ % COLORS.length];
      }
      const start = new Date(baseDate.getTime() + op.heure_debut * 60 * 1000);
      const end = new Date(baseDate.getTime() + op.heure_fin * 60 * 1000);
      // Ensure min 1 minute display
      if (end <= start) end.setTime(start.getTime() + 60 * 1000);

      return {
        id: `op_${op.id || i}`,
        name: `${op.job_nom}`,
        start: this.formatDate(start),
        end: this.formatDate(end),
        progress: 0,
        custom_class: `gantt-bar-job`,
        dependencies: '',
        _color: jobColors[op.job_nom],
        _machine: op.machine_nom,
        _start_min: op.heure_debut,
        _end_min: op.heure_fin,
      };
    });
  },

  formatDate(d) {
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  },

  // ── Rendu frappe-gantt ─────────────────────────────────────────────────
  renderFrappeGantt(container, tasks) {
    container.innerHTML = '';
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.id = 'gantt-svg';
    container.appendChild(svg);

    try {
      this.ganttInstance = new Gantt('#gantt-svg', tasks, {
        view_mode: this.viewMode,
        date_format: 'YYYY-MM-DD HH:mm',
        bar_height: 32,
        bar_corner_radius: 4,
        arrow_curve: 5,
        padding: 16,
        custom_popup_html: (task) => `
          <div style="padding:10px;font-family:Inter,sans-serif;min-width:180px">
            <div style="font-weight:700;font-size:13px;margin-bottom:4px">${task.name}</div>
            <div style="color:#64748B;font-size:12px">Machine : ${task._machine || '—'}</div>
            <div style="color:#64748B;font-size:12px">Début : ${task._start_min?.toFixed(0)} min</div>
            <div style="color:#64748B;font-size:12px">Fin : ${task._end_min?.toFixed(0)} min</div>
            <div style="color:#64748B;font-size:12px">Durée : ${((task._end_min || 0) - (task._start_min || 0)).toFixed(0)} min</div>
          </div>`,
      });

      // Color bars by job
      setTimeout(() => {
        const bars = container.querySelectorAll('.bar');
        bars.forEach((bar, i) => {
          if (tasks[i] && tasks[i]._color) {
            const rect = bar.querySelector('rect');
            if (rect) {
              rect.style.fill = tasks[i]._color;
              rect.style.opacity = '0.85';
            }
          }
        });
      }, 100);

    } catch (e) {
      // Fallback to custom canvas gantt
      this.renderCanvasGantt(container, tasks);
    }
  },

  // ── Canvas Gantt fallback ──────────────────────────────────────────────
  renderCanvasGantt(container, tasks) {
    if (!tasks || !tasks.length) return;
    container.innerHTML = '';

    const maxEnd = Math.max(...tasks.map(t => t._end_min || 0));
    const ROW_H = 40;
    const HEADER_H = 32;
    const LABEL_W = 160;
    const CHART_W = Math.max(container.clientWidth - LABEL_W - 32, 600);
    const totalH = tasks.length * ROW_H + HEADER_H + 20;

    const canvas = document.createElement('canvas');
    canvas.width = LABEL_W + CHART_W + 16;
    canvas.height = totalH;
    canvas.style.width = '100%';
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    const scale = window.devicePixelRatio || 1;
    canvas.width = (LABEL_W + CHART_W + 16) * scale;
    canvas.height = totalH * scale;
    canvas.style.width = `${LABEL_W + CHART_W + 16}px`;
    canvas.style.height = `${totalH}px`;
    ctx.scale(scale, scale);

    ctx.font = '11px Inter, sans-serif';
    ctx.textBaseline = 'middle';

    // Header
    ctx.fillStyle = '#F1F5F9';
    ctx.fillRect(0, 0, LABEL_W + CHART_W + 16, HEADER_H);
    ctx.strokeStyle = '#E2E8F0';
    ctx.strokeRect(0, 0, LABEL_W + CHART_W + 16, HEADER_H);

    ctx.fillStyle = '#64748B';
    ctx.font = 'bold 11px Inter, sans-serif';
    ctx.fillText('Job', 12, HEADER_H / 2);

    // Time axis ticks
    const ticks = 10;
    for (let i = 0; i <= ticks; i++) {
      const x = LABEL_W + (i / ticks) * CHART_W;
      const t = Math.round((i / ticks) * maxEnd);
      ctx.fillStyle = '#64748B';
      ctx.font = '10px Inter, sans-serif';
      ctx.fillText(`${t}`, x - 8, HEADER_H / 2);
    }

    // Rows
    tasks.forEach((task, rowIdx) => {
      const y = HEADER_H + rowIdx * ROW_H;
      const color = task._color || '#2563EB';
      const s = task._start_min || 0;
      const e = task._end_min || task._start_min + 10;

      // Alternating bg
      ctx.fillStyle = rowIdx % 2 === 0 ? '#F8F9FC' : '#FFFFFF';
      ctx.fillRect(0, y, LABEL_W + CHART_W + 16, ROW_H);

      // Border
      ctx.strokeStyle = '#E2E8F0';
      ctx.lineWidth = 0.5;
      ctx.beginPath();
      ctx.moveTo(0, y + ROW_H);
      ctx.lineTo(LABEL_W + CHART_W + 16, y + ROW_H);
      ctx.stroke();

      // Label
      ctx.fillStyle = '#0F172A';
      ctx.font = '600 12px Inter, sans-serif';
      const label = task.name.length > 20 ? task.name.slice(0, 18) + '…' : task.name;
      ctx.fillText(label, 12, y + ROW_H / 2);

      // Bar
      const bx = LABEL_W + (s / maxEnd) * CHART_W;
      const bw = Math.max(((e - s) / maxEnd) * CHART_W, 6);
      const by = y + 8;
      const bh = ROW_H - 16;

      // Bar fill
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.85;
      this.roundRect(ctx, bx, by, bw, bh, 3);
      ctx.fill();
      ctx.globalAlpha = 1;

      // Bar label (machine)
      if (bw > 40 && task._machine) {
        ctx.fillStyle = 'white';
        ctx.font = '10px Inter, sans-serif';
        ctx.fillText(task._machine, bx + 6, by + bh / 2);
      }
    });

    // Vertical separator
    ctx.strokeStyle = '#CBD5E1';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(LABEL_W, 0);
    ctx.lineTo(LABEL_W, totalH);
    ctx.stroke();
  },

  roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  },

  // ── Mini Gantt (dans la page scheduler) ──────────────────────────────
  renderMini(containerId, ganttData) {
    if (!ganttData || !ganttData.length) return;
    const container = document.getElementById(containerId);
    if (!container) return;

    // Convert gantt data (has start/end in minutes) to tasks
    const fakeTasks = ganttData.map(g => ({
      name: g.job,
      _start_min: g.start,
      _end_min: g.end,
      _machine: g.machine,
      _color: g.color || '#2563EB',
    }));
    this.renderCanvasGantt(container, fakeTasks);
  },

  // ── Controls ───────────────────────────────────────────────────────────
  changeMode(mode) {
    this.viewMode = mode;
    if (this.ganttInstance) {
      this.ganttInstance.change_view_mode(mode);
    }
  },

  zoomIn() {
    const modes = ['Hour', 'Quarter Day', 'Half Day', 'Day', 'Week'];
    const idx = modes.indexOf(this.viewMode);
    if (idx > 0) {
      this.viewMode = modes[idx - 1];
      document.getElementById('gantt-view-mode').value = this.viewMode;
      this.changeMode(this.viewMode);
    }
  },

  zoomOut() {
    const modes = ['Hour', 'Quarter Day', 'Half Day', 'Day', 'Week'];
    const idx = modes.indexOf(this.viewMode);
    if (idx < modes.length - 1) {
      this.viewMode = modes[idx + 1];
      document.getElementById('gantt-view-mode').value = this.viewMode;
      this.changeMode(this.viewMode);
    }
  },

  resetView() {
    this.viewMode = 'Day';
    document.getElementById('gantt-view-mode').value = 'Day';
    if (this.ganttInstance) this.ganttInstance.change_view_mode('Day');
  },

  exportPng() {
    const canvas = document.querySelector('#gantt-container canvas');
    if (canvas) {
      const link = document.createElement('a');
      link.download = `gantt_${new Date().toISOString().slice(0,10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      App.toast('Gantt exporté en PNG', 'success');
    } else {
      // Try SVG export
      const svg = document.querySelector('#gantt-svg');
      if (svg) {
        const data = new XMLSerializer().serializeToString(svg);
        const blob = new Blob([data], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.download = `gantt_${new Date().toISOString().slice(0,10)}.svg`;
        link.href = url;
        link.click();
        App.toast('Gantt exporté en SVG', 'success');
      } else {
        App.toast('Aucun Gantt à exporter', 'warning');
      }
    }
  },
};
