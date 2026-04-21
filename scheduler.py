from .models import Job, Machine, Operation
from django.utils import timezone
import datetime

def run_schedule(algo="SPT"):
    """
    Exécute l'algorithme d'ordonnancement choisi.
    Met à jour start_time et end_time de chaque Operation.
    """
    Operation.objects.update(start_time=None, end_time=None)
    
    jobs = list(Job.objects.exclude(statut='termine').order_by('id'))
    machines = list(Machine.objects.all())
    
    if not jobs or not machines:
        return
        
    start_point = timezone.now()
    
    machine_available_time = {m.id: (m.disponible_depuis if m.disponible_depuis else start_point) for m in machines}
    job_available_time = {j.id: j.date_arrivee for j in jobs}
    
    job_ops = {}
    for j in jobs:
        job_ops[j.id] = list(j.operations.order_by('ordre'))
        
    unscheduled = sum(len(ops) for ops in job_ops.values())
    
    if algo == 'JOHNSON':
        # Algorithme de Johnson pour Flow Shop 2 machines
        fs_machines = [m for m in machines if m.type_atelier == 'flow_shop']
        if len(fs_machines) == 2:
            m1, m2 = fs_machines[0], fs_machines[1]
            u, v = [], []
            for j in jobs:
                ops = job_ops[j.id]
                if len(ops) == 2 and ops[0].machine == m1 and ops[1].machine == m2:
                    if ops[0].duree_execution <= ops[1].duree_execution:
                        u.append(j)
                    else:
                        v.append(j)
            u.sort(key=lambda x: job_ops[x.id][0].duree_execution)
            v.sort(key=lambda x: job_ops[x.id][1].duree_execution, reverse=True)
            johnson_order = u + v
            
            for j in johnson_order:
                # M1
                op1 = job_ops[j.id][0]
                m = m1
                start = max(machine_available_time[m.id], job_available_time[j.id])
                op1.start_time = start
                op1.end_time = start + datetime.timedelta(minutes=(op1.duree_preparation + op1.duree_execution))
                machine_available_time[m.id] = op1.end_time
                job_available_time[j.id] = op1.end_time
                op1.save()
                
                # M2
                op2 = job_ops[j.id][1]
                m = m2
                start = max(machine_available_time[m.id], job_available_time[j.id])
                op2.start_time = start
                op2.end_time = start + datetime.timedelta(minutes=(op2.duree_preparation + op2.duree_execution))
                machine_available_time[m.id] = op2.end_time
                job_available_time[j.id] = op2.end_time
                op2.save()
            return
            
    # File d'attente / Dispatching rules (SPT, EDD, FIFO) pour Job Shop ou machines parallèles
    while unscheduled > 0:
        available_ops = []
        for j in jobs:
            if job_ops[j.id]:
                op = job_ops[j.id][0]
                m = op.machine
                earliest_start = max(machine_available_time[m.id], job_available_time[j.id])
                available_ops.append({
                    'op': op,
                    'job': j,
                    'machine': m,
                    'earliest_start': earliest_start
                })
        
        if not available_ops:
            break
            
        min_start = min(o['earliest_start'] for o in available_ops)
        ready_ops = [o for o in available_ops if o['earliest_start'] == min_start]
        
        if algo == 'SPT':
            next_op_dict = min(ready_ops, key=lambda o: o['op'].duree_execution)
        elif algo == 'EDD':
            next_op_dict = min(ready_ops, key=lambda o: o['job'].due_date)
        elif algo == 'FIFO':
            next_op_dict = min(ready_ops, key=lambda o: o['job'].date_arrivee)
        else: # Par défaut FIFO
            next_op_dict = min(ready_ops, key=lambda o: o['job'].date_arrivee)
            
        op = next_op_dict['op']
        j = next_op_dict['job']
        m = next_op_dict['machine']
        start = next_op_dict['earliest_start']
        
        op.start_time = start
        op.end_time = start + datetime.timedelta(minutes=(op.duree_preparation + op.duree_execution))
        
        machine_available_time[m.id] = op.end_time
        job_available_time[j.id] = op.end_time
        
        op.save()
        job_ops[j.id].pop(0)
        unscheduled -= 1
