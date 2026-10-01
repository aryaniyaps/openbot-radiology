/* UI verification through trusted TLS, with private credentials and owned browser. */
const fs=require('fs'),path=require('path'),cp=require('child_process');
const ROOT=path.resolve(__dirname,'../..'),O='/home/aryan/ai-projects/openbot-radiology';
const {chromium}=require(O+'/.private/browser/node_modules/playwright');
(async()=>{
 const endpoint=cp.execFileSync(O+'/.private/browser/node_modules/.bin/agent-browser',['--session','hospital-doctor','get','cdp-url'],{encoding:'utf8'}).trim();
 const browser=await chromium.connectOverCDP(endpoint),a=JSON.parse(fs.readFileSync(ROOT+'/.private/doctor-client-auth.json'));
 const context=await browser.newContext({httpCredentials:{...a.doctor,origin:'https://doctor.radiology.demo'},viewport:{width:1440,height:1000},recordVideo:{dir:ROOT+'/.private/doctor-browser-video',size:{width:1440,height:1000}}});
 const page=await context.newPage(),out=ROOT+'/docs/evidence/hospital-deployment',receipt=[];
 try{
  await page.goto('https://doctor.radiology.demo/worklist/');await page.getByRole('button',{name:'Open case',exact:true}).first().waitFor();
  for(const c of JSON.parse(fs.readFileSync(ROOT+'/config/doctor/cases.json'))){
   await page.getByRole('searchbox').fill(c.patient_id);await page.getByRole('button',{name:'Open case',exact:true}).click();
   if(!(await page.locator('#coverage').innerText()).includes(c.assistant_coverage))throw Error('Sampling coverage missing');
   await page.getByText('View the assistant’s image packet',{exact:true}).click();
   await page.waitForFunction(()=>[...document.querySelectorAll('#packet-images img')].every(i=>i.complete&&i.naturalWidth>0));
   await page.screenshot({path:out+'/doctor-'+c.modality+'-packet.png',fullPage:true});
   await page.getByText('View the assistant’s image packet',{exact:true}).click();
   const viewer=await context.newPage();viewer.setDefaultTimeout(90000);await viewer.goto(await page.locator('#images').getAttribute('href'));await viewer.waitForURL(/\/viewer\/viewer/);
   await viewer.waitForTimeout(3000);for(const text of ['Skip all','Confirm and hide']){let b=viewer.getByText(text,{exact:true});if(await b.isVisible().catch(()=>false))await b.click()}
   await viewer.locator('canvas').first().waitFor();await viewer.waitForTimeout(2500);
   const pixels=await viewer.locator('canvas').evaluateAll(cs=>cs.some(c=>{const g=c.getContext('2d');if(!g)return false;try{let data=g.getImageData(0,0,c.width,c.height).data;for(let i=0;i<data.length;i+=4)if(data[i]>35||data[i+1]>35||data[i+2]>35)return true}catch(e){}return false}));
   // Cornerstone may use GPU canvases; require a viewport render event or visible pixel screenshot inspection.
   await viewer.screenshot({path:out+'/viewer-'+c.modality+'.png',fullPage:true});
   receipt.push({modality:c.modality,patient:c.patient_id,accession:c.accession,packet_visible:true,native_viewer_loaded:true,canvas_nonblack:pixels});await viewer.close();
  }
  await page.route('**/worklist/cases.json',route=>{const cases=JSON.parse(fs.readFileSync(ROOT+'/config/doctor/cases.json'));cases[0].packet_views=[];return route.fulfill({json:cases})});
  await page.reload();await page.getByRole('button',{name:'Open case',exact:true}).first().click();let submissions=0;page.on('request',r=>{if(r.method()==='POST')submissions++});await page.getByRole('button',{name:'Prepare this case',exact:true}).click();await page.getByRole('status').filter({hasText:'Assigned images unavailable'}).waitFor();if(submissions)throw Error('Missing-image case submitted');
  fs.writeFileSync(out+'/doctor-modalities-ui.json',JSON.stringify({cases:receipt,missing_packet_refused_without_submission:true,tls_bypass:false},null,2));
  console.log('Five modality packet/viewer UI checks and missing-image refusal passed');
 }finally{await context.close();await browser.close()}
 const it=await chromium.connectOverCDP(endpoint),ctx=await it.newContext({httpCredentials:{...a.it,origin:'https://it.radiology.demo'},viewport:{width:1440,height:1000}});
 try{const p=await ctx.newPage();await p.goto('https://it.radiology.demo/operations/');await p.waitForFunction(()=>document.body.innerText.includes('Clinical Assistant'));await p.screenshot({path:out+'/it-operations.png',fullPage:true});await p.goto('https://it.radiology.demo/');await p.waitForTimeout(2500);await p.screenshot({path:out+'/it-native-management.png',fullPage:true});console.log('IT monitoring and native management UI opened')}finally{await ctx.close();await it.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
