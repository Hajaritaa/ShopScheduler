"""
Algorithmes d'ordonnancement Job Shop
─────────────────────────────────────
SPT  — Shortest Processing Time
LPT  — Longest Processing Time
EDD  — Earliest Due Date
GENA — Algorithme Génétique simplifié
"""

import random
import copy
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _build_schedule(jobs, machines, operations, job_order):
    """
    Construit un planning à partir d'un ordre de jobs.
    Respecte les contraintes d'ordre des opérations dans chaque job.
    Retourne schedule[] et gantt[].
    """
    # Dictionnaire machine_id → temps de disponibilité suivant
    machine_available = {m.id: 0.0 for m in machines}
    # Dictionnaire job_id → fin de la dernière opération planifiée
    job_end = {j.id: 0.0 for j in jobs}

    # Grouper les ops par job, triées par ordre
    ops_by_job = {}
    for op in operations:
        ops_by_job.setdefault(op.job_id, []).append(op)
    for jid in ops_by_job:
        ops_by_job[jid].sort(key=lambda o: o.ordre)

    schedule = []
    gantt = []

    # Couleurs par job (cyclique)
    COLORS = [
        "#2563EB", "#7C3AED", "#16A34A", "#D97706",
        "#DC2626", "#0891B2", "#D946EF", "#EA580C",
    ]
    job_colors = {}
    for idx, job in enumerate(jobs):
        job_colors[job.id] = COLORS[idx % len(COLORS)]

    for job in job_order:
        ops = ops_by_job.get(job.id, [])
        for op in ops:
            machine = next((m for m in machines if m.id == op.machine_id), None)
            if machine is None:
                continue
            setup = machine.temps_setup if machine.temps_setup else 0
            start = max(machine_available.get(op.machine_id, 0), job_end.get(job.id, 0)) + setup
            end = start + op.duree
            machine_available[op.machine_id] = end
            job_end[job.id] = end

            schedule.append({
                "operation_id": op.id,
                "job_id": job.id,
                "job_nom": job.nom,
                "machine_id": op.machine_id,
                "machine_nom": machine.nom if machine else "—",
                "start": start,
                "end": end,
                "duree": op.duree,
            })

            gantt.append({
                "id": f"op_{op.id}",
                "name": f"{job.nom} — {machine.nom if machine else '?'}",
                "start": start,
                "end": end,
                "machine": machine.nom if machine else "?",
                "job": job.nom,
                "color": job_colors.get(job.id, "#2563EB"),
                "custom_class": f"job-{job.id}",
            })

    return schedule, gantt


# ══════════════════════════════════════════════════════════════════════════════
# SPT — Shortest Processing Time
# ══════════════════════════════════════════════════════════════════════════════

def run_spt(jobs, machines, operations):
    """Trier les jobs par durée totale croissante."""
    ops_by_job = {}
    for op in operations:
        ops_by_job.setdefault(op.job_id, [])
        ops_by_job[op.job_id].append(op)

    def total_duration(job):
        return sum(o.duree for o in ops_by_job.get(job.id, []))

    ordered = sorted(jobs, key=total_duration)
    schedule, gantt = _build_schedule(jobs, machines, operations, ordered)
    return {"schedule": schedule, "gantt": gantt, "algorithme": "SPT"}


# ══════════════════════════════════════════════════════════════════════════════
# LPT — Longest Processing Time
# ══════════════════════════════════════════════════════════════════════════════

def run_lpt(jobs, machines, operations):
    """Trier les jobs par durée totale décroissante."""
    ops_by_job = {}
    for op in operations:
        ops_by_job.setdefault(op.job_id, [])
        ops_by_job[op.job_id].append(op)

    def total_duration(job):
        return sum(o.duree for o in ops_by_job.get(job.id, []))

    ordered = sorted(jobs, key=total_duration, reverse=True)
    schedule, gantt = _build_schedule(jobs, machines, operations, ordered)
    return {"schedule": schedule, "gantt": gantt, "algorithme": "LPT"}


# ══════════════════════════════════════════════════════════════════════════════
# EDD — Earliest Due Date
# ══════════════════════════════════════════════════════════════════════════════

def run_edd(jobs, machines, operations):
    """Trier les jobs par date d'échéance croissante (jobs sans date à la fin)."""
    def due_key(job):
        if job.date_due:
            return job.date_due.timestamp()
        return float("inf")

    ordered = sorted(jobs, key=due_key)
    schedule, gantt = _build_schedule(jobs, machines, operations, ordered)
    return {"schedule": schedule, "gantt": gantt, "algorithme": "EDD"}


# ══════════════════════════════════════════════════════════════════════════════
# GENETIC — Algorithme Génétique simplifié
# ══════════════════════════════════════════════════════════════════════════════

def _makespan_of(jobs, machines, operations, order):
    """Calcule le makespan pour un ordre de jobs donné."""
    schedule, _ = _build_schedule(jobs, machines, operations, order)
    if not schedule:
        return float("inf")
    return max(s["end"] for s in schedule)


def _crossover(parent1, parent2):
    """Order crossover (OX)."""
    n = len(parent1)
    if n <= 1:
        return parent1[:]
    a, b = sorted(random.sample(range(n), 2))
    child = [None] * n
    child[a:b+1] = parent1[a:b+1]
    filled = set(x.id for x in child[a:b+1])
    pos = (b + 1) % n
    for gene in parent2:
        if gene.id not in filled:
            child[pos] = gene
            filled.add(gene.id)
            pos = (pos + 1) % n
    return child


def _mutate(individual, mutation_rate=0.2):
    """Échange aléatoire de deux gènes."""
    ind = individual[:]
    if len(ind) > 1 and random.random() < mutation_rate:
        i, j = random.sample(range(len(ind)), 2)
        ind[i], ind[j] = ind[j], ind[i]
    return ind


def run_genetic(jobs, machines, operations,
                pop_size=20, generations=40, mutation_rate=0.25):
    """
    Algorithme génétique simplifié :
    - Population initiale aléatoire
    - Sélection par tournoi
    - Crossover OX
    - Mutation par échange
    - Élitisme : garder le meilleur
    """
    if not jobs:
        return {"schedule": [], "gantt": [], "algorithme": "GENETIC"}

    # Population initiale
    population = []
    for _ in range(pop_size):
        ind = jobs[:]
        random.shuffle(ind)
        population.append(ind)

    best_ind = None
    best_fitness = float("inf")

    for gen in range(generations):
        # Évaluation
        scored = [(ind, _makespan_of(jobs, machines, operations, ind)) for ind in population]
        scored.sort(key=lambda x: x[1])

        if scored[0][1] < best_fitness:
            best_fitness = scored[0][1]
            best_ind = scored[0][0][:]

        # Élitisme : garder le top 2
        new_pop = [scored[0][0], scored[1][0]]

        # Remplir le reste par sélection + croisement
        while len(new_pop) < pop_size:
            # Tournoi taille 3
            candidates = random.sample(scored, min(3, len(scored)))
            p1 = min(candidates, key=lambda x: x[1])[0]
            candidates2 = random.sample(scored, min(3, len(scored)))
            p2 = min(candidates2, key=lambda x: x[1])[0]

            child = _crossover(p1, p2)
            child = _mutate(child, mutation_rate)
            new_pop.append(child)

        population = new_pop

    order = best_ind if best_ind else jobs[:]
    schedule, gantt = _build_schedule(jobs, machines, operations, order)
    return {"schedule": schedule, "gantt": gantt, "algorithme": "GENETIC"}
