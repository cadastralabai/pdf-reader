# PDF Reader LangChain

Este projeto é uma aplicação para leitura e processamento de PDFs utilizando [LangChain](https://python.langchain.com/) e OCR com [Tesseract](https://github.com/tesseract-ocr/tesseract), com suporte ao idioma português.

## Funcionalidades

- Extração de texto de arquivos PDF, incluindo PDFs digitalizados (imagens).
- Suporte ao idioma português para OCR.
- Integração com LangChain para processamento avançado do texto extraído.

## Pré-requisitos

- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- Pip

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/pdf_reader_langchain.git
cd pdf_reader_langchain
```

### 2. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 3. Instale o Tesseract OCR

#### Windows

1. Baixe o instalador em: https://github.com/tesseract-ocr/tesseract/releases
2. Durante a instalação, selecione o idioma **Português** (Portuguese).
3. Adicione o caminho do executável (`tesseract.exe`) à variável de ambiente `PATH`.

#### Linux (Ubuntu)

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-por
```

#### macOS

```bash
brew install tesseract
brew install tesseract-lang
```

Para adicionar o idioma português:

```bash
brew install tesseract-lang
# Ou baixe manualmente o arquivo .traineddata para o diretório de idiomas do Tesseract
```

### 4. Configuração do arquivo `.env`

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Caminho para o executável do Tesseract (necessário se não estiver no PATH)
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe

# Outras configurações do projeto
OPENAI_API_KEY=sua_api_key_aqui
```

> **Nota:** Ajuste o caminho do `TESSERACT_CMD` conforme o local de instalação no seu sistema.

## Uso

Execute o script principal conforme a documentação do projeto:

```bash
python agent.py
```

## Observações

- Certifique-se de que o idioma português está instalado no Tesseract.
