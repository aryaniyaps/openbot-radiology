#!/usr/bin/env python3
"""Pinned benchmark-only MedGemma OpenAI-compatible image endpoint; no retrieval/tools."""
import os,pathlib,json,time,hashlib,base64,io,http.server,threading,subprocess,uuid
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2')
import torch,transformers
from transformers import AutoModelForImageTextToText,AutoProcessor,BitsAndBytesConfig
from PIL import Image
R=pathlib.Path(__file__).resolve().parents[1];MODEL='google/medgemma-1.5-4b-it';REV='91850547d9f0b2fdd21aa7c5f4f3d1a8a52c243b';KEY=(R/'private/medgemma-api-key').read_text().strip();torch.set_num_threads(2)
assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>6*1024**3,'Insufficient unused GPU capacity; do not displace other workloads'
torch.cuda.set_per_process_memory_fraction(.60)
start=time.monotonic();processor=AutoProcessor.from_pretrained(R/'private/medgemma15-model',local_files_only=True,use_fast=False)
quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
model=AutoModelForImageTextToText.from_pretrained(R/'private/medgemma15-model',local_files_only=True,quantization_config=quant,torch_dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa').eval()
original_image_features=model.model.get_image_features
def bounded_image_features(pixel_values):
 return torch.cat([original_image_features(pixel_values[i:i+1]) for i in range(pixel_values.shape[0])],dim=0)
model.model.get_image_features=bounded_image_features
info={'model':MODEL,'revision':REV,'quantization':'NF4 double quantization','compute_dtype':'bfloat16','transformers':transformers.__version__,'torch':torch.__version__,'load_seconds':time.monotonic()-start,'max_new_tokens':1600,'max_input_tokens':6000,'max_images':4,'gpu_allocator_fraction':.60,'cpu_threads':2,'tools':False,'network_image_fetch':False,'fallback':False,'vision_encoder_batch_size':1,'processor_pan_and_scan':False,'pan_and_scan_activation_ratio':1.2,'pan_and_scan_min_crop_size':256,'pan_and_scan_max_num_crops':4,'repetition_penalty':1.10,'no_repeat_ngram_size':12,'system_context':'Expert research imaging interpreter; only final supplied case user message and its images, excludes platform startup greeting','generation_prefill':'<unused95> final channel, selected on development only','output_channel_handling':'Return final channel after unused95 marker, retain complete generated text privately'}
(R/'evidence/medgemma-serving-config.json').write_text(json.dumps(info,indent=2)+'\n');print('MedGemma ready',json.dumps(info),flush=True);lock=threading.Lock()
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def emit(self,status,data):
  b=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  if self.path=='/v1/models':return self.emit(200,{'object':'list','data':[{'id':MODEL,'object':'model','owned_by':'benchmark-local'}]})
  if self.path=='/health':return self.emit(200,dict(info,gpu_allocated_bytes=torch.cuda.memory_allocated()))
  return self.emit(404,{'error':'Unknown owned endpoint'})
 def do_POST(self):
  if self.path!='/v1/chat/completions':return self.emit(404,{'error':'Unknown endpoint'})
  if self.headers.get('Authorization')!='Bearer '+KEY:return self.emit(401,{'error':'Invalid local benchmark authorization'})
  if not lock.acquire(blocking=False):return self.emit(429,{'error':'One benchmark inference at a time'})
  record={'started_unix':time.time(),'status':'failed'}
  try:
   n=int(self.headers.get('Content-Length','0'));assert 0<n<=55*1024**2,'Request size exceeded';d=json.loads(self.rfile.read(n));assert d['model']==MODEL,'Model mismatch';assert not d.get('tools'),'Tools forbidden'
   # Input consists exclusively of the request's supplied visual/text evidence.
   messages=[];images=[]
   for m in d['messages']:
    assert m['role'] in ['system','user','assistant'],'Unsupported role';content=m.get('content',[])
    if isinstance(content,str):content=[{'type':'text','text':content}]
    converted=[]
    for part in content:
     if part['type']=='text':converted.append({'type':'text','text':part['text']})
     elif part['type']=='image_url':
      u=part['image_url']['url'];assert u.startswith(('data:image/png;base64,','data:image/jpeg;base64,')),'Only supplied PNG/JPEG bytes accepted';b=base64.b64decode(u.split(',',1)[1],validate=True);assert len(b)<=10*1024**2,'Image budget';im=Image.open(io.BytesIO(b)).convert('RGB');assert im.width*im.height<=20_000_000,'Image pixel budget';images.append({'sha256':hashlib.sha256(b).hexdigest(),'width':im.width,'height':im.height});converted.append({'type':'image','image':im})
     else:raise ValueError('Unsupported visual input type')
    messages.append({'role':m['role'],'content':converted})
   # Preserve all supplied text/images while coalescing consecutive equal roles.
   # OpenMausbot may split platform instructions and current user visual input.
   merged=[]
   for m in messages:
    if merged and merged[-1]['role']==m['role']:merged[-1]['content']+=m['content']
    else:merged.append(m)
   first=next((i for i,m in enumerate(merged) if m['role']!='system'),len(merged))
   if first<len(merged) and merged[first]['role']=='assistant':
    merged.insert(first,{'role':'user','content':[{'type':'text','text':'Conversation initialization.'}]})
   messages=[{'role':'system','content':[{'type':'text','text':'You are an expert research imaging interpreter. All supplied images belong to one patient study. Use only the explicitly supplied modality context and images. Return only strictly valid JSON as requested, no comments. Confidence must be a decimal from 0 to 1, for example 0.8.'}]},next(m for m in reversed(merged) if m['role']=='user')]
   record['message_roles']=[m['role'] for m in messages]
   assert 1<=len(images)<=4,'Visual evidence required; maximum four images'
   assert torch.cuda.mem_get_info()[0]>1536*1024**2,'GPU headroom constrained; pause benchmark'
   inputs=processor.apply_chat_template(messages,add_generation_prompt=True,tokenize=True,return_dict=True,return_tensors='pt',do_pan_and_scan=False).to(model.device,dtype=torch.bfloat16);input_len=inputs['input_ids'].shape[-1];record['processed_image_tensor_shape']=list(inputs['pixel_values'].shape);assert input_len<=6000,'Input context budget exceeded'
   # Development-selected final-channel prefill; prevents verbose thought exhausting the answer budget.
   prefix=processor.tokenizer('<unused95>\n',add_special_tokens=False,return_tensors='pt')['input_ids'].to(model.device)
   inputs['input_ids']=torch.cat([inputs['input_ids'],prefix],dim=1)
   inputs['attention_mask']=torch.cat([inputs['attention_mask'],torch.ones_like(prefix)],dim=1)
   if 'token_type_ids' in inputs:inputs['token_type_ids']=torch.cat([inputs['token_type_ids'],torch.zeros_like(prefix)],dim=1)
   input_len=inputs['input_ids'].shape[-1];record['generation_prefill']='<unused95>\n'
   torch.cuda.reset_peak_memory_stats();begin=time.monotonic()
   with torch.inference_mode():out=model.generate(**inputs,max_new_tokens=1600,do_sample=False,max_time=130,repetition_penalty=1.10,no_repeat_ngram_size=12)
   generated=out[0][input_len:];text=processor.decode(generated,skip_special_tokens=True);usage={'prompt_tokens':input_len,'completion_tokens':len(generated),'total_tokens':input_len+len(generated)};record.update(status='succeeded',inference_seconds=time.monotonic()-begin,usage=usage,images=images,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),text=text,model=MODEL,revision=REV)
   text=text.rsplit('<unused95>',1)[-1] if '<unused95>' in text else text
   text=text.replace('<end_of_turn>','').strip()
   rid='bench-'+str(uuid.uuid4());result={'id':rid,'object':'chat.completion','created':int(time.time()),'model':MODEL,'choices':[{'index':0,'message':{'role':'assistant','content':text},'finish_reason':'length' if len(generated)>=1600 else 'stop'}],'usage':usage}
   if d.get('stream'):
    self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
    for c in [{'id':rid,'object':'chat.completion.chunk','model':MODEL,'choices':[{'index':0,'delta':{'role':'assistant','content':text},'finish_reason':None}]},{'id':rid,'object':'chat.completion.chunk','model':MODEL,'choices':[{'index':0,'delta':{},'finish_reason':result['choices'][0]['finish_reason']}],'usage':usage}]:self.wfile.write(('data: '+json.dumps(c)+'\n\n').encode())
    self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush()
   else:self.emit(200,result)
  except Exception as e:
   record['error']=type(e).__name__+': '+str(e)[:400];self.emit(503,{'error':{'message':record['error'],'type':'benchmark_local_failure'}})
  finally:
   record['finished_unix']=time.time();p=R/'private/medgemma-inferences.jsonl'
   with p.open('a') as f:f.write(json.dumps(record)+'\n')
   lock.release()
http.server.ThreadingHTTPServer(('127.0.0.1',18898),Handler).serve_forever()
