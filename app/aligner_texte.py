import os
import re

def aligner_texte(fichier_entree):
    """Aligne le texte en mettant chaque verset numéroté sur une seule ligne"""
    
    try:
        with open(fichier_entree, 'r', encoding='utf-8') as f:
            contenu = f.read()
    except UnicodeDecodeError:
        with open(fichier_entree, 'r', encoding='latin-1') as f:
            contenu = f.read()
    except Exception as e:
        print(f"Erreur lors de la lecture de {fichier_entree}: {e}")
        return False
    
    # Remplacer tous les retours à la ligne par des espaces d'abord
    contenu = re.sub(r'\n+', ' ', contenu)
    
    # Supprimer les références entre parenthèses (Livre n:n-n)
    contenu = re.sub(r'\([A-Za-z]+\s+\d+:\d+(?:-\d+)?(?:;\s*[A-Za-z]+\s+\d+:\d+(?:-\d+)?)*\)', '', contenu)
    
    # Identifier et séparer les versets avec tous les patterns possibles
    # Pattern principal : TOUT nombre suivi de n'importe quel caractère non-numérique
    contenu = re.sub(r'(\d+)([^\d\s])', r'\n\1 \2', contenu)
    
    # Pattern pour nombres simples suivis d'espaces (mais pas dans les références)
    contenu = re.sub(r'(?<!\()(?<!\w)(\d+)\s+(?![:\d])(?![^\(]*\))', r'\n\1 ', contenu)
    
    # Nettoyer et finaliser
    lignes = contenu.split('\n')
    lignes_finales = []
    
    for ligne in lignes:
        ligne = ligne.strip()
        if ligne:
            # Remplacer les espaces multiples par un seul espace
            ligne = re.sub(r'\s+', ' ', ligne)
            lignes_finales.append(ligne)
    
    contenu_final = '\n'.join(lignes_finales)
    
    # Créer le fichier de sortie
    nom_base = os.path.splitext(os.path.basename(fichier_entree))[0]
    dossier = os.path.dirname(fichier_entree)
    fichier_sortie = os.path.join(dossier, f"{nom_base}_aligné.txt")
    
    try:
        with open(fichier_sortie, 'w', encoding='utf-8') as f:
            f.write(contenu_final)
        print(f"Fichier aligné créé: {fichier_sortie}")
        return True
    except Exception as e:
        print(f"Erreur lors de l'écriture de {fichier_sortie}: {e}")
        return False

def aligner_tous_fichiers(dossier):
    """Aligne tous les fichiers .txt d'un dossier"""
    
    try:
        if not os.path.exists(dossier):
            print(f"Erreur: Le dossier '{dossier}' n'existe pas")
            return
        
        fichiers_txt = [f for f in os.listdir(dossier) if f.endswith('.txt') and not f.endswith('_aligné.txt')]
        
        if not fichiers_txt:
            print(f"Aucun fichier .txt trouvé dans {dossier}")
            return
        
        print(f"Fichiers à traiter: {len(fichiers_txt)}")
        
        for fichier in sorted(fichiers_txt):
            chemin_complet = os.path.join(dossier, fichier)
            print(f"Traitement de: {fichier}")
            aligner_texte(chemin_complet)
        
        print("Traitement terminé!")
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    try:
        choix = input("1 - Aligner un seul fichier\n2 - Aligner tous les fichiers d'un dossier\nChoix (1 ou 2): ").strip()
        
        if choix == "1":
            fichier = input("Chemin du fichier .txt à aligner: ").strip()
            if fichier and os.path.exists(fichier):
                aligner_texte(fichier)
            else:
                print("Fichier non trouvé")
        
        elif choix == "2":
            dossier = input("Chemin du dossier contenant les fichiers .txt: ").strip()
            if not dossier:
                dossier = "."
            aligner_tous_fichiers(dossier)
        
        else:
            print("Choix invalide")
    
    except KeyboardInterrupt:
        print("\nOpération annulée par l'utilisateur")
    except Exception as e:
        print(f"Erreur: {e}")