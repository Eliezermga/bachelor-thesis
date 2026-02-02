import os
import sys
from pathlib import Path
import re
import warnings
from datetime import datetime
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

# Installation des dépendances si nécessaire
try:
    import fitz  # PyMuPDF
    import pdfplumber
    import pandas as pd
    from PIL import Image
    import pytesseract
    import numpy as np
except ImportError as e:
    print(f"Module manquant: {e}")
    print("Installation des dépendances nécessaires...")
    import subprocess
    
    # Liste des packages à installer
    packages = [
        "pymupdf", 
        "pdfplumber", 
        "pandas",
        "pytesseract", 
        "pillow", 
        "numpy"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except:
            print(f"  Échec installation de {package}, tentative suivante...")
    
    # Réimport après installation
    try:
        import fitz
        import pdfplumber
        import pandas as pd
        from PIL import Image
        import pytesseract
        import numpy as np
    except ImportError as e:
        print(f"Erreur d'importation après installation: {e}")
        print("Installation manuelle recommandée:")
        print("pip install pymupdf pdfplumber pandas pytesseract pillow numpy")
        sys.exit(1)

class PDFRawTextExtractor:
    def __init__(self, input_folder, output_folder=None, preserve_layout=True):
        """
        Initialise l'extracteur de texte brut PDF
        
        Args:
            input_folder: Dossier contenant les PDFs
            output_folder: Dossier de sortie pour les textes extraits
            preserve_layout: Préserver la mise en page originale
        """
        self.input_folder = Path(input_folder)
        
        if output_folder:
            self.output_folder = Path(output_folder)
        else:
            self.output_folder = self.input_folder / "textes_bruts"
        
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        self.preserve_layout = preserve_layout
        self.min_text_length = 10
        
        # Pour OCR, utiliser le mode le plus neutre possible
        self.ocr_config = r'--oem 1 --psm 3 -c preserve_interword_spaces=1'
    
    def extraire_avec_pymupdf_mode_brut(self, pdf_path):
        """Extraction brute avec PyMuPDF sans interprétation"""
        text_parts = []
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Mode texte brut
                text = page.get_text()
                
                if text and text.strip():
                    text_parts.append(text)
            
            doc.close()
            return "\n".join(text_parts)
        except Exception as e:
            print(f"  Erreur PyMuPDF brut: {e}")
            return ""
    
    def extraire_avec_pymupdf_blocks(self, pdf_path):
        """Extraction par blocs avec coordonnées"""
        text_data = []
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extraire avec préservation du layout
                blocks = page.get_text("blocks")
                
                page_text = []
                for block in blocks:
                    x0, y0, x1, y1, text, block_no, block_type = block
                    
                    # Nettoyer légèrement mais garder la structure
                    clean_text = text.strip()
                    if clean_text:
                        page_text.append(clean_text)
                
                if page_text:
                    text_data.append("\n".join(page_text))
            
            doc.close()
            
            return "\n".join(text_data)
        except Exception as e:
            print(f"  Erreur PyMuPDF blocks: {e}")
            return ""
    
    def extraire_avec_pdfplumber_brut(self, pdf_path):
        """Extraction avec pdfplumber en mode brut"""
        text_parts = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extraire le texte brut
                    text = page.extract_text()
                    
                    if text:
                        # Garder les sauts de ligne originaux
                        text_parts.append(text)
            
            return "\n".join(text_parts)
        except Exception as e:
            print(f"  Erreur pdfplumber brut: {e}")
            return ""
    
    def extraire_avec_ocr_neutre(self, pdf_path):
        """OCR sans interprétation linguistique"""
        text_parts = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Vérifier d'abord si la page a du texte vectoriel
                text_vectoriel = page.get_text()
                if text_vectoriel and len(text_vectoriel.strip()) > self.min_text_length:
                    continue  # Passer à la page suivante si texte vectoriel existe
                
                # Sinon, faire OCR
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                    img_data = pix.tobytes("ppm")
                    
                    from io import BytesIO
                    img = Image.open(BytesIO(img_data))
                    
                    # Convertir en niveaux de gris pour meilleur OCR
                    if img.mode != 'L':
                        img = img.convert('L')
                    
                    # OCR avec configuration neutre
                    text = pytesseract.image_to_string(
                        img, 
                        config=self.ocr_config
                    )
                    
                    if text.strip():
                        text_parts.append(text)
                        
                except Exception as ocr_error:
                    print(f"    OCR page {page_num + 1} échoué: {ocr_error}")
                    continue
            
            doc.close()
            return "\n".join(text_parts)
        except Exception as e:
            print(f"  Erreur OCR neutre: {e}")
            return ""
    
    def extraire_texte_exact(self, pdf_path):
        """Extraction du texte exact tel qu'il apparaît"""
        print(f"\nTraitement de: {pdf_path.name}")
        
        # Essayer plusieurs méthodes pour obtenir le maximum de texte
        methodes = [
            ("PDFPlumber", self.extraire_avec_pdfplumber_brut),
            ("PyMuPDF", self.extraire_avec_pymupdf_mode_brut),
        ]
        
        tous_les_textes = []
        texte_principal = ""
        
        # D'abord essayer les méthodes de texte vectoriel
        for methode_name, methode_func in methodes:
            try:
                texte = methode_func(pdf_path)
                if texte and len(texte.strip()) > self.min_text_length:
                    if not texte_principal or len(texte) > len(texte_principal):
                        texte_principal = texte
                    print(f"  ✓ {methode_name}: {len(texte)} caractères")
                else:
                    print(f"  ✗ {methode_name}: texte insuffisant")
            except Exception as e:
                print(f"  ✗ {methode_name} échoué: {e}")
        
        # Si pas de texte vectoriel, essayer OCR
        if not texte_principal:
            print("  Tentative OCR...")
            try:
                texte_ocr = self.extraire_avec_ocr_neutre(pdf_path)
                if texte_ocr and len(texte_ocr.strip()) > self.min_text_length:
                    texte_principal = texte_ocr
                    print(f"  ✓ OCR: {len(texte_ocr)} caractères")
                else:
                    print(f"  ✗ OCR: texte insuffisant")
            except Exception as e:
                print(f"  ✗ OCR échoué: {e}")
        
        if texte_principal:
            # Nettoyer MINIMUM pour garder l'originalité
            texte_principal = self.nettoyer_minimum(texte_principal)
            tous_les_textes.append(texte_principal)
        else:
            print(f"  ⚠ Aucune méthode n'a réussi à extraire du texte")
            return ""
        
        # Combiner tous les textes
        texte_complet = "\n".join(tous_les_textes)
        
        return texte_complet
    
    def nettoyer_minimum(self, text):
        """Nettoyage minimal pour garder les caractères originaux"""
        if not text:
            return ""
        
        # Supprimer seulement les caractères de contrôle non-affichables
        cleaned = []
        for char in text:
            # Garder tous les caractères Unicode imprimables
            if ord(char) >= 32 or char in '\n\r\t':
                cleaned.append(char)
        
        result = ''.join(cleaned)
        
        # Réduire les espaces multiples, mais garder les sauts de ligne
        lines = result.split('\n')
        cleaned_lines = []
        for line in lines:
            # Réduire les espaces multiples dans une ligne
            line = re.sub(r'[ \t]+', ' ', line)
            line = line.strip()
            if line:  # Garder seulement les lignes non vides
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def sauvegarder_texte_brut(self, pdf_path, texte):
        """Sauvegarde le texte exact extrait"""
        if not texte or len(texte.strip()) < self.min_text_length:
            return None
        
        # Créer un nom de fichier de sortie
        nom_sortie = f"{pdf_path.stem}_EXACT.txt"
        chemin_sortie = self.output_folder / nom_sortie
        
        # Pas d'en-tête, seulement le texte brut
        contenu_complet = texte
        
        # Sauvegarder en UTF-8 pour garder tous les caractères
        try:
            with open(chemin_sortie, 'w', encoding='utf-8', errors='replace') as f:
                f.write(contenu_complet)
            
            print(f"  ✓ Texte sauvegardé: {chemin_sortie}")
            
            # Statistiques
            lines = texte.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            print(f"    Caractères: {len(texte)}")
            print(f"    Lignes totales: {len(lines)}")
            print(f"    Lignes non vides: {len(non_empty_lines)}")
            
            return {
                'fichier': pdf_path.name,
                'sortie_txt': str(chemin_sortie),
                'caracteres': len(texte),
                'lignes': len(lines),
                'lignes_non_vides': len(non_empty_lines)
            }
            
        except Exception as e:
            print(f"  ✗ Erreur sauvegarde: {e}")
            return None
    
    def traiter_pdf_simple(self, pdf_path):
        """Version simplifiée pour traitement parallèle"""
        try:
            print(f"Traitement: {pdf_path.name}")
            
            # Extraire le texte exact
            texte = self.extraire_texte_exact(pdf_path)
            
            if not texte or len(texte.strip()) < self.min_text_length:
                print(f"  ⚠ Texte insuffisant extrait")
                return None
            
            # Sauvegarder
            resultat = self.sauvegarder_texte_brut(pdf_path, texte)
            
            return resultat
            
        except Exception as e:
            print(f"  ✗ ERREUR: {str(e)}")
            return None
    
    def parcourir_dossier_sequentiel(self):
        """Version séquentielle simplifiée"""
        # Chercher tous les PDFs
        extensions = ['.pdf', '.PDF']
        pdf_files = []
        
        for ext in extensions:
            pdf_files.extend(self.input_folder.glob(f"**/*{ext}"))
        
        if not pdf_files:
            print(f"Aucun fichier PDF trouvé dans {self.input_folder}")
            return []
        
        print(f"Nombre de fichiers PDF trouvés: {len(pdf_files)}")
        
        resultats = []
        
        print("Traitement séquentiel...")
        for i, pdf in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] ", end="")
            result = self.traiter_pdf_simple(pdf)
            if result:
                resultats.append(result)
        
        return resultats
    
    def parcourir_dossier_parallele(self):
        """Version parallèle"""
        # Chercher tous les PDFs
        extensions = ['.pdf', '.PDF']
        pdf_files = []
        
        for ext in extensions:
            pdf_files.extend(self.input_folder.glob(f"**/*{ext}"))
        
        if not pdf_files:
            print(f"Aucun fichier PDF trouvé dans {self.input_folder}")
            return []
        
        print(f"Nombre de fichiers PDF trouvés: {len(pdf_files)}")
        
        resultats = []
        
        print("Traitement parallèle activé...")
        
        # Déterminer le nombre de workers
        cpu_count = os.cpu_count() or 2
        max_workers = min(4, cpu_count)
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            # Soumettre toutes les tâches
            for pdf in pdf_files:
                future = executor.submit(self.traiter_pdf_simple, pdf)
                futures[future] = pdf.name
            
            # Collecter les résultats
            completed = 0
            for future in as_completed(futures):
                completed += 1
                pdf_name = futures[future]
                
                try:
                    result = future.result(timeout=300)  # 5 minutes timeout
                    if result:
                        resultats.append(result)
                        print(f"[{completed}/{len(pdf_files)}] ✓ {pdf_name} terminé")
                    else:
                        print(f"[{completed}/{len(pdf_files)}] ✗ {pdf_name} échoué")
                        
                except Exception as e:
                    print(f"[{completed}/{len(pdf_files)}] ✗ {pdf_name} erreur: {e}")
        
        return resultats
    
    def generer_rapport_simple(self, resultats):
        """Génère un rapport simple"""
        if not resultats:
            return
        
        print(f"\n{'='*60}")
        print("RAPPORT FINAL D'EXTRACTION")
        print(f"{'='*60}")
        print(f"Fichiers traités avec succès: {len(resultats)}")
        print(f"Dossier de sortie: {self.output_folder}")
        
        if resultats:
            total_caracteres = sum(r['caracteres'] for r in resultats)
            total_lignes = sum(r['lignes'] for r in resultats)
            total_lignes_non_vides = sum(r.get('lignes_non_vides', 0) for r in resultats)
            
            print(f"\nStatistiques totales:")
            print(f"  Caractères totaux: {total_caracteres}")
            print(f"  Lignes totales: {total_lignes}")
            print(f"  Lignes non vides: {total_lignes_non_vides}")
            
            print(f"\nMoyennes par fichier:")
            print(f"  Caractères: {total_caracteres/len(resultats):.0f}")
            print(f"  Lignes: {total_lignes/len(resultats):.0f}")
            print(f"  Lignes non vides: {total_lignes_non_vides/len(resultats):.0f}")
        
        print(f"\nFichiers générés:")
        print(f"  • Pour chaque PDF: fichier _EXACT.txt")
        print(f"  • Tous dans: {self.output_folder}")

