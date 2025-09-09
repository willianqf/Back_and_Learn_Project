# /Back-and/processador_pdf.py

import os
import fitz  # PyMuPDF
import requests
import time
from langdetect import detect, LangDetectException # NOVO: Importa o detector de idioma

def contar_paginas_pdf(caminho_do_pdf):
    try:
        with fitz.open(caminho_do_pdf) as doc:
            return doc.page_count
    except Exception as e:
        print(f"Erro ao contar páginas do PDF: {e}")
        return 0

def extrair_texto_pagina_com_ocr(caminho_do_pdf, numero_pagina, api_key):
    doc = None
    try:
        doc = fitz.open(caminho_do_pdf)
        if numero_pagina < 1 or numero_pagina > doc.page_count:
            raise ValueError(f"Número de página inválido: {numero_pagina}")

        pagina = doc.load_page(numero_pagina - 1)
        pix = pagina.get_pixmap(dpi=96) 
        bytes_imagem = pix.tobytes("png")
        
    except Exception as e:
        print(f"❌ Erro ao ler o PDF na página {numero_pagina}: {e}")
        raise e
    finally:
        if doc:
            doc.close()

    payload = {'apikey': api_key, 'language': 'por', 'isOverlayRequired': False}
    files = {'file': ('image.png', bytes_imagem, 'image/png')}
    
    max_tentativas = 3
    for tentativa in range(max_tentativas):
        try:
            print(f"Enviando página {numero_pagina} para a API de OCR (Tentativa {tentativa + 1})...")
            response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload, timeout=60)
            response.raise_for_status()
            
            resultado = response.json()
            if resultado.get('IsErroredOnProcessing'):
                raise requests.exceptions.RequestException(f"Erro da API de OCR: {resultado.get('ErrorMessage')}")

            texto_extraido = resultado['ParsedResults'][0]['ParsedText']
            print(f"Texto da página {numero_pagina} recebido da API com sucesso.")
            
            # NOVO: Adiciona a detecção de idioma também para o OCR
            idioma_detectado = 'desconhecido'
            try:
                if texto_extraido and len(texto_extraido.strip()) > 50:
                    idioma_detectado = detect(texto_extraido)
            except LangDetectException:
                print("Não foi possível detectar o idioma do texto do OCR.")

            return {
                "texto_completo": texto_extraido.strip(),
                "palavras": [],
                "dimensoes": {"largura": 0, "altura": 0},
                "extraido_por_ocr": True,
                "idioma": idioma_detectado # Retorna o idioma
            }

        except requests.exceptions.RequestException as e:
            print(f"Tentativa de OCR {tentativa + 1} falhou: {e}")
            if tentativa < max_tentativas - 1:
                time.sleep(2 * (tentativa + 1))
            else:
                raise Exception(f"Falha ao processar a página {numero_pagina} com OCR.")

def extrair_dados_completos_pagina(caminho_do_pdf, numero_pagina, api_key):
    """
    Função principal atualizada para detectar o idioma.
    """
    try:
        doc = fitz.open(caminho_do_pdf)
        if numero_pagina < 1 or numero_pagina > doc.page_count:
            raise ValueError(f"Número de página inválido: {numero_pagina}")

        page = doc.load_page(numero_pagina - 1)
        
        lista_palavras = page.get_text("words")
        
        if lista_palavras and len(lista_palavras) > 5:
            print(f"Extraindo dados da página {numero_pagina} diretamente do PDF.")
            
            palavras_com_coords = [
                {"texto": p[4], "coords": {"x0": p[0], "y0": p[1], "x1": p[2], "y1": p[3]}}
                for p in lista_palavras
            ]

            texto_completo = page.get_text("text")
            dimensoes = {"largura": page.rect.width, "altura": page.rect.height}
            
            # NOVO: Bloco para detectar o idioma
            idioma_detectado = 'desconhecido'
            try:
                # Tenta detectar apenas se houver uma quantidade razoável de texto
                if texto_completo and len(texto_completo.strip()) > 50:
                    idioma_detectado = detect(texto_completo)
                    print(f"Idioma detectado na página {numero_pagina}: {idioma_detectado}")
            except LangDetectException:
                print(f"Não foi possível detectar o idioma na página {numero_pagina}.")

            doc.close()
            return {
                "texto_completo": texto_completo.strip(),
                "palavras": palavras_com_coords,
                "dimensoes": dimensoes,
                "extraido_por_ocr": False,
                "idioma": idioma_detectado # Adiciona o idioma à resposta
            }
        else:
            print(f"Página {numero_pagina} não contém texto direto. Usando OCR.")
            doc.close()
            return extrair_texto_pagina_com_ocr(caminho_do_pdf, numero_pagina, api_key)

    except Exception as e:
        print(f"❌ Erro crítico ao processar a página {numero_pagina}: {e}")
        raise e