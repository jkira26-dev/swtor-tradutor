"""
SWTOR Tradutor PT-BR - Módulo de Tradução
==========================================
Conecta o banco de dados SQLite com os parsers de MYP e STB
para aplicar as traduções nos arquivos do jogo.
"""

import sqlite3
import os
import html
import sys


class TranslationDB:
    """
    Interface com o banco de dados de traduções (translate_pt.db3).
    
    Tabela principal: Translated
    Colunas relevantes:
        - fileinfo: nome do arquivo .stb (ex: "abl.stb")
        - hash: hash do arquivo .tor que contém este .stb
        - key_unic: ID único da string (corresponde ao string_id no STB)
        - text_en: texto original em inglês
        - text_pt_m: tradução PT-BR masculino
        - text_pt_w: tradução PT-BR feminino
        - translator_pt_m: quem traduziu (masc.)
        - translator_pt_w: quem traduziu (fem.)
    """
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Abre conexão com o banco de dados"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Banco de dados não encontrado: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self
    
    def close(self):
        """Fecha a conexão"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_stats(self):
        """Retorna estatísticas gerais da tradução"""
        cursor = self.conn.cursor()
        
        total = cursor.execute("SELECT COUNT(*) FROM Translated").fetchone()[0]
        
        translated_m = cursor.execute(
            "SELECT COUNT(*) FROM Translated "
            "WHERE text_pt_m IS NOT NULL AND text_pt_m != '' AND text_pt_m != text_en"
        ).fetchone()[0]
        
        translated_w = cursor.execute(
            "SELECT COUNT(*) FROM Translated "
            "WHERE text_pt_w IS NOT NULL AND text_pt_w != '' AND text_pt_w != text_en"
        ).fetchone()[0]
        
        stb_files = cursor.execute(
            "SELECT COUNT(DISTINCT fileinfo) FROM Translated"
        ).fetchone()[0]
        
        return {
            "total_strings": total,
            "translated_male": translated_m,
            "translated_female": translated_w,
            "stb_files": stb_files,
            "progress_pct": round(translated_m / total * 100, 2) if total > 0 else 0,
        }
    
    def get_stb_files(self):
        """Retorna lista de todos os arquivos .stb únicos no banco"""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            "SELECT DISTINCT fileinfo FROM Translated ORDER BY fileinfo"
        ).fetchall()
        return [row["fileinfo"] for row in rows]
    
    def get_translations_for_stb(self, stb_filename, gender="m"):
        """
        Retorna todas as traduções para um determinado arquivo .stb.
        
        Args:
            stb_filename: nome do arquivo STB (ex: "quest.stb")
            gender: "m" para masculino, "w" para feminino
        
        Returns:
            dict {string_id: translated_text}
        """
        col = f"text_pt_{gender}"
        cursor = self.conn.cursor()
        
        rows = cursor.execute(
            f"SELECT key_unic, text_en, {col} FROM Translated "
            f"WHERE fileinfo = ? AND {col} IS NOT NULL AND {col} != '' "
            f"ORDER BY Order_by",
            (stb_filename,)
        ).fetchall()
        
        translations = {}
        for row in rows:
            try:
                string_id = int(row["key_unic"])
            except (ValueError, TypeError):
                continue
            
            text = row[col]
            # Decodificar entidades HTML do banco
            text = html.unescape(text) if text else ""
            
            if text:
                translations[string_id] = text
        
        return translations
    
    def get_translated_stb_files(self, gender="m"):
        """
        Retorna apenas os arquivos .stb que possuem ao menos uma tradução.
        """
        col = f"text_pt_{gender}"
        cursor = self.conn.cursor()
        rows = cursor.execute(
            f"SELECT DISTINCT fileinfo FROM Translated "
            f"WHERE {col} IS NOT NULL AND {col} != '' "
            f"ORDER BY fileinfo"
        ).fetchall()
        return [row["fileinfo"] for row in rows]
    
    def search_translations(self, query, limit=20):
        """Busca traduções por texto (inglês ou português)"""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            "SELECT fileinfo, key_unic, text_en, text_pt_m, translator_pt_m "
            "FROM Translated "
            "WHERE text_en LIKE ? OR text_pt_m LIKE ? "
            "LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()
        return [dict(row) for row in rows]


def print_stats(db_path):
    """Imprime estatísticas formatadas do banco de dados"""
    with TranslationDB(db_path) as db:
        stats = db.get_stats()
        print("=" * 55)
        print("  SWTOR Tradutor PT-BR — Estatísticas da Tradução")
        print("=" * 55)
        print(f"  Total de strings no banco:     {stats['total_strings']:>10,}")
        print(f"  Traduzidas (masculino):        {stats['translated_male']:>10,}")
        print(f"  Traduzidas (feminino):         {stats['translated_female']:>10,}")
        print(f"  Arquivos .stb únicos:          {stats['stb_files']:>10,}")
        print(f"  Progresso geral:               {stats['progress_pct']:>9}%")
        print("=" * 55)


if __name__ == "__main__":
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "db", "translate_pt.db3"
    )
    print_stats(db_path)
