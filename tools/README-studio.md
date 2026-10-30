# Studio @reyzinhoia — comment fabriquer une vidéo

0. **Avant tout** : lire `tools/GUIDE-TIKTOK.md` (règles de croissance : accroche, fin, mot-clé, séries).
1. **Voix** (gratuit, GitHub Actions) : écrire `voix/jobs/<id-video>.json`
   `{"reference": "voix/hugo-ref.wav", "langue": "fr", "exaggeration": 0.75, "cfg": 0.4, "segments": ["texte écran 0", "texte écran 1", ...]}`
   puis commit + push. L'action « Voix Chatterbox » crée `voix/out/<id-video>/seg0.wav`, `seg1.wav`… (3 à 6 min), puis `git pull`.
2. **Écrans (décor attractif, OBLIGATOIRE depuis le 26 oct. 2026)** : fabriquer chaque écran avec `tools/decor.py` (style « Archive lumineuse », lire `tools/PHILOSOPHIE-DECOR.md`)
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

## Format « Le Prof Marius » (OBLIGATOIRE depuis le 30 oct. 2026, demande de l'utilisateur)
Vidéos qui APPRENNENT quelque chose, de façon interactive, expliquées par le Prof Marius (personnage dessiné
original du Studio : lunettes rondes, gilet vert, nœud papillon jaune). Thème : culture générale.
- Montage : `python3 tools/prof.py plan.json video.mp4` (voir l'en-tête du fichier). Remplace decor.py + assembler.py.
- Structure type (25 à 45 s) : 1) la question tout de suite (pose "question") ; 2) « À ton avis ? » avec 3 choix A/B/C
  et un décompte de 3 s ; 3) la réponse (même choix, "bonne": "B", pose "wow") ; 4) 2 à 3 scènes d'explication
  simples (poses "montre" / "explique", une icône, le mot-clé surligné) ; 5) un « et le plus fou… » ou un fait bonus ;
  6) fin : question pour commenter (type "fin").
- Interactif = on parle au spectateur (« tu », « à ton avis », « tu savais ? »), on le fait deviner AVANT d'expliquer.
- La voix (Hugo expressif) = le Prof Marius. Un segment de voix par scène.
- Nadia vérifie aussi : le prof est entier et visible, rien ne chevauche le texte du tableau.
