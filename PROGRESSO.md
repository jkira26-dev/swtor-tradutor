# Progresso do Desenvolvimento - SWTOR Tradutor PT-BR

## Fase 1: Descoberta e Análise (Concluída)
- Mapeamento da estrutura dos arquivos `.tor` (MYP format).
- Identificação da estrutura de header da versão 6.
- Descoberta da mudança de compressão no jogo: agora usa **Zstandard (Zstd)** em vez de Zlib padrão para alguns arquivos.
- Criação de scripts utilitários: mapeamento de arquivos (`build_archive_map.py`), localização da instalação do jogo (`detect_game.py`).

## Fase 2: Implementação da Extração (Concluída)
- O `myp_parser.py` foi atualizado com suporte completo a leitura do header MYP v6.
- A biblioteca `zstandard` foi instalada e integrada ao `myp_parser.py`.
- Agora o parser consegue extrair com sucesso os bytes brutos descomprimidos (ex: `abl.stb` com ~7.6MB de tamanho original) a partir dos pacotes `.tor`.

## Fase 3: Leitura e Injeção de STB (Concluído)
- **Status Atual:** Ciclo de modificação e injeção do STB concluído.
- **Desenvolvimento Finalizado:**
  - Foi criado o script `build_patcher.py`, que atua como o motor final de parcheamento.
  - O script faz a leitura dos arquivos STB no banco de dados SQLite (`translate_pt.db3`).
  - Em seguida, mapeia as strings em inglês (`text_en`) para os textos em português brasileiro de forma ultra-rápida usando um dicionário O(1).
  - O `myp_parser.py` foi atualizado para comprimir e injetar as alterações utilizando o algoritmo `zstandard` nativo, preservando com segurança os dados do arquivo `.tor` ao acrescentar as strings modificadas ao fim do arquivo.
