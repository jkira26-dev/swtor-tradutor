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

## Fase 3: Leitura e Injeção de STB (Concluída)
- **Status:** Ciclo de modificação e injeção do STB concluído.
- **Desenvolvimento Finalizado:**
  - Foi criado o script `build_patcher.py`, que atua como o motor final de parcheamento.
  - O script faz a leitura dos arquivos STB no banco de dados SQLite (`translate_pt.db3`).
  - Em seguida, mapeia as strings em inglês (`text_en`) para os textos em português brasileiro de forma ultra-rápida usando um dicionário O(1).
  - O `myp_parser.py` foi atualizado para comprimir e injetar as alterações utilizando o algoritmo `zstandard` nativo, preservando com segurança os dados do arquivo `.tor` ao acrescentar as strings modificadas ao fim do arquivo.

## Fase 4: Compilação do Executável (Em Andamento)
- **Motor do patcher** (`build_patcher.py`) atualizado com:
  - Callbacks de progresso `on_progress(current, total)` e `on_file(filename)` para integração com a GUI.
  - Suporte a **backup automático** dos arquivos `.tor` antes de modificar.
  - Validação de arquivos de dados (DB e hashes) antes de iniciar.
  - Logs mais detalhados com contagem de STBs em tempo real.
- **Arquivo `.spec`** (`SWTOR_Tradutor_PTBR_v3.spec`) corrigido:
  - Modo **onedir** (pasta de distribuição, não .exe único).
  - Inclui `db/translate_pt.db3` e `db/hashes_filename.txt` como dados.
  - Hidden imports: `zstandard`, `patcher_br`, `patcher_br.myp_parser`, `patcher_br.stb_parser`, `winreg`.
  - Exclui módulos pesados não utilizados para reduzir tamanho.
- Build PyInstaller rodando via `pyinstaller --clean SWTOR_Tradutor_PTBR_v3.spec`.

## Fase 5: Melhoria da Interface Gráfica (Concluída)
- **Interface** (`swtor_tradutor_gui.py`) completamente reformulada:
  - **Barra de progresso real** (`ttk.Progressbar`) integrada ao patcher via callbacks.
  - **Contador de STBs em tempo real**: exibe "X / Y STBs" durante a instalação.
  - **Log colorido**: mensagens de sucesso (verde), erro (vermelho), aviso (laranja) e detalhe (cinza).
  - **Checkbox de backup**: opção para criar backup dos `.tor` antes de modificar.
  - **Operações thread-safe**: todas as atualizações de UI usam `after()` para segurança.
  - **Dark theme aprimorado**: paleta de cores coerente com superfícies, bordas e accents distintos.
  - **Redimensionável**: janela pode ser redimensionada para ver mais do log.
  - **Hover effects** no botão principal.
  - Detecção de caminho do jogo ampliada (mais drives/caminhos comuns).
