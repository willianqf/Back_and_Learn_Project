# processador_pdf.py (Versão de Produção)

import os
import fitz  # PyMuPDF
from gtts import gTTS
from PIL import Image
import pytesseract
import io
import time

# --- CONFIGURAÇÃO DO TESSERACT ---
# Removemos a linha específica do Windows. O servidor da nuvem (Linux)
# encontrará o Tesseract automaticamente, pois ele foi instalado pelo Dockerfile.
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def contar_paginas_pdf(caminho_do_pdf):
    """Função simples para contar o total de páginas de um PDF."""
    try:
        with fitz.open(caminho_do_pdf) as doc:
            return doc.page_count
    except Exception as e:
        print(f"Erro ao contar páginas do PDF: {e}")
        return 0

def extrair_texto_e_gerar_audio_lote(caminho_do_pdf, diretorio_saida_audio, pagina_inicio, pagina_fim):
    """
    Processa um intervalo específico de páginas de um PDF,
    extrai o texto e gera os arquivos de áudio.
    """
    caminhos_audio = []
    nome_base_arquivo = os.path.splitext(os.path.basename(caminho_do_pdf))[0]
    
    try:
        documento = fitz.open(caminho_do_pdf)
        total_paginas_doc = documento.page_count

        pagina_inicio_idx = max(0, pagina_inicio - 1)
        pagina_fim_idx = min(total_paginas_doc, pagina_fim)

        pasta_audio_pdf = os.path.join(diretorio_saida_audio, nome_base_arquivo)
        os.makedirs(pasta_audio_pdf, exist_ok=True)

        for i in range(pagina_inicio_idx, pagina_fim_idx):
            numero_pagina_atual = i + 1
            print(f"   📄 Processando página {numero_pagina_atual}...")
            
            pagina = documento.load_page(i)
            
            pix = pagina.get_pixmap(dpi=200)
            bytes_imagem = pix.tobytes("png")
            imagem_pil = Image.open(io.BytesIO(bytes_imagem))
            
            config_tesseract = r'--oem 3 --psm 6'
            
            texto = pytesseract.image_to_string(imagem_pil, lang='por', config=config_tesseract)
            
            caminho_arquivo_audio = os.path.join(pasta_audio_pdf, f"pagina_{numero_pagina_atual}.mp3")
            if texto and texto.strip():
                # --- LÓGICA DE "RETRY" ---
                tentativas = 0
                max_tentativas = 3
                sucesso = False
                while tentativas < max_tentativas and not sucesso:
                    try:
                        tts = gTTS(text=texto, lang='pt-br')
                        tts.save(caminho_arquivo_audio)
                        caminhos_audio.append(os.path.join('audios', nome_base_arquivo, f"pagina_{numero_pagina_atual}.mp3"))
                        sucesso = True # Se chegou aqui, funcionou!
                    except Exception as e_tts:
                        tentativas += 1
                        print(f"      ❌ Erro no gTTS (tentativa {tentativas}/{max_tentativas}): {e_tts}")
                        if "429" in str(e_tts) and tentativas < max_tentativas:
                            # Se o erro for de "Too Many Requests", espera mais tempo antes de tentar de novo.
                            tempo_espera = 10 * tentativas 
                            print(f"      🕒 Bloqueado pela API. A aguardar {tempo_espera} segundos...")
                            time.sleep(tempo_espera)
                        else:
                            # Para outros erros, apenas espera um pouco.
                            time.sleep(2)
            else:
                print(f"      ⚠️ OCR da página {numero_pagina_atual} não encontrou texto.")

            # Pausa normal entre o processamento de cada página
            time.sleep(1)

        documento.close()
        
    except Exception as e:
        print(f"❌ Erro crítico ao processar o lote do PDF: {e}")
        return []
        
    print(f"--- Lote de páginas {pagina_inicio}-{pagina_fim} processado. {len(caminhos_audio)} áudios gerados. ---")
    return caminhos_audio