import os
import sys
import sqlite3
import glob
import html
import shutil
import datetime

from patcher_br.myp_parser import MYPArchive, load_hash_list
from patcher_br.stb_parser import STBFile


def _get_base_path():
    """Retorna o diretório base para buscar arquivos de dados (DB, hashes).
    Compatível com execução via script Python e via PyInstaller (.exe).
    """
    if getattr(sys, 'frozen', False):
        # No PyInstaller >= 6.0 em modo onedir, os arquivos de dados ficam na pasta _internal (sys._MEIPASS)
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def create_backup(tor_files, backup_dir, logger=print):
    """Cria cópias de segurança dos arquivos .tor antes de modificá-los.
    
    Args:
        tor_files: Lista de caminhos dos arquivos .tor a fazer backup.
        backup_dir: Diretório onde os backups serão salvos.
        logger: Função de log.
    
    Returns:
        True se todos os backups foram criados, False se houve erro.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
    
    try:
        os.makedirs(backup_path, exist_ok=True)
        logger(f"Criando backup em: {backup_path}")
        
        for tor_file in tor_files:
            basename = os.path.basename(tor_file)
            dest = os.path.join(backup_path, basename)
            logger(f"  Copiando {basename}...")
            shutil.copy2(tor_file, dest)
        
        logger(f"Backup concluído: {len(tor_files)} arquivo(s) salvo(s).")
        return True
    except Exception as e:
        logger(f"[ERRO] Falha ao criar backup: {e}")
        return False


def run_patcher(game_path, logger=print, on_progress=None, on_file=None, make_backup=False):
    """Motor principal de patch do SWTOR Tradutor PT-BR.
    
    Args:
        game_path: Caminho para a pasta de instalação do SWTOR.
        logger: Função de log (str -> None). Padrão: print.
        on_progress: Callback de progresso (current: int, total: int) -> None.
                     Chamado a cada STB processado.
        on_file: Callback de arquivo atual (filename: str) -> None.
                 Chamado ao iniciar o processamento de cada arquivo .tor.
        make_backup: Se True, cria backup dos .tor antes de modificar.
    
    Returns:
        True se o patch foi aplicado com sucesso, False caso contrário.
    """
    base_path = _get_base_path()
    assets_dir = os.path.join(game_path, "Assets")
    hash_list_path = os.path.join(base_path, "db", "hashes_filename.txt")
    db_path = os.path.join(base_path, "db", "translate_pt.db3")

    if not os.path.exists(assets_dir):
        logger(f"Erro: Pasta Assets não encontrada em: {assets_dir}")
        return False

    if not os.path.exists(hash_list_path):
        logger(f"Erro: Lista de hashes não encontrada em: {hash_list_path}")
        return False

    if not os.path.exists(db_path):
        logger(f"Erro: Banco de dados não encontrado em: {db_path}")
        return False

    logger("Carregando lista de hashes...")
    hash_map = load_hash_list(hash_list_path)

    logger("Conectando ao banco de dados de tradução...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Pegar todos os arquivos listados no DB
    cursor.execute("SELECT DISTINCT fileinfo FROM Translated")
    db_files = [r[0] for r in cursor.fetchall()]
    logger(f"Encontrados {len(db_files)} arquivos .stb no banco de dados para traduzir.")

    # Encontrar todos os arquivos .tor do idioma inglês
    tor_files = glob.glob(os.path.join(assets_dir, "swtor_en-us_*.tor"))
    logger(f"Verificando {len(tor_files)} arquivo(s) .tor...")

    if not tor_files:
        logger("Nenhum arquivo .tor encontrado. Verifique o idioma do cliente do jogo (deve ser English).")
        conn.close()
        return False

    # --- Backup opcional ---
    if make_backup:
        backup_dir = os.path.join(game_path, "SWTOR_Tradutor_Backup")
        success = create_backup(tor_files, backup_dir, logger)
        if not success:
            logger("[AVISO] Backup falhou. Continuando sem backup...")

    # --- Pré-calcular total de STBs para barra de progresso ---
    total_stbs = 0
    stbs_per_tor = {}

    for tor_file in tor_files:
        try:
            archive = MYPArchive(tor_file)
            archive.load()
            archive.resolve_names(hash_map)
            matched = []
            for entry in archive.entries:
                if not entry.file_name:
                    continue
                for db_file in db_files:
                    if entry.file_name.endswith(db_file):
                        matched.append((entry, db_file))
                        break
            stbs_per_tor[tor_file] = (archive, matched)
            total_stbs += len(matched)
        except Exception as e:
            logger(f"  Erro ao pré-carregar {os.path.basename(tor_file)}: {e}")
            stbs_per_tor[tor_file] = None

    logger(f"Total de STBs a processar: {total_stbs}")

    # --- Processamento principal ---
    total_injected = 0
    total_strings = 0
    current_stb = 0

    for tor_file in tor_files:
        tor_name = os.path.basename(tor_file)
        logger(f"\nAbrindo {tor_name}...")

        if on_file:
            on_file(tor_name)

        if stbs_per_tor.get(tor_file) is None:
            logger("  [PULADO] Erro ao carregar este arquivo.")
            continue

        archive, entries_to_patch = stbs_per_tor[tor_file]

        if not entries_to_patch:
            logger("  Nenhum STB correspondente encontrado neste arquivo.")
            continue

        logger(f"  Encontrados {len(entries_to_patch)} STB(s) para patchear.")

        for entry, db_file in entries_to_patch:
            current_stb += 1
            logger(f"  > [{current_stb}/{total_stbs}] Processando {db_file}...")

            if on_progress:
                on_progress(current_stb, total_stbs)

            # Buscar traduções para este arquivo
            cursor.execute(
                "SELECT text_en, text_pt_m, text_pt_w FROM Translated "
                "WHERE fileinfo=? AND text_pt_m IS NOT NULL AND text_pt_m != ''",
                (db_file,)
            )
            translations = cursor.fetchall()

            if not translations:
                logger("    Sem traduções disponíveis.")
                continue

            en_to_pt = {}
            for row in translations:
                text_en, pt_m, pt_w = row
                new_text = pt_m if pt_m else pt_w
                if text_en and new_text:
                    en_to_pt[html.unescape(text_en)] = html.unescape(new_text)

            # Extrair, parsear e substituir
            try:
                raw_data = archive.extract_entry_data(entry)
            except Exception as e:
                logger(f"    [ERRO] Falha ao extrair dados: {e}")
                continue

            try:
                stb = STBFile.from_bytes(raw_data)
            except Exception as e:
                logger(f"    [ERRO] Falha ao ler STB: {e}")
                continue

            replaced_count = 0
            for stb_entry in stb.entries:
                if stb_entry.text in en_to_pt:
                    stb_entry.text = en_to_pt[stb_entry.text]
                    replaced_count += 1

            logger(f"    Substituídas {replaced_count} string(s).")

            if replaced_count > 0:
                logger("    Gerando novos bytes e injetando...")
                new_raw_data = stb.to_bytes()
                try:
                    archive.inject_file(entry, new_raw_data)
                    logger("    [OK] Injetado com sucesso!")
                    total_injected += 1
                    total_strings += replaced_count
                except Exception as e:
                    logger(f"    [ERRO] Falha ao injetar: {e}")

    conn.close()

    # Sinalizar progresso 100% ao terminar
    if on_progress and total_stbs > 0:
        on_progress(total_stbs, total_stbs)

    logger(f"\n{'='*50}")
    logger(f"CONCLUÍDO!")
    logger(f"  Arquivos STB patcheados: {total_injected}")
    logger(f"  Strings substituídas:    {total_strings}")
    logger(f"{'='*50}")

    return True


if __name__ == "__main__":
    game_path = r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic"
    run_patcher(game_path, make_backup=False)
