# /Back-and/processador_pdf.py

import os
import fitz
import requests
import time

def contar_paginas_pdf(caminho_do_pdf):
    try:
        with fitz.open(caminho_do_pdf) as doc:
            return doc.page_count
    except Exception as e:
        print(f"Erro ao contar páginas do PDF: {e}")
        return 0

def extrair_texto_pagina_com_api(caminho_do_pdf, numero_pagina, api_key):
    """
    Extrai uma página, envia para a API de OCR com tentativas.
    Se todas as tentativas falharem, levanta uma exceção para cancelar o processo.
    """
    try:
        documento = fitz.open(caminho_do_pdf)
        if numero_pagina < 1 or numero_pagina > documento.page_count:
            documento.close()
            raise ValueError(f"Número de página inválido: {numero_pagina}")

        pagina = documento.load_page(numero_pagina - 1)
        pix = pagina.get_pixmap(dpi=100)
        bytes_imagem = pix.tobytes("png")
        documento.close()

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
                    print(f"Erro na API de OCR: {resultado.get('ErrorMessage')}")
                    # Consideramos erro da API como uma falha que merece nova tentativa
                    raise requests.exceptions.RequestException("Erro retornado pela API de OCR.")

                texto_extraido = resultado['ParsedResults'][0]['ParsedText']
                print(f"Texto da página {numero_pagina} recebido com sucesso.")
                return texto_extraido.strip()

            except requests.exceptions.RequestException as e:
                print(f"Tentativa {tentativa + 1} falhou: {e}")
                if tentativa < max_tentativas - 1:
                    time.sleep(2 * (tentativa + 1))
                else:
                    # --- MUDANÇA PRINCIPAL ---
                    # Se todas as tentativas falharem, levanta uma exceção.
                    raise Exception(f"Falha ao processar a página {numero_pagina} após {max_tentativas} tentativas.")

    except Exception as e:
        # Repassa a exceção para que o endpoint do Flask possa tratá-la.
        print(f"❌ Erro crítico ao processar a página {numero_pagina}: {e}")
        raise e