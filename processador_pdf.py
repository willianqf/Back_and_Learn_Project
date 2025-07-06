# processador_pdf.py (Versão Final Corrigida)

import os
import fitz  # PyMuPDF
from gtts import gTTS
from PIL import Image
import pytesseract
import io

# --- CONFIGURAÇÃO DO TESSERACT ---
# 1. REMOVEMOS AS LINHAS COM O CAMINHO DO WINDOWS.
# O pytesseract encontrará o Tesseract automaticamente no servidor Linux,
# pois ele foi instalado pelo nosso Dockerfile.
#
# LINHAS REMOVIDAS:
# os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_texto_de_pdf_imagem(caminho_do_pdf):
    textos_extraidos = []
    try:
        documento = fitz.open(caminho_do_pdf)
        total_paginas = documento.page_count
        if total_paginas == 0:
            print("❌ ERRO: O arquivo PDF parece não ter páginas.")
            return None
            
        print(f"📖 PDF tem {total_paginas} páginas (detectado por PyMuPDF).")

        for i in range(total_paginas):
            numero_pagina = i + 1
            print(f"   📄 Processando página {numero_pagina}/{total_paginas}...")
            
            pagina = documento.load_page(i)
            # Aumentar o DPI pode melhorar a qualidade do OCR
            pix = pagina.get_pixmap(dpi=300) 
            bytes_imagem = pix.tobytes("png")
            imagem_pil = Image.open(io.BytesIO(bytes_imagem))
            
            try:
                # Agora o pytesseract usará o Tesseract instalado no sistema
                texto = pytesseract.image_to_string(imagem_pil, lang='por')
                
                if texto.strip():
                    print(f"      ✅ OCR da página {numero_pagina} bem-sucedido.")
                else:
                    print(f"      ⚠️ OCR da página {numero_pagina} não encontrou texto legível.")
                textos_extraidos.append(texto)
            except Exception as e_ocr:
                print(f"      ❌ Erro durante o OCR na página {numero_pagina}: {e_ocr}")
                textos_extraidos.append("")

        documento.close()
        
    except Exception as e:
        print(f"❌ Erro crítico ao abrir ou processar o PDF com PyMuPDF: {e}")
        return None
        
    print("--- Extração de texto concluída ---")
    return textos_extraidos


def gerar_audios_de_lista(lista_de_textos, nome_base_arquivo, diretorio_saida):
    caminhos_audio = []
    if not lista_de_textos: return caminhos_audio

    pasta_audio_pdf = os.path.join(diretorio_saida, nome_base_arquivo)
    os.makedirs(pasta_audio_pdf, exist_ok=True)

    for i, texto_da_pagina in enumerate(lista_de_textos):
        numero_pagina = i + 1
        caminho_arquivo_audio = os.path.join(pasta_audio_pdf, f"pagina_{numero_pagina}.mp3")
        if texto_da_pagina and texto_da_pagina.strip():
            try:
                tts = gTTS(text=texto_da_pagina, lang='pt-br')
                tts.save(caminho_arquivo_audio)
                caminhos_audio.append(caminho_arquivo_audio)
            except Exception as e:
                print(f"Erro ao gerar áudio para a página {numero_pagina}: {e}")
    return caminhos_audio


def processar_pdf_para_audio(caminho_do_pdf, diretorio_saida_audio):
    print(f"Iniciando processamento para API: {caminho_do_pdf}")
    nome_base_arquivo = os.path.splitext(os.path.basename(caminho_do_pdf))[0]
    textos_das_paginas = extrair_texto_de_pdf_imagem(caminho_do_pdf)
    if textos_das_paginas is not None:
        caminhos_dos_audios = gerar_audios_de_lista(textos_das_paginas, nome_base_arquivo, diretorio_saida_audio)
        print(f"Processamento para API concluído. {len(caminhos_dos_audios)} áudios gerados.")
        return caminhos_dos_audios
    else:
        return []