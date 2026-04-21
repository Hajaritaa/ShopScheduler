import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from .models import Planning, MaintenanceSlot, Job, Machine, PlanningOperation

COLORS = ['#00d4ff', '#7c3aed', '#00ff88', '#ffaa00', '#ff4444', '#f1f5f9', '#ff00aa', '#00ffee', '#aaff00', '#8892a4']

def generate_gantt_chart(planning_id, compare_planning_id=None):
    try:
        planning = Planning.objects.get(id=planning_id)
    except Planning.DoesNotExist:
        return "<div class='text-danger'>Planning introuvable.</div>"

    ops = planning.planning_operations.select_related('operation__job', 'operation__machine').order_by('start_time')
    if not ops.exists():
        return "<div class='alert alert-info'>Aucune opération planifiée.</div>"

    fig = go.Figure()
    
    # Construction du dataframe pour faciliter le groupement / colors
    df_data = []
    job_ids = set()
    for po in ops:
        j = po.operation.job
        m = po.operation.machine
        job_ids.add(j.id)
        df_data.append({
            'Machine': m.nom,
            'Start': po.start_time,
            'Finish': po.end_time,
            'Job': j.nom,
            'Job_ID': j.id,
            'Opération': f"Op {po.operation.ordre}",
            'Setup': po.operation.duree_preparation,
            'Durée': po.operation.duree_execution,
            'Due Date': j.due_date.strftime('%Y-%m-%d %H:%M') if j.due_date else "N/A",
            'Retard': round(po.retard, 1),
            'Hover': f"<b>{j.nom}</b><br>{m.nom} - Op {po.operation.ordre}<br>Setup: {po.operation.duree_preparation} min<br>Durée: {po.operation.duree_execution} min<br>Retard: {round(po.retard,1)} min"
        })
        
    df = pd.DataFrame(df_data)
    
    machines = df['Machine'].unique().tolist()
    sorted_jobs = list(job_ids)
    
    # Traces principales
    for i, j_id in enumerate(sorted_jobs):
        j_df = df[df['Job_ID'] == j_id]
        if j_df.empty: continue
        
        j_nom = j_df.iloc[0]['Job']
        color = COLORS[i % len(COLORS)]
        
        # Ajout comme barres
        for _, row in j_df.iterrows():
            duration_ms = (row['Finish'] - row['Start']).total_seconds() * 1000
            
            fig.add_trace(go.Bar(
                name=j_nom,
                y=[row['Machine']],
                x=[duration_ms],
                base=[row['Start'].timestamp() * 1000],
                orientation='h',
                marker=dict(
                    color=color,
                    line=dict(color='rgba(255,255,255,0.2)', width=1)
                ),
                text=row['Opération'],
                textposition='inside',
                insidetextfont=dict(color='#0a0e1a', size=11, family='Inter, sans-serif', weight='bold'),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=[row['Hover']],
                legendgroup=j_nom,
                showlegend=(True if _ == 0 else False),
                opacity=0.9
            ))
            
    # Lignes verticales pour Due dates
    jobs = Job.objects.filter(id__in=job_ids)
    for j in jobs:
        if j.due_date:
            fig.add_vline(
                x=j.due_date.timestamp() * 1000, 
                line_width=2, line_dash="dash", line_color="#ff4444",
                annotation_text=f"Due {j.nom}", 
                annotation_position="top left",
                annotation_font_color="#ff4444"
            )

    # Zones de maintenance
    maintenances = MaintenanceSlot.objects.filter(machine__nom__in=machines)
    for maint in maintenances:
        fig.add_shape(
            type="rect",
            x0=maint.debut.timestamp() * 1000, y0=-0.5 + machines.index(maint.machine.nom),
            x1=maint.fin.timestamp() * 1000, y1=0.5 + machines.index(maint.machine.nom),
            fillcolor="rgba(255, 170, 0, 0.2)",
            line=dict(width=1, color="#ffaa00", dash="dot"),
            layer="below"
        )
            
    # Layout UI
    fig.update_layout(
        title=f"Gantt : {planning.nom}",
        font=dict(family="Inter, sans-serif", color="#f1f5f9"),
        paper_bgcolor='#0a0e1a',
        plot_bgcolor='#111827',
        barmode='stack',
        xaxis=dict(
            type='date',
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            rangeslider=dict(visible=True, bgcolor='#1a2035')
        ),
        yaxis=dict(
            autorange="reversed",
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(weight='bold')
        ),
        sliders=[],
        hoverlabel=dict(bgcolor="#111827", font_size=12, font_family="Inter", bordercolor="#00d4ff"),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Boutons custom
    config = {
        'displayModeBar': True,
        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
        'displaylogo': False,
        'toImageButtonOptions': {'format': 'png', 'filename': 'gantt_export', 'scale': 2}
    }

    return fig.to_html(full_html=False, include_plotlyjs='cdn', config=config)
