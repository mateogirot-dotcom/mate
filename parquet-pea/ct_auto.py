"""Fait tourner les agents COURT TERME sur GitHub, sans IA (argent fictif, aucun ordre réel, pas un conseil).
Lit data/cours_live.json et data/agents_ct.json, lance seance_ct.py, et réécrit data/agents_ct.json.
Une tâche Claude recopie ce fichier dans la ville une fois par soir."""
import json, os, subprocess, sys, tempfile
D = os.path.dirname(os.path.abspath(__file__)); data = os.path.join(D, "data")
A = json.load(open(os.path.join(data, "agents_ct.json")))
out = tempfile.mkdtemp()
r = subprocess.run([sys.executable, os.path.join(D, "seance_ct.py"), os.path.join(data, "cours_live.json"), os.path.join(data, "agents_ct.json"), out])
if r.returncode: sys.exit(r.returncode)
new = []
for a in A:
    f = os.path.join(out, a["_id"] + ".json")
    new.append(json.load(open(f)) if os.path.exists(f) else a)
json.dump(new, open(os.path.join(data, "agents_ct.json"), "w"), ensure_ascii=False)
if os.path.exists(os.path.join(out, "resume_ct.txt")): print(open(os.path.join(out, "resume_ct.txt")).read())
