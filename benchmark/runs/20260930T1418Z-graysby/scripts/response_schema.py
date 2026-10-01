"""Shared frozen output validation; invalid structures are operational failures."""
import math
def validate(v,classes):
 required={'primary_diagnosis','findings_status','key_findings','image_references','urgent_findings','confidence','abstention','limitations'}
 assert isinstance(v,dict) and required.issubset(v),'Missing required response fields'
 assert isinstance(v['primary_diagnosis'],str) and v['primary_diagnosis'].strip(),'Missing conclusion'
 assert isinstance(v['findings_status'],dict) and set(v['findings_status'])==set(classes),'Task keys mismatch'
 assert all(x in ['present','absent','uncertain','unassessable'] for x in v['findings_status'].values()),'Invalid status'
 assert type(v['abstention']) is bool,'Abstention must be boolean'
 assert type(v['confidence']) in [int,float] and math.isfinite(v['confidence']) and 0<=v['confidence']<=1,'Invalid confidence'
 for k in ['key_findings','image_references','urgent_findings','limitations']:assert isinstance(v[k],list) and all(isinstance(x,str) for x in v[k]),'Invalid '+k
 return v
