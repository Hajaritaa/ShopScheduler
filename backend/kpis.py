"""
Calcul des KPIs temps réel
─────────────────────────
- makespan
- taux de retard
- utilisation des machines
"""

from datetime import datetime


def compute_kpis(schedule, jobs, machines):
    """
    Calcule les KPIs principaux à partir d'un schedule.

    Args:
        schedule: liste de dicts {operation_id, job_id, machine_id, start, end, job_nom, machine_nom}
        jobs: list[Job] SQLAlchemy
        machines: list[Machine] SQLAlchemy

    Returns:
        dict avec makespan, taux_retard, utilisation_machines
    """
    if not schedule:
        return {
            "makespan": 0,
            "taux_retard": 0.0,
            "utilisation_machines": {m.nom: 0.0 for m in machines},
        }

    # ── Makespan ──────────────────────────────────────────────────────────────
    makespan = max(s["end"] for s in schedule)  # minutes

    # ── Fin de chaque job ─────────────────────────────────────────────────────
    job_end = {}
    for s in schedule:
        jid = s["job_id"]
        job_end[jid] = max(job_end.get(jid, 0), s["end"])

    # ── Taux de retard ────────────────────────────────────────────────────────
    now_ts = datetime.utcnow().timestamp()
    retard_count = 0
    total_with_due = 0
    for job in jobs:
        if job.date_due:
            total_with_due += 1
            due_offset = (job.date_due.timestamp() - now_ts) / 60  # minutes depuis maintenant
            job_finish = job_end.get(job.id, 0)
            if job_finish > due_offset:
                retard_count += 1

    taux_retard = retard_count / total_with_due if total_with_due > 0 else 0.0

    # ── Utilisation machines ──────────────────────────────────────────────────
    machine_busy = {}  # machine_id → total temps occupé
    for s in schedule:
        mid = s["machine_id"]
        machine_busy[mid] = machine_busy.get(mid, 0) + (s["end"] - s["start"])

    utilisation_machines = {}
    for m in machines:
        busy = machine_busy.get(m.id, 0)
        # Utilisation = temps occupé / makespan × 100
        utilisation_machines[m.nom] = round((busy / makespan * 100) if makespan > 0 else 0, 1)

    return {
        "makespan": round(makespan, 1),
        "taux_retard": round(taux_retard, 4),
        "utilisation_machines": utilisation_machines,
    }
