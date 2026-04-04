from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import httpx, os, psycopg

router = APIRouter()

def get_db_url():
    return os.getenv("DATABASE_URL")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Alexandra — Project Ascension</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; background: #0d1117; color: #e6edf3; font-family: 'Courier New', monospace; overflow: hidden; }
#top-bar { position: fixed; top: 0; left: 0; right: 0; height: 52px; background: #161b22; border-bottom: 1px solid #21262d; display: flex; align-items: center; padding: 0 16px; gap: 12px; z-index: 100; }
#top-left { display: flex; flex-direction: column; min-width: 140px; }
#top-title { color: #58a6ff; font-size: 1rem; font-weight: bold; }
#top-sub { color: #8b949e; font-size: 0.68rem; }
#top-badges { display: flex; gap: 6px; flex: 1; justify-content: center; flex-wrap: wrap; }
.badge { padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold; }
.badge.ok { background: #1a2f1a; color: #3fb950; border: 1px solid #3fb950; }
.badge.err { background: #2f1a1a; color: #f85149; border: 1px solid #f85149; }
.badge.loading { background: #1a1f2f; color: #8b949e; border: 1px solid #30363d; }
#hamburger-btn { background: none; border: 1px solid #30363d; color: #e6edf3; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 1rem; }
#hamburger-btn:hover { border-color: #58a6ff; color: #58a6ff; }
#overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 200; }
#overlay.open { display: block; }
#side-menu { position: fixed; top: 0; right: -420px; width: 420px; max-width: 95vw; height: 100vh; background: #161b22; border-left: 1px solid #21262d; z-index: 300; transition: right 0.25s ease; overflow-y: auto; }
#side-menu.open { right: 0; }
#menu-header { display: flex; align-items: center; justify-content: space-between; padding: 16px; border-bottom: 1px solid #21262d; }
#menu-title { color: #58a6ff; font-size: 0.9rem; font-weight: bold; }
#menu-close { background: none; border: none; color: #8b949e; font-size: 1.2rem; cursor: pointer; padding: 4px 8px; }
#menu-close:hover { color: #e6edf3; }
.menu-section { border-bottom: 1px solid #21262d; }
.menu-section-hdr { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; cursor: pointer; user-select: none; }
.menu-section-hdr:hover { background: #0d1117; }
.menu-section-title { color: #8b949e; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 2px; }
.menu-chevron { color: #8b949e; font-size: 0.85rem; transition: transform 0.2s; }
.menu-section-body { display: none; padding: 12px 16px; }
.menu-section-body.open { display: block; }
.menu-chevron.open { transform: rotate(90deg); }
.brief-text { color: #e6edf3; font-size: 0.82rem; line-height: 1.7; white-space: pre-wrap; }
.brief-meta { color: #8b949e; font-size: 0.7rem; margin-top: 8px; }
.run-item { background: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; }
.run-prompt { color: #58a6ff; font-size: 0.8rem; margin-bottom: 4px; }
.run-answer { color: #e6edf3; font-size: 0.78rem; line-height: 1.5; white-space: pre-wrap; }
.run-meta { color: #8b949e; font-size: 0.68rem; margin-top: 6px; }
.task-table { width: 100%; border-collapse: collapse; font-size: 0.75rem; }
.task-table th { color: #8b949e; text-align: left; padding: 5px 8px; border-bottom: 1px solid #21262d; }
.task-table td { padding: 5px 8px; border-bottom: 1px solid #0d1117; vertical-align: middle; }
.status-pending { color: #f0883e; } .status-approved { color: #3fb950; } .status-rejected { color: #f85149; }
.btn-approve { background: #1a2f1a; color: #3fb950; border: 1px solid #3fb950; padding: 2px 8px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; cursor: pointer; }
.btn-approve:hover { background: #3fb950; color: #0d1117; }
.btn-reject { background: #2f1a1a; color: #f85149; border: 1px solid #f85149; padding: 2px 8px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; cursor: pointer; margin-left: 3px; }
.btn-reject:hover { background: #f85149; color: #0d1117; }
#main { position: fixed; top: 52px; bottom: 58px; left: 0; right: 0; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; scroll-behavior: smooth; }
.chat-msg { max-width: 75%; display: flex; flex-direction: column; gap: 3px; }
.chat-msg.user { align-self: flex-end; align-items: flex-end; }
.chat-msg.alex { align-self: flex-start; align-items: flex-start; }
.chat-bubble { padding: 10px 14px; border-radius: 10px; font-size: 0.84rem; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
.chat-msg.user .chat-bubble { background: #1f3a6e; color: #e6edf3; border-radius: 10px 10px 2px 10px; }
.chat-msg.alex .chat-bubble { background: #161b22; color: #e6edf3; border: 1px solid #30363d; border-radius: 10px 10px 10px 2px; }
.chat-ts { color: #8b949e; font-size: 0.67rem; }
#chat-typing { color: #8b949e; font-size: 0.78rem; font-style: italic; padding: 4px 0; align-self: flex-start; }
#voice-status { position: fixed; bottom: 62px; left: 50%; transform: translateX(-50%); background: rgba(22,27,34,0.92); color: #8b949e; font-size: 0.75rem; font-style: italic; padding: 4px 14px; border-radius: 12px; border: 1px solid #30363d; pointer-events: none; opacity: 0; transition: opacity 0.2s; z-index: 50; white-space: nowrap; }
#voice-status.visible { opacity: 1; }
.rec-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #f85149; margin-right: 5px; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
#bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; height: 58px; background: #161b22; border-top: 1px solid #21262d; display: flex; align-items: center; padding: 0 12px; gap: 8px; z-index: 100; }
#chat-input { flex: 1; background: #0d1117; border: 1px solid #30363d; color: #e6edf3; padding: 9px 14px; border-radius: 6px; font-family: monospace; font-size: 0.88rem; outline: none; }
#chat-input:focus { border-color: #58a6ff; }
.bar-btn { border: none; padding: 9px 16px; border-radius: 6px; font-family: monospace; font-size: 0.88rem; cursor: pointer; }
#send-btn { background: #1f6feb; color: #fff; }
#send-btn:hover { background: #388bfd; }
#mic-btn { background: #1a2f1a; color: #3fb950; border: 1px solid #3fb950; padding: 9px 12px; border-radius: 6px; font-size: 0.9rem; cursor: pointer; }
#mic-btn:hover { background: #3fb950; color: #0d1117; }
#mic-btn.recording { background: #2f1a1a; color: #f85149; border: 1px solid #f85149; }
#cam-btn { background: #1a1f2f; color: #58a6ff; border: 1px solid #58a6ff; padding: 9px 12px; border-radius: 6px; font-size: 0.9rem; cursor: pointer; }
#cam-btn:hover { background: #58a6ff; color: #0d1117; }
  #start-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(13,17,23,0.93);z-index:999;display:flex;align-items:center;justify-content:center;cursor:pointer;}
  #start-overlay-inner{text-align:center;}
  .ol-icon{font-size:3rem;margin-bottom:16px;}
  .ol-title{font-size:1.5rem;color:#58a6ff;font-family:monospace;margin-bottom:8px;letter-spacing:2px;}
  .ol-sub{font-size:0.85rem;color:#8b949e;font-family:monospace;}
</style>
</head>
<body>
<div id="start-overlay" onclick="startSession()"><div id="start-overlay-inner"><div class="ol-icon">&#9889;</div><div class="ol-title">ALEXANDRA</div><div class="ol-sub">click anywhere to begin</div></div></div>
<div id="top-bar">
  <div id="top-left"><span id="top-title">⚡ Alexandra</span></div>
  <div id="top-badges"><span class="badge loading">loading...</span></div>
  <button id="hamburger-btn" onclick="openMenu()">☰</button>
</div>
<div id="overlay" onclick="closeMenu()"></div>
<div id="menu-overlay" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:none;z-index:99;" onclick="toggleMenu()"></div>
<div id="side-menu">
  <div id="menu-header"><span id="menu-title">⚡ Alexandra</span><button id="menu-close" onclick="closeMenu()">✕</button></div>
  <div class="menu-section">
    <div class="menu-section-hdr" onclick="toggleSection('brief')"><span class="menu-section-title">Daily Brief</span><span class="menu-chevron" id="chevron-brief">&#8250;</span></div>
    <div class="menu-section-body" id="body-brief"><div id="daily-brief" style="color:#8b949e;font-size:0.82rem">Loading...</div></div>
  </div>
  <div class="menu-section">
    <div class="menu-section-hdr" onclick="toggleSection('runs')"><span class="menu-section-title">Today Activity</span><span class="menu-chevron" id="chevron-runs">&#8250;</span></div>
    <div class="menu-section-body" id="body-runs"><div id="runs" style="color:#8b949e;font-size:0.82rem">Loading...</div></div>
  </div>
  <div class="menu-section">
    <div class="menu-section-hdr" onclick="toggleSection('tasks')"><span class="menu-section-title">Agent Tasks</span><span class="menu-chevron" id="chevron-tasks">&#8250;</span></div>
    <div class="menu-section-body" id="body-tasks"><div id="agent-tasks" style="color:#8b949e;font-size:0.82rem">Loading...</div></div>
  </div>
  <div class="menu-section">
    <div class="menu-section-hdr" onclick="toggleSection('archive')"><span class="menu-section-title">Chat History</span><span class="menu-chevron" id="chevron-archive">&#8250;</span></div>
    <div class="menu-section-body" id="body-archive"><div id="chat-archive-list" style="color:#8b949e;font-size:0.82rem">Loading...</div></div>
  </div>
</div>
<div id="main"></div>
<div id="voice-status"></div>
<div id="bottom-bar">
  <input type="text" id="chat-input" placeholder="Message Alexandra..." />
  <button class="bar-btn" id="send-btn" onclick="sendChat()">Send</button>
  <button id="mic-btn" onclick="toggleRecording()" title="Voice input">&#127908;</button>
  <button id="cam-btn" onclick="captureWebcam()" title="Camera input">&#128247;</button>
</div>
<script>
function openMenu(){document.getElementById('overlay').classList.add('open');document.getElementById('side-menu').classList.add('open');}
function closeMenu(){document.getElementById('overlay').classList.remove('open');document.getElementById('side-menu').classList.remove('open');}
function toggleMenu(){const panel=document.getElementById('side-menu');const overlay=document.getElementById('menu-overlay');if(!panel)return;const open=panel.classList.toggle('open');if(overlay)overlay.style.display=open?'block':'none';}
function toggleSection(id){const body=document.getElementById('body-'+id);const chev=document.getElementById('chevron-'+id);body.classList.toggle('open');chev.classList.toggle('open');}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function fmtTime(d){return d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});}
async function loadStatus(){try{const r=await fetch('/healthz');const d=await r.json();const det=d.details||{};const badges=document.getElementById('top-badges');badges.innerHTML='';['api','postgres','ollama'].forEach(k=>{const val=det[k]||'unknown';const ok=val==='ok';const b=document.createElement('span');b.className='badge '+(ok?'ok':'err');b.textContent=k+': '+val;badges.appendChild(b);});try{const tr=await fetch('/dashboard/agent_tasks');const td=await tr.json();const tks=td.tasks||[];const pend=tks.filter(t=>t.status==='pending_approval').length;const appr=tks.filter(t=>t.status==='approved').length;const qc=pend+appr;const qb=document.createElement('span');qb.className='badge '+(qc===0?'ok':'err');qb.style.borderColor=qc===0?'#3fb950':'#f0883e';qb.style.color=qc===0?'#3fb950':'#f0883e';qb.style.background=qc===0?'#1a2f1a':'#2f2a1a';qb.textContent='queue: '+qc;badges.appendChild(qb);}catch(e){}}catch(e){document.getElementById('top-badges').innerHTML='<span class="badge err">status error</span>';}}
async function loadRuns(){try{const r=await fetch('/dashboard/runs');const runs=await r.json();const el=document.getElementById('runs');if(!runs.length){el.innerHTML='<div style="color:#8b949e">No runs yet.</div>';return;}el.innerHTML=runs.map(run=>{const data=run.data||{};return'<div class="run-item"><div class="run-prompt">&rsaquo; '+esc(data.prompt||'(no prompt)')+'</div><div class="run-answer">'+esc(data.answer||'')+'</div><div class="run-meta">'+(run.created_at||'')+'</div></div>';}).join('');}catch(e){document.getElementById('runs').textContent='Error loading runs';}}
async function loadAgentTasks(){try{const r=await fetch("/dashboard/agent_tasks");const d=await r.json();const el=document.getElementById("agent-tasks");const tks=d.tasks||[];if(!tks.length){el.innerHTML='<div style="color:#8b949e">No tasks.</div>';return;}const grp={pa:[],ip:[],done:[],rej:[]};tks.forEach(t=>{const k=t.status||"";if(k==="pending_approval")grp.pa.push(t);else if(k==="approved"||k==="in_progress")grp.ip.push(t);else if(k==="completed")grp.done.push(t);else grp.rej.push(t);});let h="";function sec(ti,co,its,rn){if(!its.length)return;h+='<div style="margin-bottom:10px"><div style="color:'+co+';font-size:0.75rem;font-weight:bold;margin-bottom:4px">'+ti+' <span style="padding:1px 6px;border-radius:8px;font-size:0.68rem;margin-left:4px;background:'+co+'22;color:'+co+'">'+its.length+'</span></div><div>'+its.map(rn).join('')+'</div></div>';}sec("PENDING APPROVAL","#f0883e",grp.pa,t=>'<div style="background:#0d1117;border:1px solid #21262d;border-radius:5px;padding:6px 8px;margin-bottom:4px;font-size:0.78rem;display:flex;justify-content:space-between;align-items:center">'+esc(t.title)+'<span><button class="btn-approve" onclick="taskAction(&#39;'+t.id+'&#39;,&#39;approve&#39;)">&check;</button><button class="btn-reject" onclick="taskAction(&#39;'+t.id+'&#39;,&#39;reject&#39;)">&cross;</button></span></div>');sec("IN PROGRESS","#58a6ff",grp.ip,t=>'<div style="background:#0d1117;border:1px solid #21262d;border-radius:5px;padding:6px 8px;margin-bottom:4px;font-size:0.78rem">'+esc(t.title)+(t.assigned_to?'<span style="color:#8b949e;font-size:0.7rem;margin-top:2px"> ['+esc(t.assigned_to)+']</span>':'')+'</div>');sec("COMPLETED","#3fb950",grp.done,t=>'<div style="background:#0d1117;border:1px solid #21262d;border-radius:5px;padding:6px 8px;margin-bottom:4px;font-size:0.78rem">'+esc(t.title)+(t.result?'<div style="color:#8b949e;font-size:0.7rem;margin-top:2px">'+esc(t.result)+'</div>':'')+'</div>');sec("REJECTED","#f85149",grp.rej,t=>'<div style="background:#0d1117;border:1px solid #21262d;border-radius:5px;padding:6px 8px;margin-bottom:4px;font-size:0.78rem">'+esc(t.title)+(t.feedback?'<div style="color:#8b949e;font-size:0.7rem;margin-top:2px">'+esc(t.feedback)+'</div>':'')+'</div>');el.innerHTML=h;}catch(e){document.getElementById("agent-tasks").textContent="Error loading tasks";}}
async function taskAction(id,action){const label=action==='approve'?'Approve':'Reject';const reason=window.prompt(label+' reason (optional - press OK to skip):','');if(reason===null)return;try{const body=reason.trim()?JSON.stringify({feedback:reason.trim()}):'{}';await fetch('/tasks/'+id+'/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body});loadAgentTasks();}catch(e){alert('Error: '+e.message);}}
async function loadDailyBrief(){try{const r=await fetch('/dashboard/daily_brief');const d=await r.json();const el=document.getElementById('daily-brief');if(d.brief){el.innerHTML='<div class="brief-text">'+esc(d.brief)+'</div><div class="brief-meta">'+esc(d.date||'')+'</div>';}else{el.innerHTML='<div style="color:#8b949e;font-style:italic">No brief available yet.</div>';}}catch(e){document.getElementById('daily-brief').textContent='Error loading brief';}}
const SESSION_ID='dashboard_main';
async function loadChatHistory(){try{const today=new Date().toISOString().split('T')[0];const r=await fetch('/dashboard/chat_history_by_date?date='+today);const d=await r.json();(d.messages||[]).forEach(m=>appendMsg(m.role==='user'?'user':'alex',m.content));}catch(e){console.warn('chat history load error:',e);}}
async function loadChatArchive(){try{const r=await fetch('/dashboard/chat_archive');const d=await r.json();const container=document.getElementById('chat-archive-list');if(!container)return;container.innerHTML='';const today=new Date().toISOString().split('T')[0];(d.dates||[]).forEach(item=>{const label=item.date===today?'Today':item.date===new Date(Date.now()-86400000).toISOString().split('T')[0]?'Yesterday':item.date;const div=document.createElement('div');div.style.cssText='padding:8px 12px;cursor:pointer;border-bottom:1px solid #333;font-size:13px;';div.innerHTML='<span style=\"color:#ccc\">'+label+'</span> '+'<span style=\"color:#666;font-size:11px\">('+item.count+' msgs)</span>';div.onclick=()=>loadHistoryForDate(item.date,label);container.appendChild(div);});}catch(e){console.warn('archive load error:',e);}}
async function loadHistoryForDate(date,label){try{const r=await fetch('/dashboard/chat_history_by_date?date='+date);const d=await r.json();const chatBox=document.getElementById('main');if(!chatBox)return;chatBox.innerHTML='<div style=\"text-align:center;color:#666;padding:10px;font-size:12px;border-bottom:1px solid #333;margin-bottom:10px\">\u2014 '+label+' \u2014</div>';(d.messages||[]).forEach(m=>appendMsg(m.role==='user'?'user':'alex',m.content));}catch(e){console.warn('history load error:',e);}}
function appendMsg(role,text){const main=document.getElementById('main');const wrap=document.createElement('div');wrap.className='chat-msg '+(role==='user'?'user':'alex');const bubble=document.createElement('div');bubble.className='chat-bubble';bubble.textContent=text;const ts=document.createElement('div');ts.className='chat-ts';ts.textContent=fmtTime(new Date());wrap.appendChild(bubble);wrap.appendChild(ts);main.appendChild(wrap);main.scrollTop=main.scrollHeight;}
function setTyping(on){const main=document.getElementById('main');let el=document.getElementById('chat-typing');if(on){if(!el){el=document.createElement('div');el.id='chat-typing';el.className='chat-typing';el.textContent='Alexandra is thinking...';main.appendChild(el);main.scrollTop=main.scrollHeight;}}else{if(el)el.remove();}}
async function sendChat(){const input=document.getElementById('chat-input');const msg=input.value.trim();if(!msg)return;input.value='';document.getElementById('send-btn').disabled=true;appendMsg('user',msg);setTyping(true);try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg,session_id:SESSION_ID})});const d=await r.json();setTyping(false);const reply=d.response||JSON.stringify(d);appendMsg('alex',reply);setTimeout(loadRuns,1000);try{const sr=await fetch('/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:reply})});const ab=await sr.blob();const au=URL.createObjectURL(ab);const a=new Audio(au);a.onended=()=>{URL.revokeObjectURL(au);};a.play();}catch(ve){console.warn('voice speak error:',ve);}}catch(e){setTyping(false);appendMsg('alex','Error: '+e.message);}finally{document.getElementById('send-btn').disabled=false;}}
function setVoiceStatus(html){const el=document.getElementById('voice-status');if(!el)return;if(html){el.innerHTML=html;el.classList.add('visible');}else{el.innerHTML='';el.classList.remove('visible');}}
let mediaRecorder=null,audioChunks=[];
async function toggleRecording(){if(mediaRecorder&&mediaRecorder.state==='recording'){mediaRecorder.stop();return;}try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});mediaRecorder=new MediaRecorder(stream);audioChunks=[];mediaRecorder.ondataavailable=e=>{if(e.data.size>0)audioChunks.push(e.data);};mediaRecorder.onstop=async()=>{stream.getTracks().forEach(t=>t.stop());const btn=document.getElementById('mic-btn');btn.classList.remove('recording');btn.innerHTML='&#127908;';setVoiceStatus('Transcribing...');const blob=new Blob(audioChunks,{type:'audio/webm'});const fd=new FormData();fd.append('file',blob,'voice_input.webm');
try{const tr=await fetch('/voice/transcribe',{method:'POST',body:fd});const td=await tr.json();const text=(td.text||'').trim();if(!text){setVoiceStatus('');return;}setVoiceStatus('Sending to Alexandra...');appendMsg('user',text);setTyping(true);const cr=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,session_id:SESSION_ID})});const cd=await cr.json();setTyping(false);const reply=cd.response||JSON.stringify(cd);appendMsg('alex',reply);setVoiceStatus('Alexandra is speaking...');const sr=await fetch('/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:reply})});const audioBlob=await sr.blob();const audioUrl=URL.createObjectURL(audioBlob);const audio=new Audio(audioUrl);audio.onended=()=>{setVoiceStatus('');URL.revokeObjectURL(audioUrl);};audio.play();}catch(e){setTyping(false);setVoiceStatus('Error: '+e.message);}};mediaRecorder.start();const btn2=document.getElementById('mic-btn');btn2.classList.add('recording');btn2.innerHTML='&#9209;';setVoiceStatus('<span class="rec-dot"></span>Recording… click to stop');}catch(e){setVoiceStatus('Mic error: '+e.message);}}
async function captureWebcam(){const btn=document.getElementById('cam-btn');const vs=document.getElementById('voice-status');try{btn.disabled=true;btn.textContent='⏳';if(vs){vs.textContent='Alexandra is looking...';vs.classList.add('visible');}const stream=await navigator.mediaDevices.getUserMedia({video:true});const video=document.createElement('video');video.srcObject=stream;await video.play();const canvas=document.createElement('canvas');canvas.width=video.videoWidth||640;canvas.height=video.videoHeight||480;canvas.getContext('2d').drawImage(video,0,0);stream.getTracks().forEach(t=>t.stop());const blob=await new Promise(r=>canvas.toBlob(r,'image/jpeg',0.9));const fd=new FormData();fd.append('file',blob,'webcam.jpg');const r=await fetch('/vision/analyze',{method:'POST',body:fd});const d=await r.json();appendMsg('alex',d.description||'Could not analyze image');setVoiceStatus('');}catch(e){appendMsg('alex','Camera error: '+e.message);setVoiceStatus('');}finally{btn.disabled=false;btn.textContent='📷';}}
let _audioCtx=null;
function unlockAudio(){try{_audioCtx=new AudioContext();_audioCtx.resume();}catch(e){}}
let _greeted=false;
async function autoGreet(){
  if(_greeted)return;
  _greeted=true;
  const vs=document.getElementById('voice-status');
  try{
    const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480}}});
    if(vs){vs.textContent='Alexandra is looking...';vs.classList.add('visible');}
    const video=document.createElement('video');
    video.srcObject=stream;
    video.setAttribute('playsinline','true');
    await new Promise(r=>video.addEventListener('loadeddata',r,{once:true}));
    await video.play().catch(()=>{});
    await new Promise(r=>setTimeout(r,5000));
    const canvas=document.createElement('canvas');
    canvas.width=video.videoWidth||640;
    canvas.height=video.videoHeight||480;
    const ctx=canvas.getContext('2d');
    for(let att=0;att<5;att++){
      ctx.drawImage(video,0,0,canvas.width,canvas.height);
      const px=ctx.getImageData(0,0,canvas.width,1).data;
      let bright=0;for(let i=0;i<px.length;i+=4){if(px[i]+px[i+1]+px[i+2]>30)bright++;}
      if(bright>canvas.width*0.1)break;
      await new Promise(r=>setTimeout(r,2000));
    }
    stream.getTracks().forEach(t=>t.stop());
    // Check if frame is still too dark after all retries
    const finalPx=ctx.getImageData(0,0,canvas.width,1).data;
    let finalBright=0;for(let i=0;i<finalPx.length;i+=4){if(finalPx[i]+finalPx[i+1]+finalPx[i+2]>30)finalBright++;}
    if(finalBright<canvas.width*0.1){appendMsg('alex','Camera is still warming up - try clicking the camera button in a moment.');if(vs){vs.textContent='';vs.classList.remove('visible');}_greeted=false;return;}

    const blob=await new Promise(r=>canvas.toBlob(r,'image/jpeg',0.85));
    const fd=new FormData();
    fd.append('file',blob,'webcam.jpg');
    const vr=await fetch('/vision/analyze',{method:'POST',body:fd});
    const vd=await vr.json();
    const desc=vd.description||'';
    if(!desc){if(vs)vs.textContent='';return;}
    appendMsg('alex',desc);
    if(vs)vs.textContent='Alexandra is speaking...';
    const sr=await fetch('/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:desc})});
    const ab=await sr.blob();
    const au=URL.createObjectURL(ab);
    const a=new Audio(au);
    a.onended=()=>{if(vs){vs.textContent='';vs.classList.remove('visible');}URL.revokeObjectURL(au);};
    a.play();
  }catch(e){
    _greeted=false;
    if(vs){vs.textContent='';vs.classList.remove('visible');}
  }
}
loadStatus();loadRuns();loadAgentTasks();loadDailyBrief();loadChatHistory();loadChatArchive();setInterval(loadAgentTasks,20000);setInterval(loadStatus,30000);
const main=document.getElementById('main'); if(main) main.scrollTop=main.scrollHeight;
document.getElementById('chat-input').addEventListener('keydown',function(e){if(e.key==='Enter')sendChat();});
document.addEventListener('keydown',unlockAudio,{once:true});
function startSession(){
  const ov=document.getElementById('start-overlay');
  if(ov)ov.remove();
  setTimeout(autoGreet,300);
}

// Wake word - VAD + local Whisper
let wakeStream = null;
let wakeRunning = false;
let wakeAudioCtx = null;
let wakeAnalyser = null;
let wakeSilenceTimer = null;
let wakeChunks = [];
let wakeRecorder = null;
let wakeRecording = false;
let wakeSpeaking = false;
let speechStartTime = null;
const VAD_THRESHOLD = 0.12;
const VAD_SILENCE_MS = 600;
const VAD_MIN_SPEECH_MS = 500;
const VAD_MAX_RECORD_MS = 5000;

function rmsFromBuffer(buf) {
  let s = 0;
  for (let i = 0; i < buf.length; i++) s += buf[i] * buf[i];
  return Math.sqrt(s / buf.length);
}

async function startWakeWordWhisper() {
  if (wakeRunning) return;
  try {
    wakeStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 16000 }
    });
  } catch(e) { console.warn('Wake mic error:', e); return; }
  wakeAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const source = wakeAudioCtx.createMediaStreamSource(wakeStream);
  wakeAnalyser = wakeAudioCtx.createAnalyser();
  wakeAnalyser.fftSize = 512;
  source.connect(wakeAnalyser);
  wakeRunning = true;
  setVoiceStatus('Wake word armed');
  setTimeout(() => setVoiceStatus(''), 2000);
  console.log('PACO: VAD armed, threshold=' + VAD_THRESHOLD);
  vadLoop();
}

function vadLoop() {
  if (!wakeRunning) return;
  const buf = new Float32Array(wakeAnalyser.fftSize);
  wakeAnalyser.getFloatTimeDomainData(buf);
  const rms = rmsFromBuffer(buf);
  if (rms > VAD_THRESHOLD) {
    if (!wakeRecording) {
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        requestAnimationFrame(vadLoop); return;
      }
      if (wakeSpeaking) { requestAnimationFrame(vadLoop); return; }
      wakeChunks = [];
      speechStartTime = Date.now();
      try {
        wakeRecorder = new MediaRecorder(wakeStream, { mimeType: 'audio/webm;codecs=opus' });
      } catch(e) {
        wakeRecorder = new MediaRecorder(wakeStream);
      }
      wakeRecorder.ondataavailable = e => { if (e.data.size > 0) wakeChunks.push(e.data); };
      wakeRecorder.onstop = handleWakeChunk;
      wakeRecorder.start();
      wakeRecording = true;
      setTimeout(() => { if (wakeRecording) stopWakeRecording(); }, VAD_MAX_RECORD_MS);
    }
    clearTimeout(wakeSilenceTimer);
    wakeSilenceTimer = setTimeout(() => { if (wakeRecording) stopWakeRecording(); }, VAD_SILENCE_MS);
  }
  requestAnimationFrame(vadLoop);
}

function stopWakeRecording() {
  if (!wakeRecording) return;
  wakeRecording = false;
  clearTimeout(wakeSilenceTimer);
  if (wakeRecorder && wakeRecorder.state === 'recording') wakeRecorder.stop();
}

async function handleWakeChunk() {
  const duration = Date.now() - speechStartTime;
  if (duration < VAD_MIN_SPEECH_MS || wakeChunks.length === 0) return;
  const blob = new Blob(wakeChunks, { type: 'audio/webm' });
  const fd = new FormData();
  fd.append('file', blob, 'wake.webm');
  try {
    const r = await fetch('/voice/wake-detect', { method: 'POST', body: fd });
    const d = await r.json();
    console.log('PACO wake result:', JSON.stringify({triggered: d.triggered, transcript: d.transcript, query: d.query}));
    if (d.triggered && d.response) {
      appendMsg('user', d.query || '');
      appendMsg('alex', d.response);
      wakeSpeaking = true;
      setVoiceStatus('Alexandra is speaking...');
      try {
        const sr = await fetch('/voice/speak', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({text: d.response}) });
        const ab = await sr.blob();
        const au = URL.createObjectURL(ab);
        const a = new Audio(au);
        a.onended = () => { wakeSpeaking = false; setVoiceStatus(''); URL.revokeObjectURL(au); };
        a.play();
      } catch(e) { wakeSpeaking = false; setVoiceStatus(''); }
    }
  } catch(e) { console.warn('wake-detect error:', e); }
}

document.addEventListener('DOMContentLoaded', () => { const startOnce = () => { startWakeWordWhisper(); document.removeEventListener('click', startOnce); document.removeEventListener('keydown', startOnce); }; document.addEventListener('click', startOnce); document.addEventListener('keydown', startOnce); });

</script>
</body>
</html>
"""

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=HTML)

@router.get("/dashboard/runs")
async def dashboard_runs():
    import json as _json

    def _extract(val):
        if isinstance(val, dict):
            return val.get("data", val)
        if isinstance(val, str):
            try:
                obj = _json.loads(val)
                return obj.get("data", obj)
            except Exception:
                return {}
        return {}

    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, created_at, tool_result
                    FROM memory
                    WHERE tool = 'agent_answer'
                    AND created_at > NOW() - INTERVAL '24 hours'
                    ORDER BY created_at DESC
                    LIMIT 20
                """)
                rows = cur.fetchall()
                return [
                    {
                        "run_id": str(r[0]),
                        "created_at": r[1].isoformat() if r[1] else None,
                        "data": _extract(r[2])
                    }
                    for r in rows
                ]
    except Exception as e:
        return []

@router.get("/dashboard/agent_tasks")
async def dashboard_agent_tasks():
    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, status, title, assigned_to, result, feedback, created_at, updated_at
                    FROM agent_tasks ORDER BY created_at DESC LIMIT 20
                """)
                rows = cur.fetchall()
                import json as _j2
                def _res(v):
                    if v is None: return ''
                    if isinstance(v, dict): return str(v.get('output', v))[:120]
                    if isinstance(v, str):
                        try: return str(_j2.loads(v).get('output', v))[:120]
                        except: return v[:120]
                    return ''
                return {"tasks": [{"id": str(r[0]), "status": r[1], "title": r[2],
                    "assigned_to": r[3], "result": _res(r[4]), "feedback": r[5] or '',
                    "created_at": r[6].isoformat() if r[6] else None,
                    "updated_at": r[7].isoformat() if r[7] else None} for r in rows]}
    except Exception as e:
        return {"tasks": [], "error": str(e)}


@router.get("/dashboard/daily_brief")
async def dashboard_daily_brief():
    import json as _json
    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT title, result, created_at FROM agent_tasks
                    WHERE created_by='alexandra' AND assigned_to='sloan'
                    AND title LIKE 'Daily Brief%'
                    ORDER BY created_at DESC LIMIT 1
                """)
                row = cur.fetchone()
        if not row:
            return {"brief": None, "date": None}
        title, result, created_at = row
        brief_text = None
        if isinstance(result, dict):
            brief_text = result.get("brief")
        elif isinstance(result, str):
            try:
                obj = _json.loads(result)
                brief_text = obj.get("brief")
            except Exception:
                pass
        # unwrap nested agent JSON if brief_text is itself a serialised response
        if brief_text:
            try:
                inner = _json.loads(brief_text)
                if isinstance(inner, dict) and inner.get("answer"):
                    brief_text = inner["answer"]
            except Exception:
                pass
        date_str = created_at.strftime("%-d %B %Y") if created_at else None
        return {"brief": brief_text, "date": date_str, "title": title}
    except Exception as e:
        return {"brief": None, "date": None, "error": str(e)}


@router.get("/dashboard/chat_history")
async def dashboard_chat_history(session_id: str = 'default'):
    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT role, content, created_at FROM chat_history WHERE session_id=%s ORDER BY created_at ASC LIMIT 50',
                    (session_id,)
                )
                rows = cur.fetchall()
                return {'messages': [{'role': r[0], 'content': r[1], 'created_at': r[2].isoformat() if r[2] else None} for r in rows]}
    except Exception as e:
        return {'messages': [], 'error': str(e)}


@router.get('/dashboard/chat_archive')
async def dashboard_chat_archive():
    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DATE(created_at) as chat_date,
                           COUNT(*) as message_count
                    FROM chat_history
                    WHERE session_id = 'dashboard_main'
                    GROUP BY DATE(created_at)
                    ORDER BY chat_date DESC
                    LIMIT 60
                """)
                rows = cur.fetchall()
                return {'dates': [{'date': str(r[0]), 'count': r[1]} for r in rows]}
    except Exception as e:
        return {'dates': [], 'error': str(e)}

@router.get('/dashboard/chat_history_by_date')
async def dashboard_chat_history_by_date(date: str):
    try:
        with psycopg.connect(get_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT role, content, created_at
                    FROM chat_history
                    WHERE session_id = 'dashboard_main'
                    AND DATE(created_at) = %s
                    ORDER BY created_at ASC
                """, (date,))
                rows = cur.fetchall()
                return {'messages': [{'role': r[0], 'content': r[1], 'created_at': r[2].isoformat()} for r in rows]}
    except Exception as e:
        return {'messages': [], 'error': str(e)}
