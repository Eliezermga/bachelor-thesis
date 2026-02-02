import os
import glob

def combiner_fichiers_txt(dossier_source, fichier_sortie):
    """Combine tous les fichiers .txt d'un dossier en un seul fichier"""
    
    try:
        # Vérifier si le dossier existe
        if not os.path.exists(dossier_source):
            print(f"Erreur: Le dossier '{dossier_source}' n'existe pas")
            return False
        
        # Obtenir tous les fichiers .txt du dossier et les trier par nom
        fichiers_txt = sorted(glob.glob(os.path.join(dossier_source, "*.txt")))
        
        if not fichiers_txt:
            print(f"Aucun fichier .txt trouvé dans {dossier_source}")
            return False
        
        print(f"Fichiers trouvés (dans l'ordre):")
        for fichier in fichiers_txt:
            print(f"  - {os.path.basename(fichier)}")
        
        with open(fichier_sortie, 'w', encoding='utf-8') as sortie:
            for fichier in fichiers_txt:
                print(f"Traitement de: {os.path.basename(fichier)}")
                
                try:
                    with open(fichier, 'r', encoding='utf-8') as f:
                        sortie.write(f.read())
                        sortie.write('\n')  # Ajouter un saut de ligne après chaque fichier
                except UnicodeDecodeError:
                    try:
                        with open(fichier, 'r', encoding='latin-1') as f:
                            sortie.write(f.read())
                            sortie.write('\n')  # Ajouter un saut de ligne après chaque fichier
                    except Exception as e:
                        print(f"Erreur lors de la lecture de {fichier}: {e}")
                        continue
                except Exception as e:
                    print(f"Erreur lors de la lecture de {fichier}: {e}")
                    continue
        
        print(f"Fichiers combinés dans: {fichier_sortie}")
        return True
        
    except Exception as e:
        print(f"Erreur générale: {e}")
        return False

if __name__ == "__main__":
    try:
        # Configuration
        dossier = input("Chemin du dossier contenant les fichiers .txt: ").strip()
        if not dossier:
            dossier = "."  # Dossier courant par défaut
        
        fichier_combine = input("Nom du fichier de sortie: ").strip()
        if not fichier_combine:
            fichier_combine = "fichiers_combines"
        
        # Ajouter automatiquement l'extension .txt
        if not fichier_combine.endswith('.txt'):
            fichier_combine += '.txt'
        
        combiner_fichiers_txt(dossier, fichier_combine)
        
    except KeyboardInterrupt:
        print("\nOpération annulée par l'utilisateur")
    except Exception as e:
        print(f"Erreur: {e}")