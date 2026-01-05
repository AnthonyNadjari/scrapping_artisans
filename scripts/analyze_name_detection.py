"""
Script pour analyser la détection de prénoms dans la base de données
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from whatsapp_database.queries import get_artisans
from whatsapp.name_detector import detect_prenom, load_prenoms

def main():
    print("Analyse de la detection de prenoms dans la base de donnees\n")
    print("=" * 70)
    
    # Charger tous les artisans
    artisans = get_artisans(limit=None)
    print(f"\nTotal artisans dans la base: {len(artisans)}")
    
    # Analyser la détection
    prenoms_detectes = {}
    sans_prenom = []
    noms_analyse = []
    
    for artisan in artisans:
        nom = artisan.get('nom_entreprise', '')
        if not nom:
            continue
        
        prenom = detect_prenom(nom)
        if prenom:
            prenoms_detectes[prenom] = prenoms_detectes.get(prenom, 0) + 1
        else:
            sans_prenom.append((nom, artisan.get('id')))
            # Analyser les tokens pour voir ce qui pourrait être un prénom
            tokens = nom.split()
            noms_analyse.append((nom, tokens))
    
    # Statistiques
    total_avec_prenom = sum(prenoms_detectes.values())
    total_sans_prenom = len(sans_prenom)
    taux_detection = (total_avec_prenom / len(artisans) * 100) if artisans else 0
    
    print(f"\n[OK] Artisans avec prenom detecte: {total_avec_prenom} ({taux_detection:.1f}%)")
    print(f"[KO] Artisans sans prenom detecte: {total_sans_prenom} ({100 - taux_detection:.1f}%)")
    
    # Top 10 prénoms détectés
    print(f"\nTop 10 prenoms detectes:")
    for prenom, count in sorted(prenoms_detectes.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {prenom:15} : {count:3} fois")
    
    # Analyser les noms sans prénom détecté
    print(f"\nAnalyse des noms sans prenom detecte (echantillon de 100):")
    print("=" * 70)
    
    prenoms_set = load_prenoms()
    
    # Chercher des patterns dans les noms non détectés
    tokens_potentiels = {}
    for nom, tokens in noms_analyse[:200]:
        for token in tokens:
            token_clean = token.lower().strip('.,;:!?()[]{}')
            if len(token_clean) >= 3 and token_clean not in ['sarl', 'eurl', 'sas', 'sa', 'sci', 'snc', 
                                                              'entreprise', 'entreprises', 'societe', 'societe',
                                                              'plomberie', 'plombier', 'electricite', 'electricite',
                                                              'chauffage', 'artisan', 'artisans', 'le', 'la', 'les',
                                                              'du', 'de', 'des', 'et']:
                if token_clean not in tokens_potentiels:
                    tokens_potentiels[token_clean] = []
                tokens_potentiels[token_clean].append(nom[:50])
    
    # Vérifier si certains tokens pourraient être des prénoms manquants
    print("\nTokens potentiellement manquants dans la liste de prenoms:")
    tokens_manquants = []
    for token, exemples in sorted(tokens_potentiels.items(), key=lambda x: len(x[1]), reverse=True)[:50]:
        if token not in prenoms_set and len(token) >= 3:
            tokens_manquants.append((token, len(exemples)))
            if len(tokens_manquants) <= 20:
                print(f"   {token:20} : {len(exemples):3} occurrences")
                if exemples:
                    print(f"      Exemples: {', '.join(exemples[:2])}")
    
    # Afficher quelques exemples de noms sans prénom
    print(f"\nExemples de noms sans prenom detecte (30 premiers):")
    for nom, _id in sans_prenom[:30]:
        print(f"   {nom}")
    
    # Suggestions d'amélioration
    print(f"\nSuggestions:")
    if tokens_manquants:
        print(f"   - {len(tokens_manquants)} tokens frequents pourraient etre ajoutes a la liste de prenoms")
        top_5 = [t[0] for t in tokens_manquants[:5]]
        print(f"   - Top 5 a considerer: {', '.join(top_5)}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

