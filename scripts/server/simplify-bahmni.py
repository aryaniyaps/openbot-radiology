#!/usr/bin/env python3
"""Apply the scoped radiology presentation to an extracted native config."""
import json
import pathlib

base = pathlib.Path('/opt/kauvery-hospital/bahmni-config/openmrs/apps')
for name in ['dashboard.json', 'visit.json']:
    file = base / 'clinical' / name
    data = json.loads(file.read_text())
    for tab in data.values():
        if not isinstance(tab, dict) or 'sections' not in tab:
            continue
        keep = ['patientInformation', 'basicDetails', 'visits', 'pacsOrders', 'radiologyOrders', 'radiology', 'formsDisplay']
        tab['sections'] = {key: value for key, value in tab['sections'].items() if key in keep}
        for section in tab['sections'].values():
            if section.get('type') == 'pacsOrders':
                section.setdefault('dashboardConfig', {})['pacsImageUrl'] = '/open-study.html?patientID={{patientID}}&accessionNumber={{orderNumber}}'
    file.write_text(json.dumps(data, indent=2))
file = base / 'clinical/app.json'
data = json.loads(file.read_text())
data['config']['orderTypeClassMap'] = {'Radiology Orders': ['Radiology', 'Radiology/Imaging Procedure']}
data['config']['otherInvestigationsMap'] = {'Radiology': 'Radiology Order'}
file.write_text(json.dumps(data, indent=2))
file = base / 'home/extension.json'
data = json.loads(file.read_text())
data = {key: value for key, value in data.items() if key in ['registration', 'clinical', 'orders']}
file.write_text(json.dumps(data, indent=2))
print('Native radiology presentation configured')
