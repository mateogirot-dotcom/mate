# Studio @reyzinhoia — comment fabriquer une vidéo

1. **Voix** (gratuit, GitHub Actions) : écrire `voix/jobs/<id-video>.json`
   `{"reference": "voix/hugo-ref.wav", "langue": "fr", "exaggeration": 0.75, "cfg": 0.4, "segments": ["texte écran 0", "texte écran 1", ...]}`
   puis commit + push. L'action « Voix Chatterbox » crée `voix/out/<id-video>/seg0.wav`, `seg1.wav`… (3 à 6 min), puis `git pull`.
2. **Écrans** : un PNG 1080x1920 par écran (Pillow), texte gros et lisible, fond coloré, une idée par écran.
   Pour un « Vrai ou faux » : écran question, puis 3 images de décompte (3, 2, 1), puis la réponse.
   INTERDIT à l'écran : écran « Sources », badge « Contenu généré par IA », « Voix de synthèse », « n°X » en haut.
   Dernier écran : la question pour faire commenter (« Ta réponse en commentaire ! »).
3. **Montage** : `python3 tools/assembler.py plan.json video.mp4` (voir l'en-tête du fichier pour plan.json).
   Son de décompte : `sons/son-A-horloge-carillon.wav` (choisi par l'utilisateur).
4. **Contrôle de Nadia** : `python3 tools/verifier.py video.mp4` doit dire OK, puis REGARDER les images verif_*.png.
   Si un problème : corriger et refaire. Jamais de vidéo envoyée sans ce contrôle.
