"""
SWTOR Tradutor PT-BR - Parser de Arquivos MYP (.tor)
====================================================
Módulo responsável por ler e escrever nos arquivos .tor do SWTOR.

O formato MYP (My P???) é o formato de arquivo proprietário da BioWare.
Estrutura:
  - Header (24 ou 28 bytes)
    - Magic: 4 bytes ("MYP\0")
    - Version: 4 bytes (uint32 LE) - Normalmente 6
    - Unknown/Dummy: 4 bytes (apenas na versão 6)
    - File Table Offset: 8 bytes (uint64 LE)  
    - Files Per Table: 4 bytes (uint32 LE)
  - File Table
    - num_files: 4 bytes (uint32 LE)
    - next_table_offset: 8 bytes (uint64 LE)
    - Array de entries (num_files * 34 bytes):
      - Offset: 8 bytes (uint64 LE)
      - HeaderSize: 4 bytes (uint32 LE)
      - CompressedSize: 4 bytes (uint32 LE)
      - UncompressedSize: 4 bytes (uint32 LE)
      - FileHash2: 4 bytes (uint32 LE)
      - FileHash1: 4 bytes (uint32 LE)
      - Extra: 4 bytes (uint32 LE)
      - CompressionMethod: 2 bytes (uint16 LE)
"""

import struct
import os
import zlib


class MYPEntry:
    """Representa um arquivo dentro de um pacote .tor"""
    
    def __init__(self):
        self.offset = 0
        self.header_size = 0
        self.compressed_size = 0
        self.uncompressed_size = 0
        self.file_hash1 = 0
        self.file_hash2 = 0
        self.extra = 0
        self.compression_method = 0
        self.file_name = None  # Preenchido depois via hash lookup
        
        # Atributos de controle interno para injeção
        self.table_offset = 0
        self.entry_index = 0
    
    @property
    def hash_key(self):
        """Retorna a chave hash combinada como string hex"""
        return f"{self.file_hash1:08X}#{self.file_hash2:08X}"
    
    @property
    def data_offset(self):
        """Offset real dos dados (após o header do arquivo)"""
        return self.offset + self.header_size
    
    def __repr__(self):
        name = self.file_name or self.hash_key
        return f"MYPEntry({name}, offset={self.offset}, size={self.uncompressed_size})"


