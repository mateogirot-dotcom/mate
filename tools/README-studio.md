# Studio @reyzinhoia — comment fabriquer une vidéo

0. **Avant tout** : lire `tools/GUIDE-TIKTOK.md` (règles de croissance : accroche, fin, mot-clé, séries).
1. **Voix** (gratuit, GitHub Actions) : écrire `voix/jobs/<id-video>.json`
   `{"reference": "voix/hugo-ref.wav", "langue": "fr", "exaggeration": 0.75, "cfg": 0.4, "segments": ["texte écran 0", "texte écran 1", ...]}`
   puis commit + push. L'action « Voix Chatterbox » crée `voix/out/<id-video>/seg0.wav`, `seg1.wav`… (3 à 6 min), puis `git pull`.
2. **Écrans (décor attractif, OBLIGATOIRE depuis le 26 oct. 2026)** : fabriquer chaque écran avec `tools/decor.py`
   (`from decor import ecran` après `sys.path.insert(0, "tools")`) : dégradé coloré, bulles lumineuses, carte blanche, gros titres.
   Types : "question" (avec une icône), "decompte" ("3","2","1"), "vrai" / "faux", "explication", "chiffre" ("GROS CHIFFRE|phrase"), "fin".
   Mettre le MOT-CLÉ entre {accolades} pour le surligner en jaune. Icônes : piece, carte, cheque, billet, cerveau, os, globe, horloge, ampoule, livre.
   Ne pas dessiner ses propres écrans plats. Pour un « 5 vrai ou faux » : compteur="1/5" … "5/5".
   Pour un « Vrai ou faux » : écran question, puis 3 images de décompte (3, 2, 1), puis la réponse.
   INTERDIT à l'écran : écran « Sources », badge « Contenu généré par IA », « Voix de synthèse », « n°X » en haut.
   Dernier écran : la question pour faire commenter (« Ta réponse en commentaire ! »).
3. **Montage** : `python3 tools/assembler.py plan.json video.mp4` (ajoute un léger zoom lent sur chaque écran) (voir l'en-tête du fichier pour plan.json).
   Son de décompte : `sons/son-A-horloge-carillon.wav` (choisi par l'utilisateur).
4. **Contrôle de Nadia** : `python3 tools/verifier.py video.mp4` doit dire OK, puis REGARDER les images verif_*.png.
   Si un problème : corriger et refaire. Jamais de vidéo envoyée sans ce contrôle.
