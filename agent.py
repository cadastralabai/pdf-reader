# agent.py (Versão com Instruções Especializadas para Texto e Imagem)

# --- IMPORTS NECESSÁRIOS ---
import fitz
import os
import pytesseract
from PIL import Image
import re
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.runnables import RunnableBranch, RunnableLambda
from dotenv import load_dotenv

# --- ETAPA DE CONFIGURAÇÃO GLOBAL ---
load_dotenv()

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")
if not pytesseract.pytesseract.tesseract_cmd or not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
    print("AVISO: Caminho do Tesseract não encontrado ou inválido. A extração OCR pode falhar.")

# --- FERRAMENTAS ---
@tool
def analisar_pdf_texto(caminho_do_pdf: str) -> dict:
    """Ferramenta RÁPIDA: Extrai texto de PDFs com texto selecionável."""
    try:
        if not os.path.exists(caminho_do_pdf):
            return {"erro": f"Arquivo não encontrado: {caminho_do_pdf}"}
        texto_completo = ""
        with fitz.open(caminho_do_pdf) as doc:
            for page in doc:
                texto_completo += page.get_text() + "\n\n"
        if not texto_completo.strip(): return {"erro": "Nenhum texto foi encontrado no PDF."}
        return {"texto_completo": texto_completo}
    except Exception as e: return {"erro": f"Falha ao processar o PDF de texto: {e}"}

@tool
def analisar_pdf_imagem_ocr(caminho_do_pdf: str) -> dict:
    """Ferramenta LENTA: Extrai texto de PDFs escaneados usando OCR."""
    try:
        if not os.path.exists(caminho_do_pdf):
            return {"erro": f"Arquivo não encontrado: {caminho_do_pdf}"}
        texto_completo = ""
        with fitz.open(caminho_do_pdf) as doc:
            for page_num, page in enumerate(doc):
                print(f"Processando OCR na página {page_num + 1}...")
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                texto_ocr = pytesseract.image_to_string(img, lang='por')
                texto_completo += texto_ocr + "\n\n"
        if not texto_completo.strip(): return {"erro": "O OCR não conseguiu extrair nenhum texto do PDF."}
        return {"texto_completo": texto_completo}
    except Exception as e: return {"erro": f"Falha ao processar o PDF com OCR: {e}"}

@tool
def converter_cmyk_para_hex(cmyk_string: str) -> str:
    """Converte uma string de cor CMYK para um código hexadecimal."""
    try:
        numeros = [int(n) for n in re.findall(r'\d+', cmyk_string)]
        if len(numeros) != 4: return f"Formato CMYK inválido: {cmyk_string}"
        c, m, y, k = [n / 100.0 for n in numeros]
        r = 255 * (1 - c) * (1 - k); g = 255 * (1 - m) * (1 - k); b = 255 * (1 - y) * (1 - k)
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
    except Exception as e: return f"Erro ao converter CMYK: {e}"

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# --- INSTRUÇÕES ESPECIALIZADAS ---

# <<< INSTRUÇÃO Nº 1: Para PDFs de TEXTO (Rígida e precisa) >>>
INSTRUCAO_PARA_PDF_TEXTO = """Você é um robô processador de texto. Sua função é extrair informações de forma literal e precisa, focando apenas nas seções de paleta de cores.

**FLUXO DE TRABALHO OBRIGATÓRIO:**
1.  **Extraia o Texto:** Use a ferramenta `analisar_pdf_texto`.
2.  **Análise de Cores Contextual:**
    - **Foque:** Encontre as seções que definem a paleta oficial (ex: "Cores Primárias", "Primary", "Secondary").
    - **Ignore:** Ignore ativamente qualquer cor fora dessas seções.
    - **Processe:** Dentro da paleta, para cada cor:
        - Se encontrar um código Hexadecimal ('#') completo, use-o.
        - Se encontrar um código CMYK, use a ferramenta `converter_cmyk_para_hex`.
3.  **Análise de Outras Informações:** Procure por "Nome da Marca", "URLs", "Tom de Voz" e "Fontes".
4.  **Relatório Final:** Monte um relatório único e coeso com as informações encontradas.
"""