class MYPArchive:
    """
    Leitor/escritor de arquivos .tor (formato MYP) do SWTOR.
    """
    
    MAGIC = b"MYP\x00"
    ENTRY_SIZE = 34
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.version = 0
        self.entries = []
        self._file_table_offset = 0
        self._file_count = 0
    
    def load(self):
        """Carrega o header e a tabela de arquivos do .tor"""
        with open(self.filepath, "rb") as f:
            self._read_header(f)
            self._read_file_table(f)
        return self
    
    def _read_header(self, f):
        """Lê o header do arquivo MYP de forma compatível com v5 e v6"""
        magic = f.read(4)
        if magic != self.MAGIC:
            raise ValueError(
                f"Arquivo inválido: magic esperado 'MYP\\x00', "
                f"encontrado {magic!r}"
            )
        
        self.version = struct.unpack("<I", f.read(4))[0]
        if self.version == 6:
            # Pula 4 bytes desconhecidos na versão 6
            _ = f.read(4)
            
        self._file_table_offset = struct.unpack("<Q", f.read(8))[0]
        self._file_count = struct.unpack("<I", f.read(4))[0]
    
    def _read_file_table(self, f):
        """Lê a tabela de arquivos, seguindo encadeamento de tabelas"""
        self.entries = []
        table_offset = self._file_table_offset
        
        while table_offset != 0:
            f.seek(table_offset)
            
            table_header = f.read(12)
            if len(table_header) < 12:
                break
                
            num_entries, next_offset = struct.unpack("<IQ", table_header)
            
            for i in range(num_entries):
                data = f.read(self.ENTRY_SIZE)
                if len(data) < self.ENTRY_SIZE:
                    break
                
                (
                    offset,
                    header_size,
                    compressed_size,
                    uncompressed_size,
                    hash2,
                    hash1,
                    extra,
                    compression_method,
                ) = struct.unpack("<QIIIIIIH", data)
                
                # Ignorar entries vazias
                if offset == 0 and compressed_size == 0:
                    continue
                
                entry = MYPEntry()
                entry.offset = offset
                entry.header_size = header_size
                entry.compressed_size = compressed_size
                entry.uncompressed_size = uncompressed_size
                entry.file_hash2 = hash2
                entry.file_hash1 = hash1
                entry.extra = extra
                entry.compression_method = compression_method
                entry.table_offset = table_offset
                entry.entry_index = i
                
                self.entries.append(entry)
            
            table_offset = next_offset
            
    def extract_entry_data(self, entry):
        """
        Extrai os dados brutos de uma entry.
        Retorna os bytes descomprimidos.
        """
        with open(self.filepath, "rb") as f:
            f.seek(entry.data_offset)
            raw_data = f.read(entry.compressed_size)
            
            if raw_data.startswith(b"\x28\xb5\x2f\xfd"):
                import zstandard
                dctx = zstandard.ZstdDecompressor()
                return dctx.decompress(raw_data)
                
            if entry.compression_method == 0:
                # Sem compressão
                return raw_data
            elif entry.compression_method == 1:
                # Zlib
                try:
                    return zlib.decompress(raw_data)
                except zlib.error:
                    # Tentar sem header
                    return zlib.decompress(raw_data, -15)
            else:
                raise ValueError(
                    f"Método de compressão desconhecido: "
                    f"{entry.compression_method}"
                )
                
    def inject_file(self, entry, new_uncompressed_data):
        """
        Injeta os dados de um arquivo atualizado no final do arquivo .tor,
        atualizando os offsets e o cabeçalho correspondente.
        """
        # 1. Comprimir dados novos usando zstandard
        import zstandard
        cctx = zstandard.ZstdCompressor()
        compressed_data = cctx.compress(new_uncompressed_data)
        
        # 2. Abrir o arquivo em modo leitura/escrita binária
        with open(self.filepath, "r+b") as f:
            # Copiar cabeçalho do arquivo original
            f.seek(entry.offset)
            header_bytes = f.read(entry.header_size)
            if len(header_bytes) < entry.header_size:
                raise ValueError("Não foi possível ler o cabeçalho original da entry.")
                
            # 3. Gravar novos dados no final do arquivo .tor
            f.seek(0, 2)
            new_offset = f.tell()
            f.write(header_bytes)
            f.write(compressed_data)
            
            # 4. Atualizar os atributos da entry em memória
            entry.offset = new_offset
            entry.compressed_size = len(compressed_data)
            entry.uncompressed_size = len(new_uncompressed_data)
            entry.compression_method = 1
            
            # 5. Sobrescrever a entry na tabela de arquivos física do .tor
            entry_pos = entry.table_offset + 12 + entry.entry_index * self.ENTRY_SIZE
            f.seek(entry_pos)
            updated_entry_data = struct.pack(
                "<QIIIIIIH",
                entry.offset,
                entry.header_size,
                entry.compressed_size,
                entry.uncompressed_size,
                entry.file_hash2,
                entry.file_hash1,
                entry.extra,
                entry.compression_method
            )
            f.write(updated_entry_data)
    
    def resolve_names(self, hash_map):
        """
        Resolve os nomes dos arquivos usando um mapa de hashes.
        hash_map: dict {hash_key: filename}
        """
        resolved = 0
        for entry in self.entries:
            key = entry.hash_key
            if key in hash_map:
                entry.file_name = hash_map[key]
                resolved += 1
        return resolved


def load_hash_list(filepath):
    """
    Carrega o arquivo hashes_filename.txt e retorna um dicionário
    {hash_key: filepath_in_archive}
    """
    hash_map = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("#")
            if len(parts) >= 3:
                hash_key = f"{parts[0].upper()}#{parts[1].upper()}"
                file_path = parts[2]
                hash_map[hash_key] = file_path
    return hash_map
