import pathlib,subprocess,time,json,datetime
R=pathlib.Path(__file__).resolve().parents[1];deadline=datetime.datetime(2026,10,1,1,0,tzinfo=datetime.timezone.utc).timestamp();seen=False
while True:
 p=subprocess.run(['sudo','-n','/usr/bin/python3',str(R/'scripts/build_report.py')],capture_output=True,text=True)
 subprocess.run(['sudo','-n','/usr/bin/python3',str(R/'scripts/plot_report.py')],capture_output=True,text=True)
 with (R/'private/report-watch.log').open('a') as f:f.write(str(time.time())+' '+p.stdout+p.stderr)
 if time.time()>=deadline and not seen:
  checkpoint=json.loads(subprocess.check_output(['sudo','-n','cat',str(R/'report/checkpoint.json')]));checkpoint['deadline']='2026-10-01 06:30 Asia/Kolkata';checkpoint['remaining_assignments']=checkpoint['assigned']-checkpoint['recorded_outcomes'];(R/'evidence/morning-checkpoint.json').write_text(json.dumps(checkpoint,indent=2));seen=True
 events=[json.loads(line) for line in (R/'evidence/batch-events.jsonl').read_text().splitlines()] if (R/'evidence/batch-events.jsonl').exists() else []
 completed=[d for d in events if d.get('batch_complete')]
 if completed and not completed[-1].get('stopped_by_budget_or_safety'):
  checkpoint=json.loads(subprocess.check_output(['sudo','-n','cat',str(R/'report/checkpoint.json')]))
  if checkpoint['recorded_outcomes']==checkpoint['assigned']:break
 time.sleep(60)
