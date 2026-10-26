"""Liste de contrôle de Nadia — à lancer sur chaque vidéo AVANT de l'envoyer à l'utilisateur.
Usage : python3 tools/verifier.py video.mp4      (sortie : OK, ou la liste des problèmes ; code 1 si problème)
Vérifie : format 1080x1920, durée 15-60 s, piste audio présente et pas muette, aucun silence de plus de 2,5 s
(sauf pendant un décompte où le tic-tac joue), volume correct, et extrait 6 images (verif_*.png) à REGARDER
pour contrôler à l'œil : pas d'écran « Sources », pas de badge IA, pas de « Voix de synthèse »,
pas de « n°X » en haut, fin sur la question pour commenter, texte lisible, aucune faute.
"""
import subprocess, sys, re, json
f = sys.argv[1]; pb = []
info = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",f]))
v = [s for s in info["streams"] if s["codec_type"]=="video"]; a = [s for s in info["streams"] if s["codec_type"]=="audio"]
d = float(info["format"]["duration"])
if not v or (v[0]["width"], v[0]["height"]) != (1080, 1920): pb.append("format différent de 1080x1920")
if not 15 <= d <= 60: pb.append(f"durée {d:.1f} s (attendu 15-60 s)")
if not a: pb.append("PAS DE PISTE AUDIO")
else:
    out = subprocess.run(["ffmpeg","-i",f,"-af","volumedetect,silencedetect=n=-40dB:d=2.5","-vn","-f","null","-"],capture_output=True,text=True).stderr
    m = re.search(r"mean_volume: (-?[\d.]+)", out)
    if m and float(m.group(1)) < -35: pb.append(f"son trop faible ({m.group(1)} dB)")
    for s in re.findall(r"silence_duration: ([\d.]+)", out): pb.append(f"silence de {float(s):.1f} s")
for k in range(6):
    t = d * (k + 0.5) / 6
    subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",f"{t:.2f}","-i",f,"-frames:v","1","-vf","scale=360:-1",f"verif_{k}.png"])
subprocess.run(["ffmpeg","-y","-loglevel","error","-sseof","-0.3","-i",f,"-frames:v","1","-vf","scale=360:-1","verif_fin.png"])
print("OK" if not pb else "PROBLÈMES :\n- " + "\n- ".join(pb))
print("Regarde maintenant verif_0..5.png et verif_fin.png (contrôle visuel obligatoire).")
sys.exit(1 if pb else 0)
