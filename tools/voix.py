import json, glob, os, time
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
jobs = [j for j in sorted(glob.glob("voix/jobs/*.json")) if not os.path.exists("voix/out/" + os.path.basename(j)[:-5] + "/fini.txt")]
print("jobs:", jobs)
if not jobs: raise SystemExit
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
for j in jobs:
    cfg = json.load(open(j)); name = os.path.basename(j)[:-5]
    out = f"voix/out/{name}"; os.makedirs(out, exist_ok=True)
    for i, txt in enumerate(cfg["segments"]):
        t = time.time()
        wav = model.generate(txt, language_id=cfg.get("langue", "fr"), audio_prompt_path=cfg.get("reference"),
                             exaggeration=cfg.get("exaggeration", 0.5), cfg_weight=cfg.get("cfg", 0.5))
        ta.save(f"{out}/seg{i}.wav", wav, model.sr)
        print(name, i, round(time.time() - t, 1), "s", flush=True)
    open(f"{out}/fini.txt", "w").write("ok")
