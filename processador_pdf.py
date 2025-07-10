# /Back-and/processador_pdf.py

import os
import fitz  # PyMuPDF
import requests
import time

def contar_paginas_pdf(caminho_do_pdf):
    try:
        with fitz.open(caminho_do_pdf) as doc:
            return doc.page_count
    except Exception as e:
        print(f"Erro ao contar páginas do PDF: {e}")
        return 0

def extrair_texto_pagina_com_ocr(caminho_do_pdf, numero_pagina, api_key):
    """
    Extrai uma página, converte em imagem e envia para a API de OCR.
    A resolução (DPI) foi ajustada para reduzir o tamanho do ficheiro.
    """
    doc = None
    try:
        doc = fitz.open(caminho_do_pdf)
        if numero_pagina < 1 or numero_pagina > doc.page_count:
            raise ValueError(f"Número de página inválido: {numero_pagina}")

        pagina = doc.load_page(numero_pagina - 1)
        # --- CORREÇÃO PRINCIPAL AQUI ---
        # Reduzimos o DPI para diminuir o tamanho da imagem final.
        pix = pagina.get_pixmap(dpi=96) 
        bytes_imagem = pix.tobytes("png")
        
    except Exception as e:
        print(f"❌ Erro ao ler o PDF na página {numero_pagina}: {e}")
        raise e
    finally:
        if doc:
            doc.close()

    payload = {'apikey': api_key, 'language': 'por'}
    files = {'file': ('image.png', bytes_imagem, 'image/png')}
    
    max_tentativas = 3
    for tentativa in range(max_tentativas):
        try:
            print(f"Enviando página {numero_pagina} para a API de OCR (Tentativa {tentativa + 1})...")
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files=files,
                data=payload,
                timeout=60
            )
            response.raise_for_status()
            
            resultado = response.json()
            
            if resultado.get('IsErroredOnProcessing'):
                raise requests.exceptions.RequestException(f"Erro da API de OCR: {resultado.get('ErrorMessage')}")

            texto_extraido = resultado['ParsedResults'][0]['ParsedText']
            print(f"Texto da página {numero_pagina} recebido da API com sucesso.")
            return texto_extraido.strip()

        except requests.exceptions.RequestException as e:
            print(f"Tentativa de OCR {tentativa + 1} falhou: {e}")
            if tentativa < max_tentativas - 1:
                time.sleep(2 * (tentativa + 1))
            else:
                raise Exception(f"Falha ao processar a página {numero_pagina} com OCR após {max_tentativas} tentativas.")


def extrair_texto_pagina(caminho_do_pdf, numero_pagina, api_key):
    """
    Tenta extrair texto diretamente. Se falhar, usa o OCR como fallback.
    """
    texto_direto = ""
    try:
        with fitz.open(caminho_do_pdf) as doc:
            if numero_pagina < 1 or numero_pagina > doc.page_count:
                raise ValueError(f"Número de página inválido: {numero_pagina}")

            pagina = doc.load_page(numero_pagina - 1)
            texto_direto = pagina.get_text("text")
            
        if texto_direto and len(texto_direto.strip()) > 50:
            print(f"Texto da página {numero_pagina} extraído diretamente do PDF.")
            return texto_direto.strip()
        else:
            print(f"Página {numero_pagina} não contém texto direto ou é muito curto. Usando OCR.")
            return extrair_texto_pagina_com_ocr(caminho_do_pdf, numero_pagina, api_key)

    except Exception as e:
        print(f"❌ Erro crítico ao processar a página {numero_pagina}: {e}")
        raise e