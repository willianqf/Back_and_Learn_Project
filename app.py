# app.py (Versão de Depuração)

import os
import time
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from whitenoise import WhiteNoise
import processador_pdf

# --- Constantes ---
FILE_LIFETIME_SECONDS = 1800
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
AUDIO_FOLDER = os.path.join(STATIC_FOLDER, 'audios')

# --- Inicialização ---
app = Flask(__name__, static_folder=STATIC_FOLDER)
# Configuração do WhiteNoise (mantemos a última versão)
app.wsgi_app = WhiteNoise(app.wsgi_app, root=STATIC_FOLDER, prefix='/static/')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# --- Lógica de Limpeza (sem alterações) ---
def cleanup_old_files():
    print("Executando a tarefa de limpeza de arquivos antigos...")
    now = time.time()
    # ... (código de limpeza omitido para brevidade, mantenha o seu)
    # Limpa a pasta de uploads (PDFs)
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            try:
                if os.stat(file_path).st_mtime < (now - FILE_LIFETIME_SECONDS):
                    os.remove(file_path)
                    print(f"Arquivo de upload removido: {file_path}")
            except Exception as e:
                print(f"Erro ao tentar remover o arquivo de upload {file_path}: {e}")

    # Limpa a pasta de áudios (MP3s)
    for root, dirs, files in os.walk(app.config['AUDIO_FOLDER']):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                if os.stat(file_path).st_mtime < (now - FILE_LIFETIME_SECONDS):
                    os.remove(file_path)
                    print(f"Arquivo de áudio removido: {file_path}")
            except Exception as e:
                print(f"Erro ao tentar remover o arquivo de áudio {file_path}: {e}")


# --- Agendador (sem alterações) ---
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=cleanup_old_files, trigger="interval", minutes=10)
scheduler.start()

# --- Endpoint Principal ---
@app.route('/processar', methods=['POST'])
def processar_arquivo():
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({'erro': 'Nome de arquivo inválido'}), 400

    if file:
        filename = secure_filename(file.filename)
        caminho_pdf_salvo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(caminho_pdf_salvo)
        print(f"Arquivo PDF salvo em: {caminho_pdf_salvo}")

        caminhos_relativos_audio = processador_pdf.processar_pdf_para_audio(
            caminho_pdf_salvo, 
            app.config['AUDIO_FOLDER']
        )
        
        # --- LOG DE DEPURACAO 1 ---
        print(f"Caminhos relativos recebidos do processador: {caminhos_relativos_audio}")

        base_url = request.host_url
        urls_completas = []
        for caminho_relativo in caminhos_relativos_audio:
            url = base_url + caminho_relativo.replace('\\', '/')
            urls_completas.append(url)

        # --- LOG DE DEPURACAO 2 ---
        print(f"URLs completas que serão enviadas para o app: {urls_completas}")

        return jsonify({
            'status': 'sucesso',
            'paginas_processadas': len(urls_completas),
            'audio_urls': urls_completas
        })

    return jsonify({'erro': 'Ocorreu um erro inesperado'}), 500

# --- NOVAS ROTAS DE DEPURACAO ---
@app.route('/')
def health_check():
    """Rota simples para verificar se o app está rodando."""
    return "Servidor HearLearn está no ar!"

@app.route('/debug-files')
def list_files():
    """Rota para listar os arquivos nas pastas e ajudar a depurar."""
    try:
        uploads_list = os.listdir(UPLOAD_FOLDER)
    except Exception as e:
        uploads_list = [f"Erro ao listar uploads: {e}"]

    try:
        audio_files = []
        for root, dirs, files in os.walk(AUDIO_FOLDER):
            for name in files:
                audio_files.append(os.path.join(root, name))
    except Exception as e:
        audio_files = [f"Erro ao listar áudios: {e}"]
        
    return jsonify({
        "uploads": uploads_list,
        "audios": audio_files
    })


import atexit
atexit.register(lambda: scheduler.shutdown())