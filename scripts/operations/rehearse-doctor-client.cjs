/* Doctor journey using deployed UI and native authentication; no secrets logged. */
const fs=require('fs'),path=require('path'),cp=require('child_process');
const ROOT=path.resolve(__dirname,'../..'),ORIGINAL='/home/aryan/ai-projects/openbot-radiology';
const {chromium}=require(ORIGINAL+'/.private/browser/node_modules/playwright');
const CLI=ORIGINAL+'/.private/browser/node_modules/.bin/agent-browser';
const OUT=ROOT+'/docs/evidence/hospital-deployment';
(async()=>{
 const endpoint=cp.execFileSync(CLI,['--session','hospital-doctor','get','cdp-url'],{encoding:'utf8'}).trim();
 const browser=await chromium.connectOverCDP(endpoint),a=JSON.parse(fs.readFileSync(ROOT+'/.private/doctor-client-auth.json'));
 const context=await browser.newContext({httpCredentials:{...a.doctor,origin:'https://doctor.radiology.demo'},viewport:{width:1440,height:1000},recordVideo:{dir:ROOT+'/.private/doctor-browser-video',size:{width:1440,height:1000}}});
 const page=await context.newPage();page.setDefaultTimeout(45000);
 try{
  await page.goto('https://doctor.radiology.demo/worklist/');await page.getByRole('button',{name:'Open case',exact:true}).first().waitFor();
  if(await page.getByRole('button',{name:'Open case',exact:true}).count()!==5)throw Error('Five practice cases not visible');
  await page.getByRole('button',{name:'CT',exact:true}).click();if(await page.getByRole('button',{name:'Open case',exact:true}).count()!==1)throw Error('Modality filter failed');
  await page.getByRole('button',{name:'All',exact:true}).click();await page.getByRole('searchbox').fill('NO-SUCH-PATIENT');if(await page.getByRole('button',{name:'Open case',exact:true}).count()!==0)throw Error('Patient search failed');await page.getByRole('searchbox').fill('');
  await page.getByRole('button',{name:'Open case',exact:true}).first().click();await page.screenshot({path:OUT+'/doctor-worklist.png',fullPage:true});
  const cases=JSON.parse(fs.readFileSync(ROOT+'/config/doctor/cases.json')),c=cases[0];
  const record=await page.locator('#record').getAttribute('href'),images=await page.locator('#images').getAttribute('href'),report=await page.locator('#report').getAttribute('href');
  if(!record.includes(c.patient)||!images.includes(c.patient_id)||!images.includes(c.accession)||!report.includes(c.patient))throw Error('Case links do not preserve identity');
  const hospital=await context.newPage();hospital.setDefaultTimeout(60000);
  await hospital.goto('https://radiology.demo/bahmni/home/#/login');
  await hospital.getByRole('textbox',{name:'Username *'}).fill(a.hospital.username);await hospital.getByRole('textbox',{name:'Password *'}).fill(a.hospital.password);await hospital.getByRole('button',{name:'Login',exact:true}).click();
  await hospital.getByRole('button',{name:'Continue',exact:true}).waitFor();const locations=hospital.locator('select').last();await locations.selectOption({label:'OPD-1'});await hospital.getByRole('button',{name:'Continue',exact:true}).click();await hospital.waitForURL(/dashboard/);
  await hospital.goto(record);await hospital.waitForFunction(id=>document.body.innerText.includes(id),c.patient_id);await hospital.screenshot({path:OUT+'/doctor-patient-record.png',fullPage:true});
  const viewer=await context.newPage();viewer.setDefaultTimeout(90000);await viewer.goto(images);await viewer.waitForURL(/\/viewer\/viewer/);
  await viewer.waitForTimeout(3500);for(const text of ['Skip all','Confirm and hide']){const button=viewer.getByText(text,{exact:true});if(await button.isVisible().catch(()=>false))await button.click()}
  await viewer.locator('canvas').first().waitFor();await viewer.waitForTimeout(2500);await viewer.screenshot({path:OUT+'/doctor-images.png',fullPage:true});
  await page.getByRole('button',{name:'Prepare this case',exact:true}).click();await page.getByRole('status').filter({hasText:'Case preparation started'}).waitFor();
  const bots=await page.evaluate(async()=> (await(await fetch('/api/bots')).json()).bots),bot=bots.find(b=>b.name==='Clinical Assistant');
  const native=await context.newPage();await native.goto('https://doctor.radiology.demo/');await native.waitForTimeout(1500);await native.screenshot({path:OUT+'/doctor-assistant-started.png',fullPage:true});
  const assignment={case:c,coordinator_id:bot.id,thread_id:bot.threadId,started_unix:Date.now()/1000,report_url:report};
  fs.writeFileSync(ROOT+'/.private/doctor-workflow-assignment.json',JSON.stringify(assignment,null,2));
  fs.writeFileSync(OUT+'/doctor-journey-start.json',JSON.stringify({status:'started',five_cases_visible:true,modality_and_patient_filters_passed:true,identity_preserved_in_links:true,physician_login_passed:true,native_chart_opened:true,native_viewer_opened:true,case_id:c.patient_id,accession:c.accession,thread_id:bot.threadId},null,2));
  console.log('Doctor case selection, native chart, native viewer and restricted assistant case launch passed',c.patient_id,c.accession);
 }finally{await context.close();await browser.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
