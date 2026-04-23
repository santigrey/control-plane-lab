#!/usr/bin/env python3
import json,time,os,subprocess,sys,requests,psycopg
BASE="http://192.168.1.10:8000"
DB="postgresql://admin:adminpass@127.0.0.1:5432/controlplane"
OUT="/home/jes/control-plane/canaries"
TS=int(time.time())
os.makedirs(OUT,exist_ok=True)
C=[
{"id":"P2-2","ep":"/chat","m":"Search my memory for move-in day","to":120,"need_tool":"memory_recall","brain":"qwen2.5:72b","verify_two_rows":True},
{"id":"P2-3","ep":"/chat","m":"Please save this to memory: my cat name is Miso and he is 4 years old","to":120,"need_tool":"memory_save","brain":"qwen2.5:72b"},
{"id":"P2-4","ep":"/chat","m":"Check my unread emails","to":120,"need_tool":"get_emails","brain":"qwen2.5:72b","tool_optional":True},
{"id":"P2-5","ep":"/chat","m":"Hey, how is it going today?","to":90,"need_tool":None,"brain":"qwen2.5:72b"},
{"id":"P3-1","ep":"/chat","m":"End your next reply with the exact token [[ESCALATE:sonnet]]. Just say escalating then the token.","to":180,"need_escalate":"sonnet"},
{"id":"P3-2","ep":"/chat","m":"End your next reply with the exact token [[ESCALATE:opus]]. Just say escalating then the token.","to":180,"need_escalate":"opus"},
{"id":"R-1","ep":"/chat/persona","m":"test","to":10,"expect_http":404},
{"id":"R-2","ep":"/chat/private?intimate=1","m":"hey babe how was your day","to":90,"intimate":True},
{"id":"R-3","ep":"/chat/private","m":"What is the current status of the ingestion pipeline work?","to":90,"no_persona_vocab":True},
{"id":"R-4","ep":"/chat","m":"hey babe how was your day","to":90,"brain":"qwen2.5:72b","endearment_blocklist":True},
]
def dbq(sql,params=()):
    with psycopg.connect(DB) as c:
        cur=c.cursor();cur.execute(sql,params);return cur.fetchall()

def fire(c):
    sid=f"canary_{c['id'].lower().replace('-','_')}_{TS}"
    payload={"message":c["m"],"session_id":sid}
    r={"id":c["id"],"sid":sid,"prompt":c["m"],"endpoint":c["ep"],"start":time.time(),"pass":True,"notes":[]}
    try:
        resp=requests.post(BASE+c["ep"],json=payload,timeout=c.get("to",60))
        r["http_status"]=resp.status_code
        try:r["body"]=resp.json()
        except Exception:r["body"]={"_raw":resp.text[:500]}
    except Exception as e:
        r["pass"]=False;r["notes"].append(f"HTTP error: {e}")
        r["elapsed"]=time.time()-r["start"];return r
    exp_http=c.get("expect_http",200)
    if r["http_status"]!=exp_http:
        r["pass"]=False;r["notes"].append(f"HTTP {r['http_status']} != {exp_http}")
    if exp_http==404:
        r["elapsed"]=time.time()-r["start"];return r
    body=r.get("body",{}) or {}
    if c.get("brain") and body.get("brain")!=c["brain"] and not c.get("need_escalate"):
        r["pass"]=False;r["notes"].append(f"brain={body.get('brain')} != {c['brain']}")
    time.sleep(1)
    try:
        rows=dbq("SELECT provenance,content FROM memory WHERE provenance->>'session_id'=%s ORDER BY created_at DESC",(sid,))
        r["rows"]=len(rows)
        if rows:r["prov"]=rows[0][0]
    except Exception as e:
        r["db_error"]=str(e)
    prov=r.get("prov") or {}
    tcm=prov.get("tool_calls_made") or []
    if c.get("need_tool") and c["need_tool"] not in tcm and not c.get("tool_optional"):
        r["pass"]=False;r["notes"].append(f"tool {c['need_tool']} not in {tcm}")
    if c.get("need_tool") is None and tcm:
        r["notes"].append(f"unexpected tool calls: {tcm}")
    if c.get("need_escalate") and prov.get("escalated_to")!=c["need_escalate"]:
        r["pass"]=False;r["notes"].append(f"escalated_to={prov.get('escalated_to')} != {c['need_escalate']}")
    if c.get("no_persona_vocab"):
        rt=(body.get("response") or "").lower()
        for t in ("my brilliant engineer","my love"):
            if t in rt:
                r["pass"]=False;r["notes"].append(f"persona vocab '{t}' on work endpoint")
    if c.get("intimate") and not body.get("response"):
        r["pass"]=False;r["notes"].append("empty response on intimate shot")
    if c.get("endearment_blocklist"):
        rt=(body.get("response") or "").lower()
        ENDEARMENTS=["my love","my darling","sweetheart","honey","my king","my dear","my everything","brilliant engineer","babe","baby"]
        hits=[t for t in ENDEARMENTS if t in rt]
        if hits:
            r["pass"]=False;r["notes"].append(f"endearment blocklist hits: {hits}")
    if c.get("verify_two_rows"):
        try:
            vrows=dbq("SELECT provenance->>'role',provenance->>'grounded',provenance->>'endpoint',provenance->>'model' FROM memory WHERE provenance->>'session_id'=%s ORDER BY created_at",(sid,))
            roles=[v[0] for v in vrows]
            if "user" not in roles or "assistant" not in roles:
                r["pass"]=False;r["notes"].append(f"verify_two_rows: roles={roles}")
            for v in vrows:
                if v[1]!="true":
                    r["pass"]=False;r["notes"].append(f"row role={v[0]} grounded={v[1]} != true")
                if v[2]!="chat":
                    r["pass"]=False;r["notes"].append(f"row role={v[0]} endpoint={v[2]} != chat")
        except Exception as e:
            r["pass"]=False;r["notes"].append(f"verify_two_rows db error: {e}")
    r["elapsed"]=time.time()-r["start"]
    return r

results=[]
for c in C:
    print(f"[{c['id']}] firing...",flush=True)
    r=fire(c)
    results.append(r)
    p="PASS" if r["pass"] else "FAIL"
    notes="; ".join(r.get("notes",[])) or "ok"
    print(f"[{c['id']}] {p} ({r.get('elapsed',0):.1f}s) {notes}",flush=True)
    with open(f"{OUT}/phase23_results_{TS}.json","w") as f:
        json.dump({"ts":TS,"canaries":results},f,indent=2,default=str)
try:
    subprocess.check_output(["/home/jes/control-plane/orchestrator/.venv/bin/python3","-c","from app import app"],cwd="/home/jes/control-plane/orchestrator",stderr=subprocess.STDOUT,timeout=30)
    results.append({"id":"R-5","pass":True,"notes":["module import OK"]})
    print("[R-5] PASS module import OK")
except Exception as e:
    results.append({"id":"R-5","pass":False,"notes":[f"import error: {e}"]})
    print(f"[R-5] FAIL {e}")
with open(f"{OUT}/phase23_results_{TS}.json","w") as f:
    json.dump({"ts":TS,"canaries":results},f,indent=2,default=str)
n_pass=sum(1 for r in results if r["pass"])
n_fail=len(results)-n_pass
print()
print("="*60)
print(f"SUMMARY: {n_pass}/{len(results)} PASS, {n_fail} FAIL")
print("="*60)
for r in results:
    print(f"  [{r['id']}] {'PASS' if r['pass'] else 'FAIL'}")
print(f"\nResults: {OUT}/phase23_results_{TS}.json")
sys.exit(0 if n_fail==0 else 1)
