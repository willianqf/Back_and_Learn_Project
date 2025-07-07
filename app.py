# app.py (Versão de Produção)

import os
import time
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from whitenoise import WhiteNoise
import processador_pdf

# --- Constantes de Configuração ---
FILE_LIFETIME_SECONDS = 900 # 15 minutos
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
AUDIO_FOLDER = os.path.join(STATIC_FOLDER, 'audios')

# --- Inicialização ---
app = Flask(__name__, static_folder=STATIC_FOLDER)
CORS(app)
app.wsgi_app = WhiteNoise(app.wsgi_app, root=STATIC_FOLDER, prefix='/static/')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)


# --- Endpoint 1: Iniciar o Processamento ---
@app.route('/iniciar_processamento', methods=['POST'])
def iniciar_processamento():
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


# --- Endpoint 2: Obter Lote de Áudio ---
@app.route('/obter_audio_lote', methods=['POST'])
def obter_audio_lote():
    try:
        data = request.get_json()
        id_arquivo = data.get('id_arquivo')
        pagina_inicio = data.get('pagina_inicio')
        pagina_fim = data.get('pagina_fim')

        if not all([id_arquivo, pagina_inicio, pagina_fim]):
            return jsonify({'erro': 'Parâmetros ausentes'}), 400

        caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], id_arquivo)
        if not os.path.exists(caminho_pdf):
            return jsonify({'erro': 'Arquivo não encontrado no servidor'}), 404

        print(f"Processando lote para {id_arquivo} (páginas {pagina_inicio}-{pagina_fim})")

        caminhos_relativos = processador_pdf.extrair_texto_e_gerar_audio_lote(
            caminho_pdf,
            app.config['AUDIO_FOLDER'],
            pagina_inicio,
            pagina_fim
        )

        base_url = request.host_url.replace('http://', 'https://') if 'fly.dev' in request.host_url else request.host_url
        
        urls_completas = []
        for caminho_relativo_audio in caminhos_relativos:
            caminho_url = f"static/{caminho_relativo_audio}".replace('\\', '/')
            url = base_url + caminho_url
            urls_completas.append(url)
        
        print(f"URLs Geradas: {urls_completas}")

        return jsonify({'status': 'sucesso', 'audio_urls': urls_completas})

    except Exception as e:
        print(f"Erro em /obter_audio_lote: {e}")
        return jsonify({'erro': 'Erro interno ao processar o lote.'}), 500


# --- Lógica de Limpeza e Agendador ---
def cleanup_old_files():
    print("Executando a tarefa de limpeza de arquivos antigos...")
    now = time.time()
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            try:
                if os.stat(file_path).st_mtime < (now - FILE_LIFETIME_SECONDS):
                    os.remove(file_path)
                    print(f"Arquivo de upload removido: {file_path}")
            except Exception as e:
                print(f"Erro ao tentar remover o arquivo de upload {file_path}: {e}")
    for root, dirs, files in os.walk(app.config['AUDIO_FOLDER']):
        for name in files:
            try:
                file_path = os.path.join(root, name)
                if os.stat(file_path).st_mtime < (now - FILE_LIFETIME_SECONDS):
                    os.remove(file_path)
                    print(f"Arquivo de áudio removido: {file_path}")
            except Exception as e:
                print(f"Erro ao tentar remover o arquivo de áudio {os.path.join(root, name)}: {e}")

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=cleanup_old_files, trigger="interval", minutes=15)
scheduler.start()
import atexit
atexit.register(lambda: scheduler.shutdown())
