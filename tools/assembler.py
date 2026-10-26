"""Modèle de vidéo du Studio (@reyzinhoia) — assemble une vidéo à partir des écrans et des voix.

Usage : python3 tools/assembler.py plan.json sortie.mp4

plan.json :
{
  "son_decompte": "sons/son-A-horloge-carillon.wav",
  "ecrans": [
    {"image": "ecran0.png", "voix": "voix/out/<id>/seg0.wav"},
    {"image": "question.png", "voix": "voix/out/<id>/seg1.wav",
     "decompte": ["d3.png", "d2.png", "d1.png"]},          # écran suivi du décompte (1 s par image)
    {"image": "reponse.png", "voix": "voix/out/<id>/seg2.wav"},   # après un décompte : carillon + voix 0,25 s après
    ...
    {"image": "fin.png", "voix": "voix/out/<id>/segN.wav"}         # dernier écran : « Ta réponse en commentaire ! »
  ]
}
Chaque "image" est un PNG 1080x1920 (ou "video": un petit .mp4 animé à la place).
Règles : chaque écran dure le temps de sa voix + 0,4 s ; silences coupés (-45 dB) ; le décompte dure
1 s par image, avec les 2 dernières secondes de tic-tac ; le carillon tombe sur l'écran de réponse ;
volume final loudnorm I=-15. AUCUN écran Sources, AUCUN badge, AUCUNE mention de voix (règles de l'utilisateur).
"""
import json, subprocess, sys, os, tempfile

def run(*a): subprocess.run(list(a), check=True, capture_output=True)
def dur(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]).decode())
ENC = ["-r","30","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p"]

def clip(src, d, out):
    if src.endswith(".png") or src.endswith(".jpg"):
        run("ffmpeg","-y","-loglevel","error","-loop","1","-t",f"{d:.3f}","-i",src,"-vf","scale=1080:1920,format=yuv420p",*ENC,out)
    else:
        run("ffmpeg","-y","-loglevel","error","-i",src,"-vf",f"scale=1080:1920,tpad=stop_mode=clone:stop_duration=60,trim=0:{d:.3f},setpts=PTS-STARTPTS",*ENC,out)

def main(plan_path, out):
    plan = json.load(open(plan_path)); son = plan.get("son_decompte")
    t = tempfile.mkdtemp(); parts = []; carillon_next = False
    for i, e in enumerate(plan["ecrans"]):
        v = f"{t}/v{i}.wav"
        run("ffmpeg","-y","-loglevel","error","-i",e["voix"],"-af",
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,aresample=44100","-ac","1",v)
        vd = dur(v); delay = 0.25 if carillon_next else 0.0
        d = vd + delay + 0.4
        clip(e.get("image") or e["video"], d, f"{t}/c{i}.mp4")
        a = f"{t}/a{i}.wav"
        if carillon_next and son:
            run("ffmpeg","-y","-loglevel","error","-i",v,"-i",son,"-filter_complex",
                f"[1:a]atrim=start=2.0,asetpts=PTS-STARTPTS,volume=0.8[c];[0:a]adelay=250|250[vv];[vv][c]amix=inputs=2:normalize=0,apad,atrim=0:{d:.3f}[a]",
                "-map","[a]","-ar","44100","-ac","1",a)
        else:
            run("ffmpeg","-y","-loglevel","error","-i",v,"-af",f"apad,atrim=0:{d:.3f}","-ar","44100","-ac","1",a)
        run("ffmpeg","-y","-loglevel","error","-i",f"{t}/c{i}.mp4","-i",a,"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","160k","-shortest",f"{t}/p{i}.mp4")
        parts.append(f"{t}/p{i}.mp4"); carillon_next = False
        if e.get("decompte"):
            imgs = e["decompte"]; n = len(imgs)
            for k, im in enumerate(imgs): clip(im, 1.0, f"{t}/d{i}_{k}.mp4")
            open(f"{t}/dl{i}.txt","w").write("".join(f"file '{t}/d{i}_{k}.mp4'\n" for k in range(n)))
            run("ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{t}/dl{i}.txt","-c","copy",f"{t}/dv{i}.mp4")
            st = max(0, n - 2.0); da = f"{t}/da{i}.wav"
            if son:
                run("ffmpeg","-y","-loglevel","error","-i",son,"-af",f"atrim=0:2.0,adelay={int(st*1000)}|{int(st*1000)},apad,atrim=0:{n}","-ar","44100","-ac","1",da)
            else:
                run("ffmpeg","-y","-loglevel","error","-f","lavfi","-i",f"anullsrc=r=44100:cl=mono","-t",str(n),da)
            run("ffmpeg","-y","-loglevel","error","-i",f"{t}/dv{i}.mp4","-i",da,"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","160k","-shortest",f"{t}/dp{i}.mp4")
            parts.append(f"{t}/dp{i}.mp4"); carillon_next = True
    open(f"{t}/list.txt","w").write("".join(f"file '{p}'\n" for p in parts))
    run("ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{t}/list.txt","-c:v","copy","-af","loudnorm=I=-15:TP=-1.5","-c:a","aac","-b:a","160k","-movflags","+faststart",out)
    print("ok", out, round(dur(out), 2))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
