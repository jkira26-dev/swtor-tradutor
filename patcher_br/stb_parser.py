"""
SWTOR Tradutor PT-BR - Parser de Arquivos STB (String Table Binary)
===================================================================
Módulo responsável por ler e escrever arquivos .stb do SWTOR.

O formato STB armazena strings localizadas do jogo.
Nova estrutura (Versão 1, usada no SWTOR 7.0+):
  - Header (7 bytes)
    - Magic: 3 bytes (0x01, 0x00, 0x00)
    - NumRows: 4 bytes (int32 LE)
  - Row Index Table (NumRows * 26 bytes)
    Cada row index:
    - ID: 8 bytes (int64 LE) — Identificador único da string
    - Bitflag: 2 bytes (uint16 LE)
    - Version: 4 bytes (uint32 LE)
    - Length: 4 bytes (uint32 LE) — Tamanho da string em bytes
    - Offset: 4 bytes (uint32 LE) — Offset no bloco de dados
    - Length2: 4 bytes (uint32 LE)
  - String Data Block
    Strings armazenadas como UTF-8
"""

import struct
import io
import html


class STBEntry:
    """Representa uma entrada (string) no arquivo STB"""
    
    def __init__(self, string_id=0, text="", bitflag=0, version=0, len2=0):
        self.string_id = string_id
        self.text = text
        self.bitflag = bitflag
        self.version = version
        self.len2 = len2
    
    def __repr__(self):
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        preview = preview.replace("\n", "\\n")
        return f"STBEntry(id={self.string_id}, text='{preview}')"


class STBFile:
    """
    Leitor/escritor de arquivos STB do SWTOR.
    
    Uso para leitura:
        stb = STBFile.from_bytes(raw_data)
        for entry in stb.entries:
            print(entry.string_id, entry.text)
    
    Uso para escrita:
        stb = STBFile()
        stb.entries = [STBEntry(id=123, text="Olá Mundo")]
        data = stb.to_bytes()
    """
    
    def __init__(self):
        self.magic = b"\x01\x00\x00"
        self.entries = []
    
    @classmethod
    def from_bytes(cls, data):
        """Cria um STBFile a partir de bytes brutos"""
        stb = cls()
        
        # Verificar novo formato vs formato antigo
        if data[:3] == b"\x01\x00\x00":
            # Novo formato (v1)
            num_rows = struct.unpack("<I", data[3:7])[0]
            
            row_index = []
            for i in range(num_rows):
                start = 7 + i * 26
                row_data = data[start:start+26]
                string_id, bitflag, version, length, offset, len2 = struct.unpack("<qHIIII", row_data)
                row_index.append((string_id, bitflag, version, length, offset, len2))
                
            for string_id, bitflag, version, length, offset, len2 in row_index:
                raw_text = data[offset:offset+length]
                # Limpar bytes nulos no final, se houver
                raw_text = raw_text.rstrip(b"\x00")
                text = raw_text.decode("utf-8", errors="replace")
                
                stb.entries.append(STBEntry(string_id, text, bitflag, version, len2))
        else:
            # Formato antigo
            f = io.BytesIO(data)
            magic = struct.unpack("<i", f.read(4))[0]
            num_rows = struct.unpack("<i", f.read(4))[0]
            
            if num_rows < 0 or num_rows > 1_000_000:
                raise ValueError(f"Número de rows inválido no formato antigo: {num_rows}")
            
            row_index = []
            for _ in range(num_rows):
                string_id = struct.unpack("<q", f.read(8))[0]
                offset = struct.unpack("<i", f.read(4))[0]
                row_index.append((string_id, offset))
            
            data_start = f.tell()
            for string_id, offset in row_index:
                f.seek(data_start + offset)
                chars = []
                while True:
                    byte = f.read(1)
                    if byte == b"\x00" or byte == b"":
                        break
                    chars.append(byte)
                text = b"".join(chars).decode("utf-8", errors="replace")
                stb.entries.append(STBEntry(string_id, text))
                
        return stb
    
    def to_bytes(self):
        """Serializa o STBFile de volta para bytes no novo formato (v1)"""
        buf = io.BytesIO()
        
        # Header (7 bytes)
        buf.write(self.magic)
        buf.write(struct.pack("<I", len(self.entries)))
        
        # Como precisamos saber os offsets dos blocos de dados antes de gravar as rows,
        # primeiro vamos codificar as strings.
        encoded_strings = []
        offsets = []
        
        # O bloco de dados começa após o Header (7) e a Tabela de Índice (NumRows * 26)
        current_offset = 7 + len(self.entries) * 26
        
        for entry in self.entries:
            # Novo formato não requer explicitamente null-terminator se usar length,
            # mas vamos manter o comportamento do original (text encoded diretamente).
            encoded = entry.text.encode("utf-8")
            # Adicionar null terminator por segurança, pois algumas tools esperam
            encoded += b"\x00"
            
            offsets.append(current_offset)
            encoded_strings.append(encoded)
            current_offset += len(encoded)
            
        # Escrever Tabela de Índice
        for i, entry in enumerate(self.entries):
            length = len(encoded_strings[i])
            buf.write(struct.pack(
                "<qHIIII",
                entry.string_id,
                entry.bitflag,
                entry.version,
                length,
                offsets[i],
                entry.len2 if entry.len2 else length # len2 frequentemente = length
            ))
            
        # Escrever Bloco de Dados
        for encoded in encoded_strings:
            buf.write(encoded)
            
        return buf.getvalue()
    
    def get_entry_by_id(self, string_id):
        """Busca uma entry pelo ID"""
        if not hasattr(self, '_id_to_entry') or len(self._id_to_entry) != len(self.entries):
            self._id_to_entry = {e.string_id: e for e in self.entries}
            
        return self._id_to_entry.get(string_id)
    
    def replace_text(self, string_id, new_text):
        """Substitui o texto de uma entry pelo ID"""
        entry = self.get_entry_by_id(string_id)
        if entry:
            entry.text = new_text
            return True
        return False


def decode_html_entities(text):
    if not text:
        return text
    return html.unescape(text)
