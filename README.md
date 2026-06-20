# SWTOR Tradutor PT-BR (Patcher)

Este é um projeto de código aberto para aplicar traduções em português brasileiro ao jogo *Star Wars: The Old Republic* (SWTOR).

## Visão Geral

Nas versões mais recentes (SWTOR 7.0+), o jogo passou a usar pacotes comprimidos em `Zstandard` com uma nova formatação binária de strings (STB Versão 1). Este patcher é escrito do zero em Python para conseguir ler o novo modelo, substituir as *strings* pelos textos traduzidos através de um banco de dados e injetar tudo com segurança no final dos pacotes locais `.tor`.

## Recursos
- **Leitura Nativa MYP/STB**: Módulos para parsear e formatar arquivos `STB` V1 e `MYP` (v6).
- **Injeção de Código Zstandard**: Adiciona conteúdo alterado sem corromper ou deletar os dados originais do `.tor`.
- **GUI Intuitiva**: Interface fácil com auto-detecção da pasta Steam para os jogadores instalarem o Mod com 1 clique.
- **Rápido**: Mapeamento de O(1) que permite a substituição de dezenas de milhares de *strings* em segundos.

## Como Compilar o Código Fonte

Se você deseja compilar o seu próprio executável (.exe) a partir da fonte:
1. Instale o Python (3.10 ou mais recente).
2. Instale as dependências: `pip install pyinstaller zstandard`
3. Rode o comando:
   `pyinstaller --onefile --windowed --name "SWTOR_Tradutor_PTBR" swtor_tradutor_gui.py`

## Para Jogadores (Como instalar a Tradução)

1. Faça o download da pasta com a tradução na aba de `Releases` do GitHub.
2. Extraia o arquivo `.zip` e certifique-se de que a pasta `db/` (contendo os arquivos do banco de dados) esteja no mesmo local que o executável `SWTOR_Tradutor_PTBR.exe`.
3. Rode o programa `SWTOR_Tradutor_PTBR.exe`.
4. Se ele não encontrar a pasta do jogo sozinho, clique em "Procurar..." e selecione a pasta raiz de instalação do SWTOR.
5. Clique em "Instalar Tradução" e aguarde a mensagem de sucesso no terminal da tela!

## Estrutura do Projeto
- `swtor_tradutor_gui.py`: Interface Gráfica e ponto de entrada principal do usuário.
- `build_patcher.py`: O "motor" do patcher. Ele lê os arquivos `swtor_en-us_*.tor`, compara os STBs com o SQLite e aciona a injeção.
- `patcher_br/`: Contém as bibliotecas criadas para desencapsular (`myp_parser.py`) e traduzir (`stb_parser.py`) a matriz de dados do jogo.
