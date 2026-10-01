import pathlib,json,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=pathlib.Path(__file__).resolve().parents[1];rows=json.loads((R/'report/assignment-results.json').read_text());fig,axes=plt.subplots(1,3,figsize=(16,6),constrained_layout=True)
colors={'valid':'#31857c','failed':'#c97452','pending':'#d9dfe7'}
for ax,mod in zip(axes,['CXR','CT','MR']):
 groups=[]
 for arm in ['B','A']:
  models=['gpt-6-luna','gpt-6.1-sol','gpt-6-astra']+(['google/medgemma-1.5-4b-it'] if arm=='B' else [])
  for model in models:
   rr=[r for r in rows if r['stage']=='evaluation' and r['modality']==mod and r['arm']==arm and r['model']==model and r['configuration']=='primary' and not r['attempt']]
   counts={'valid':sum(r['valid_structured'] for r in rr),'failed':sum(not r['valid_structured'] and r['execution_status']!='not_run' for r in rr),'pending':sum(r['execution_status']=='not_run' for r in rr)};groups.append((arm+' '+model.replace('google/medgemma-1.5-4b-it','MedGemma 4B'),counts,len(rr)))
 for i,(label,c,n) in enumerate(groups):
  left=0
  for status in ['valid','failed','pending']:
   ax.barh(i,c[status],left=left,color=colors[status],label=('failed / unqualified' if status=='failed' else status) if i==0 else None);left+=c[status]
  ax.text(n+.6,i,str(c['valid'])+'/'+str(n),va='center',fontsize=9)
 ax.set_yticks(range(len(groups)),[g[0] for g in groups]);ax.invert_yaxis();ax.set_title(mod);ax.set_xlabel('Assigned studies: valid / assigned at right');ax.spines[['top','right']].set_visible(False);ax.set_xlim(0,max(g[2] for g in groups)*1.18);ax.legend(loc='lower right',fontsize=8)
fig.suptitle('Primary response capture — valid response is not diagnostic correctness\nA: graphical viewer / B: supplied visual inputs; unqualified includes 18 exposed CT viewer contexts',fontsize=14)
fig.savefig(R/'report/execution-progress.png',dpi=160);fig.savefig(R/'report/execution-progress.svg');plt.close(fig)

# Released-study task fractions; OpenI study IDs do not prove longitudinal patient independence.
from binary_metrics import proportion
metrics=json.loads((R/'report/task-metrics.json').read_text())
models=['gpt-6-luna','gpt-6.1-sol','gpt-6-astra','google/medgemma-1.5-4b-it']
palette=['#0072B2','#E69F00','#009E73','#CC79A7']
fig,axes=plt.subplots(2,3,figsize=(17,10),constrained_layout=True)
for column,mod in enumerate(['CXR','CT','MR']):
 selected=[x for x in metrics if x['stage']=='evaluation' and x['arm']=='B' and x['configuration']=='primary' and not x['attempt'] and x['modality']==mod]
 labels=list(dict.fromkeys(x['task'] for x in selected))
 for row,(reference,confusion,title) in enumerate([('reference_positive','TP','Report-positive findings resolved'),('reference_negative','TN','Report-negative findings resolved')]):
  ax=axes[row,column]
  for m,(model,color) in enumerate(zip(models,palette)):
   for k,label in enumerate(labels):
    x=next(z for z in selected if z['model']==model and z['task']==label)
    p=proportion(x['diagnostic_confusion_counts'][confusion],x[reference])
    if p['estimate'] is None:continue
    y=100*p['estimate'];lo,hi=[100*v for v in p['ci95']]
    pending=x['status_counts'].get('not_run',0)>0
    if pending:continue
    ax.errorbar(k+(m-1.5)*.15,y,yerr=[[max(0,y-lo)],[max(0,hi-y)]],fmt='o',capsize=3,color=color,alpha=.4 if pending else 1,label=model.replace('google/medgemma-1.5-4b-it','MedGemma1.5 4B NF4') if k==0 else None)
  counts=[next(z for z in selected if z['task']==label)[reference] for label in labels]
  ax.set_xticks(range(len(labels)),[label.replace('_','\n')+'\nn='+str(n) for label,n in zip(labels,counts)],fontsize=8)
  ax.set_ylim(-5,105);ax.set_ylabel('Successful assigned finding resolution (%)');ax.set_title(mod+' — '+title,fontsize=10);ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
  if not any(counts):ax.text(.5,.5,'No explicit report negatives\nSpecificity is not estimable',ha='center',va='center',transform=ax.transAxes)
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([],[],marker='o',linestyle='',color=color,label=model.replace('google/medgemma-1.5-4b-it','MedGemma1.5 4B NF4')) for model,color in zip(models,palette)],fontsize=9,loc='outside lower center',ncol=4)
fig.suptitle('Direct-input finding resolution with study-level Wilson 95% intervals\nNot clinical accuracy: failures/abstentions unresolved; groups with pending cases are omitted\nMRI WM n=5 includes two normal-impression reports: coded signal-foci assertions, not confirmed pathological diagnoses',fontsize=12)
fig.savefig(R/'report/finding-resolution.png',dpi=160);fig.savefig(R/'report/finding-resolution.svg');plt.close(fig)
