from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count, F, Q, Max
from django.utils import timezone
from .models import Job, Machine, Operation, Contrainte
from .forms import JobForm, MachineForm, OperationForm, ContrainteForm
from .scheduler import run_schedule
from .gantt import generate_gantt_chart

def dashboard(request):
    jobs = Job.objects.all()
    machines = Machine.objects.all()
    nb_jobs = jobs.count()
    nb_machines = machines.count()
    
    ops = Operation.objects.exclude(end_time__isnull=True)
    if ops.exists():
        makespan = (ops.aggregate(Max('end_time'))['end_time__max'] - ops.order_by('start_time').first().start_time).total_seconds() / 60
    else:
        makespan = 0
        
    retard_count = 0
    for j in jobs.exclude(statut='termine'):
        j_ops = j.operations.exclude(end_time__isnull=True)
        if j_ops.exists() and j.due_date:
            max_end = j_ops.aggregate(Max('end_time'))['end_time__max']
            if max_end > j.due_date:
                retard_count += 1
                
    taux_retard = round((retard_count / nb_jobs * 100), 2) if nb_jobs > 0 else 0
    
    context = {
        'nb_jobs': nb_jobs,
        'nb_machines': nb_machines,
        'makespan_moyen': round(makespan, 2),
        'taux_retard': taux_retard
    }
    return render(request, 'dashboard.html', context)

def job_list(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('job_list')
    else:
        form = JobForm()
    
    jobs = Job.objects.all()
    return render(request, 'jobs.html', {'jobs': jobs, 'form': form})

def machine_list(request):
    if request.method == 'POST':
        form = MachineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('machine_list')
    else:
        form = MachineForm()
    
    machines = Machine.objects.all()
    return render(request, 'machines.html', {'machines': machines, 'form': form})

def add_operation(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        form = OperationForm(request.POST)
        if form.is_valid():
            op = form.save(commit=False)
            op.job = job
            op.save()
            return redirect('add_operation', job_id=job.id)
    else:
        form = OperationForm(initial={'ordre': job.operations.count() + 1})
    
    return render(request, 'operations.html', {'job': job, 'form': form})

def constraints_list(request):
    machine_filter = request.GET.get('machine')
    type_atelier_filter = request.GET.get('type_atelier')
    retard_filter = request.GET.get('retard')
    
    jobs_query = Job.objects.all()
    
    if machine_filter:
        jobs_query = jobs_query.filter(operations__machine_id=machine_filter).distinct()
    if type_atelier_filter:
        jobs_query = jobs_query.filter(operations__machine__type_atelier=type_atelier_filter).distinct()
        
    jobs_data = []
    for job in jobs_query:
        setup_total = job.operations.aggregate(Sum('duree_preparation'))['duree_preparation__sum'] or 0
        
        # Determine makespan and retard
        ops = job.operations.exclude(end_time__isnull=True)
        makespan_val = ops.aggregate(Max('end_time'))['end_time__max'] if ops.exists() else None
        
        retard_min = 0
        if makespan_val and job.due_date:
            retard_td = makespan_val - job.due_date
            retard_min = int(retard_td.total_seconds() / 60)
            
        contraintes_count = job.contraintes_sources.count() + job.contraintes_cibles.count()
        
        # Apply retard filter
        if retard_filter == 'en_retard' and retard_min <= 0:
            continue
        elif retard_filter == 'a_temps' and retard_min > 0:
            continue
            
        jobs_data.append({
            'job': job,
            'setup_total': setup_total,
            'makespan': makespan_val,
            'retard_min': retard_min,
            'contraintes_count': contraintes_count,
        })
        
    machines = Machine.objects.all()
    
    return render(request, 'constraints.html', {
        'jobs_data': jobs_data,
        'machines': machines,
        'machine_val': machine_filter,
        'type_atelier_val': type_atelier_filter,
        'retard_val': retard_filter,
    })

def schedule_view(request):
    algo = request.GET.get('algo', 'SPT')
    run_schedule(algo=algo)
    return redirect('dashboard')

def gantt_view(request):
    algo = request.GET.get('algo', 'SPT')
    plot_html = generate_gantt_chart()
    return render(request, 'gantt.html', {'plot_html': plot_html, 'algo': algo})
