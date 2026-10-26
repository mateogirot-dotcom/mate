import json
R = json.load(open("parquet-pea/resultats.json"))["inconnue_2016_2026"]
def res(prefix): return next(v for k, v in R.items() if k.startswith(prefix))
J = [
 ("hector-le-paresseux","Hector le Paresseux","paresseux","Le Paresseux",True,
  {"role":"Témoin","trait":"Ne bouge jamais","quote":"Pourquoi se fatiguer ?","aime":"La sieste","deteste":"Les décisions","tic":"Bâille pendant les séances"},
  {"skin":0xe0ac7e,"hair":["messy",0x7a4a2a],"top":0x8c9bb8,"bottom":0x3a4258,"h":1.0,"w":1.12,"face":["dot","smile","calm"],"extras":["stripes"]},"calm"),
 ("prudence-la-prudente","Prudence la Prudente","prudent","Le Prudent",True,
  {"role":"Témoin","trait":"Garde 40 % de côté","quote":"On ne sait jamais.","aime":"Les matelas de sécurité","deteste":"Les montagnes russes","tic":"Recompte sa tirelire"},
  {"skin":0xf3c9a6,"hair":["bun",0xbfc4cc],"top":0x5fb36a,"bottom":0x26304a,"h":0.95,"w":0.95,"face":["dot","smile","calm"],"extras":["rectglasses","scarf"]},"nod"),
 ("toinette-la-tortue","Toinette la Tortue","tortue","La Tortue",False,
  {"role":"Trader","trait":"Répartit et garde","quote":"Lentement mais sûrement.","aime":"Le long terme","deteste":"S'agiter","tic":"Arrose sa plante avant chaque séance"},
  {"skin":0xb27349,"hair":["curly",0x14100e],"top":0x2f9e5b,"bottom":0x3a4258,"h":0.95,"w":1.05,"face":["happy","smile","calm"],"extras":["book"]},"calm"),
 ("berenice-la-boussole","Bérénice la Boussole","boussole","La Boussole",False,
  {"role":"Trader","trait":"Suit la tendance","quote":"Je suis le vent.","aime":"Les courbes qui montent","deteste":"Aller à contre-courant","tic":"Vérifie sa boussole"},
  {"skin":0xf1c7a1,"hair":["pony",0xa0462a],"hat":"cap","top":0x3b6fd8,"bottom":0x26304a,"h":1.0,"w":0.95,"face":["big","smile","up"],"extras":["watch"]},"look"),
 ("fanny-la-fusee","Fanny la Fusée","fusee","La Fusée",False,
  {"role":"Trader","trait":"Suit l'élan","quote":"Ce qui monte peut encore monter !","aime":"La vitesse","deteste":"Attendre","tic":"Tape du pied en attendant"},
  {"skin":0x8d5a3b,"hair":["spiky",0xe85d3f],"top":0xe85d3f,"bottom":0x26304a,"h":0.97,"w":0.95,"face":["happy","grin","up"],"extras":["headphones"]},"bounce"),
 ("charles-le-chineur","Charles le Chineur","chineur","Le Chineur",False,
  {"role":"Trader","trait":"Achète les baisses","quote":"Une chute, c'est des soldes.","aime":"Les bonnes affaires","deteste":"Acheter au plus haut","tic":"Dessine des flèches partout"},
  {"skin":0xd99a6c,"hair":["side",0x2a1d18],"hat":"fedora","top":0xb5603a,"bottom":0x4a4f63,"h":1.05,"w":1.05,"face":["dot","smirk","raised"],"extras":["magnifier","mustache"]},"look"),
 ("valentine-la-vigilante","Valentine la Vigilante","vigilante","La Vigilante",False,
  {"role":"Trader","trait":"Se protège après une chute","quote":"Au premier signal, je me mets à l'abri.","aime":"Les filets de sécurité","deteste":"Les pertes qui s'accumulent","tic":"Relit ses règles tous les matins"},
  {"skin":0xc68b5e,"hair":["bob",0x2a1d18],"top":0xb07ce8,"bottom":0x26304a,"h":1.0,"w":0.92,"face":["dot","flat","sharp"],"extras":["jacket","clipboard"]},"headshake"),
 ("elio-l-equilibriste","Elio l'Équilibriste","equilibriste","L'Équilibriste",False,
  {"role":"Trader","trait":"Équilibre les risques","quote":"Un pied sur chaque fil.","aime":"La stabilité","deteste":"Tout miser sur un seul fonds","tic":"Fait tenir un crayon en équilibre"},
  {"skin":0xf0c09a,"hair":["short",0x3b2a20],"top":0xf2b544,"bottom":0x3a4258,"h":1.02,"w":1.0,"face":["dot","smile","calm"],"extras":["pencil","overalls"]},"sway"),
]
METHODE = ["Argent fictif : 10 000 € au départ le 26 oct. 2026. Aucun ordre réel n'est jamais passé. Ce n'est pas un conseil d'investissement.",
 "Règles du PEA : seulement des fonds « éligibles PEA » (ici S&P 500, Nasdaq-100, Europe, France, pays émergents), pas d'obligations ni d'or.",
 "Les fonds PEA sont simulés par les indices qu'ils copient, convertis en euros (prix des fonds SPY, QQQ, VGK, EWQ, EEM divisés par l'EUR/USD).",
 "Chaque prix est vérifié avec 2 sources ; sinon le fonds est mis de côté pour la séance.",
 "Une séance par semaine (le lundi soir). Frais fictifs : 0,1 % par achat ou vente.",
 "Règle de Gaspard : jamais plus de 50 % sur un seul fonds (sauf le témoin Hector, qui copie l'investisseur le plus simple).",
 "Fiscalité d'un vrai PEA de plus de 5 ans : pas d'impôt sur les gains, mais 18,6 % de prélèvements sociaux (2026)."]
docs = []
for _id, agent, code, prefix, temoin, perso, look, anim in J:
    r = res(prefix)
    docs.append({"_id": _id, "agent": agent, "statut": "actif", "direct": True, "ligue": "pea", "devise": "€", "temoin": temoin,
      "plafond": not (code == "paresseux"), "style_code": code, "style": ("Témoin. " if temoin else "") + perso["trait"] + ".",
      "depart": 10000, "cash": 10000, "valeur": 10000, "pic": 10000, "mdd": 0, "positions": [], "historique": [], "courbe": [{"date": "2026-10-26", "valeur": 10000}],
      "periode": "en direct depuis le 26 oct. 2026", "depuis": "26 oct. 2026", "maj": "2026-10-26", "moment": "ouverture",
      "entrainement": {"periode": "test honnête 2016-2026, sur des années jamais vues", "multiplie": round(r["final"]/10000, 3), "rendement": r["par_an_pct"]/100, "chute": -r["pire_chute_pct"]/100},
      "regles": [], "methode": METHODE, "perso": perso, "look": look, "anim": anim, "notes": []})
json.dump(docs, open("parquet-pea/portefeuilles_init.json", "w"), ensure_ascii=False, indent=1)
print(len(docs), [d["entrainement"] for d in docs][:2])