# <<< INSTRUÇÃO Nº 2: Para PDFs de IMAGEM (Flexível e com Plano B) >>>
INSTRUCAO_PARA_PDF_IMAGEM = """Você é um analista especialista em interpretar textos extraídos de imagens (OCR), que podem conter erros. Sua função é usar seu raciocínio para extrair informações de forma inteligente, mesmo com dados imperfeitos. VOCÊ ESTÁ PROIBIDO DE INVENTAR informações que não possam ser razoavelmente deduzidas do texto.

**FLUXO DE TRABALHO OBRIGATÓRIO E INTERPRETATIVO:**

**1. EXTRAÇÃO DE TEXTO OCR:**
   - Use a ferramenta `analisar_pdf_imagem_ocr` para obter o `texto_completo`, sabendo que ele pode conter erros.

**2. ANÁLISE INTERPRETATIVA DE CORES COM VALIDAÇÃO:**
   - Para cada cor que você identificar na paleta:
     - **TENTATIVA 1 (Hexadecimal):**
       - Tente encontrar um código hexadecimal no texto OCR.
       - **Validação:** Após encontrar um código, verifique se ele está completo (um '#' seguido por 6 caracteres). Se estiver, use-o e considere a cor resolvida.
       - **Se o código estiver incompleto ou corrompido (ex: '#FFF' ou '#1234F'), NÃO TENTE ADIVINHAR.** Abandone esta tentativa e vá para o "Plano B".
     - **PLANO B (CMYK como fonte da verdade):**
       - Encontre a string CMYK associada à cor. Como os números são mais fáceis para o OCR, este método é mais confiável.
       - Use a ferramenta `converter_cmyk_para_hex` com a string CMYK que você extraiu para obter o valor hexadecimal final.
     
**3. ANÁLISE DE OUTRAS INFORMAÇÕES:**
   - Continue analisando o texto OCR para encontrar: "Nome da Marca", "Descrição da Marca", "URLs Importantes", "Tom de Voz" e "Fontes".

**4. GERAÇÃO DO RELATÓRIO FINAL:**
   - Apresente um relatório final único e limpo. Se algo não for encontrado, indique "Não encontrado".
"""

# --- PARTE PRINCIPAL: FUNÇÃO DE EXECUÇÃO ---
def analisar_guia_de_marca():
    print("Bem-vindo ao Analisador de Guia de Marcas!")
    
    while True:
        caminho_pdf = input("Por favor, insira o caminho para o arquivo PDF (ou 'sair' para terminar): ").strip()
        if caminho_pdf.lower() == 'sair':
            break

        if not os.path.exists(caminho_pdf):
            print(f"Erro: O arquivo não foi encontrado no caminho '{caminho_pdf}'.")
            continue

        tipo_pdf = ""
        while tipo_pdf not in ["texto", "imagem"]:
            tipo_pdf = input("Qual o tipo do PDF? Digite 'texto' ou 'imagem': ").lower().strip()

        print("\n>>> Criando agentes com memória limpa e instruções especializadas...")
        
        # <<< LÓGICA DE ESPECIALIZAÇÃO >>>
        # Seleciona a instrução e as ferramentas corretas com base no tipo de PDF.
        if tipo_pdf == 'texto':
            instrucao_do_agente = INSTRUCAO_PARA_PDF_TEXTO
            ferramentas_do_agente = [analisar_pdf_texto, converter_cmyk_para_hex]
        else: # tipo_pdf == 'imagem'
            instrucao_do_agente = INSTRUCAO_PARA_PDF_IMAGEM
            ferramentas_do_agente = [analisar_pdf_imagem_ocr, converter_cmyk_para_hex]

        prompt_agente = ChatPromptTemplate.from_messages([
            ("system", instrucao_do_agente),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agente_runnable = create_tool_calling_agent(llm, ferramentas_do_agente, prompt_agente)
        agente_executor = AgentExecutor(agent=agente_runnable, tools=ferramentas_do_agente, verbose=True)
        
        print(f"\nAnalisando o documento '{caminho_pdf}'...")
        input_para_agente = {"input": f"Analise o seguinte arquivo PDF: {caminho_pdf}"}
        resultado = agente_executor.invoke(input_para_agente)
        
        print("\n--- Relatório Final da Análise ---")
        print(resultado['output'])
        print("---------------------------------\n")

if __name__ == "__main__":
    analisar_guia_de_marca()