def main():
    """Fonction principale simplifiée"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   EXTRACTEUR DE TEXTE PDF - MODE EXACT           ║
    ║   Extraction brute sans interprétation           ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # Demander le dossier
    dossier_input = input("Chemin du dossier contenant les PDFs: ").strip()
    
    if not os.path.exists(dossier_input):
        print(f"❌ Erreur: Dossier '{dossier_input}' introuvable")
        return
    
    # Simplifier les options
    dossier_output = input("Dossier de sortie (laisser vide pour 'textes_bruts'): ").strip()
    
    # Demander mode parallèle ou séquentiel
    print("\nMode de traitement:")
    print("1. Séquentiel (plus stable)")
    print("2. Parallèle (plus rapide pour 86 fichiers)")
    choix_mode = input("Choix [1/2]: ").strip()
    
    # Confirmation
    print(f"\nConfiguration:")
    print(f"  Source: {dossier_input}")
    print(f"  Sortie: {dossier_output or 'textes_bruts'}")
    print(f"  Mode: {'Parallèle' if choix_mode == '2' else 'Séquentiel'}")
    
    confirmer = input("\nDémarrer l'extraction? (o/n): ").strip().lower()
    if confirmer != 'o':
        print("Annulé.")
        return
    
    # Créer l'extracteur
    extracteur = PDFRawTextExtractor(
        input_folder=dossier_input,
        output_folder=dossier_output or None,
        preserve_layout=False  # Mode simplifié
    )
    
    # Démarrer
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print("DÉMARRAGE DE L'EXTRACTION...")
    print(f"{'='*60}")
    
    if choix_mode == '2':
        resultats = extracteur.parcourir_dossier_parallele()
    else:
        resultats = extracteur.parcourir_dossier_sequentiel()
    
    end_time = datetime.now()
    duree = end_time - start_time
    
    # Générer rapport
    extracteur.generer_rapport_simple(resultats)
    
    print(f"\n{'='*60}")
    print("EXTRACTION TERMINÉE !")
    print(f"{'='*60}")
    print(f"Durée totale: {duree}")
    
    # Ouvrir le dossier de sortie
    if resultats:
        ouvrir = input("\nOuvrir le dossier de sortie? (o/n): ").strip().lower()
        if ouvrir == 'o':
            try:
                import platform
                if platform.system() == "Windows":
                    os.startfile(extracteur.output_folder)
                elif platform.system() == "Darwin":
                    os.system(f"open '{extracteur.output_folder}'")
                else:
                    os.system(f"xdg-open '{extracteur.output_folder}'")
            except:
                print(f"Chemin: {extracteur.output_folder}")

if __name__ == "__main__":
    # Désactiver les warnings
    warnings.filterwarnings('ignore')
    
    # Vérifier Tesseract
    try:
        pytesseract.get_tesseract_version()
    except:
        print("⚠ AVERTISSEMENT: Tesseract OCR n'est pas installé.")
        print("L'extraction des PDF scannés sera limitée.")
        print("Continuer quand même...")
    
    # Lancer le programme
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Extraction interrompue par l'utilisateur.")
    except Exception as e:
        print(f"\n\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur Entrée pour quitter...")