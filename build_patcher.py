import os
import sys
import sqlite3
import glob
import html

from patcher_br.myp_parser import MYPArchive, load_hash_list
from patcher_br.stb_parser import STBFile

def run_patcher(game_path, logger=print):
    # Determine base path for data files (handles both script and PyInstaller .exe execution)
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    assets_dir = os.path.join(game_path, "Assets")
    hash_list_path = os.path.join(base_path, "db", "hashes_filename.txt")
    db_path = os.path.join(base_path, "db", "translate_pt.db3")
    
    if not os.path.exists(assets_dir):
        logger(f"Erro: Pasta Assets não encontrada em: {assets_dir}")
        return False
        
    logger("Carregando lista de hashes...")
    hash_map = load_hash_list(hash_list_path)
    
    logger("Conectando ao banco de dados de tradução...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Pegar todos os arquivos listados na DB
    cursor.execute("SELECT DISTINCT fileinfo FROM Translated")
    db_files = [r[0] for r in cursor.fetchall()]
    logger(f"Encontrados {len(db_files)} arquivos .stb no banco de dados para traduzir.")
    
    # Encontrar todos os arquivos .tor do idioma (onde os STBs ficam armazenados)
    tor_files = glob.glob(os.path.join(assets_dir, "swtor_en-us_*.tor"))
    logger(f"Verificando {len(tor_files)} arquivos .tor...")
    
    total_injected = 0
    total_strings = 0
    
    for tor_file in tor_files:
        logger(f"\nAbrindo {os.path.basename(tor_file)}...")
        try:
            archive = MYPArchive(tor_file)
            archive.load()
            archive.resolve_names(hash_map)
        except Exception as e:
            logger(f"  Erro ao carregar {tor_file}: {e}")
            continue
            
        entries_to_patch = []
        for entry in archive.entries:
            if not entry.file_name:
                continue
                
            if entry.file_name.endswith(".stb"):
                # Verificar se este STB está no nosso banco de dados
                matched_db_file = None
                for db_file in db_files:
                    if entry.file_name.endswith(db_file):
                        matched_db_file = db_file
                        break
                        
                if matched_db_file:
                    entries_to_patch.append((entry, matched_db_file))
                    
        if not entries_to_patch:
            logger("  Nenhum STB correspondente encontrado neste arquivo.")
            continue
            
        logger(f"  Encontrados {len(entries_to_patch)} STBs para patchear.")
        
        for entry, db_file in entries_to_patch:
            logger(f"  > Processando {db_file}...")
            
            # Buscar traduções para este arquivo
            cursor.execute(
                "SELECT text_en, text_pt_m, text_pt_w FROM Translated WHERE fileinfo=? AND text_pt_m IS NOT NULL AND text_pt_m != ''", 
                (db_file,)
            )
            translations = cursor.fetchall()
            
            if not translations:
                logger("    Sem traduções.")
                continue
                
            en_to_pt = {}
            for row in translations:
                text_en, pt_m, pt_w = row
                new_text = pt_m if pt_m else pt_w
                if text_en and new_text:
                    en_to_pt[html.unescape(text_en)] = html.unescape(new_text)
                    
            # Extrair, Parsear e Substituir
            raw_data = archive.extract_entry_data(entry)
            try:
                stb = STBFile.from_bytes(raw_data)
            except Exception as e:
                logger(f"    Erro ao ler STB: {e}")
                continue
                
            replaced_count = 0
            for stb_entry in stb.entries:
                if stb_entry.text in en_to_pt:
                    stb_entry.text = en_to_pt[stb_entry.text]
                    replaced_count += 1
                    
            logger(f"    Substituídas {replaced_count} strings.")
            
            if replaced_count > 0:
                logger("    Gerando novos bytes e injetando...")
                new_raw_data = stb.to_bytes()
                try:
                    archive.inject_file(entry, new_raw_data)
                    logger("    [SUCESSO] Injetado!")
                    total_injected += 1
                    total_strings += replaced_count
                except Exception as e:
                    logger(f"    [ERRO] Falha ao injetar: {e}")
                    
    conn.close()
    logger(f"\nConcluído! Total de arquivos patcheados: {total_injected}")
    logger(f"Total de strings substituídas: {total_strings}")
    return True

if __name__ == "__main__":
    game_path = r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic"
    run_patcher(game_path)
