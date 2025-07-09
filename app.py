# /Back-and/app.py

import os
import time
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
import processador_pdf

# Carrega a chave da API a partir das variáveis de ambiente
OCR_API_KEY = os.getenv('OCR_SPACE_API_KEY')

# --- Constantes e Inicialização ---
FILE_LIFETIME_SECONDS = 3600
UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/iniciar_processamento', methods=['POST'])
def iniciar_processamento():
    # Este endpoint continua igual
    try:
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'erro': 'Nome de arquivo inválido'}), 400

        extensao = os.path.splitext(file.filename)[1]
        id_arquivo = f"{uuid.uuid4()}{extensao}"
        caminho_pdf_salvo = os.path.join(app.config['UPLOAD_FOLDER'], id_arquivo)
        file.save(caminho_pdf_salvo)

        total_paginas = processador_pdf.contar_paginas_pdf(caminho_pdf_salvo)

        if total_paginas == 0:
            os.remove(caminho_pdf_salvo)
            return jsonify({'erro': 'Não foi possível ler as páginas do PDF.'}), 400

        print(f"Arquivo recebido: {id_arquivo}, Total de páginas: {total_paginas}")

        return jsonify({
            'status': 'iniciado',
            'id_arquivo': id_arquivo,
            'total_paginas': total_paginas,
            'nome_original': file.filename
        }), 200
    except Exception as e:
        print(f"Erro em /iniciar_processamento: {e}")
        return jsonify({'erro': 'Erro interno ao iniciar o processamento.'}), 500
@app.route('/obter_texto_pagina', methods=['POST'])
def obter_texto_pagina():
    if not OCR_API_KEY:
        return jsonify({'erro': 'Chave da API de OCR não configurada no servidor.'}), 500

    try:
        data = request.get_json()
        id_arquivo = data.get('id_arquivo')
        numero_pagina = data.get('numero_pagina')

        if not all([id_arquivo, numero_pagina]):
            return jsonify({'erro': 'Parâmetros ausentes'}), 400

        caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], id_arquivo)
        if not os.path.exists(caminho_pdf):
            return jsonify({'erro': 'Arquivo não encontrado no servidor'}), 404
        
        # --- MUDANÇA PRINCIPAL AQUI ---
        # O try/except agora está focado na função que pode falhar.
        texto_extraido = processador_pdf.extrair_texto_pagina_com_api(
            caminho_pdf,
            numero_pagina,
            OCR_API_KEY
        )
        
        return jsonify({'status': 'sucesso', 'texto': texto_extraido})

    except Exception as e:
        # Se a função do processador levantar uma exceção, nós a capturamos
        # e retornamos um erro 500 (Erro Interno do Servidor) para o frontend.
        print(f"Erro final no endpoint /obter_texto_pagina: {e}")
        return jsonify({'erro': str(e)}), 500

# A lógica de limpeza continua igual
def cleanup_old_files():
    print("Executando a tarefa de limpeza...")
    # ... (código da limpeza sem alterações)

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=cleanup_old_files, trigger="interval", minutes=30)
scheduler.start()
import atexit
atexit.register(lambda: scheduler.shutdown())