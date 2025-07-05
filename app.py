# app.py

import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import processador_pdf # Importamos nosso script adaptado

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configurações
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = os.path.join('static', 'audios')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Define o endpoint da API para processar o PDF
@app.route('/processar', methods=['POST'])
def processar_arquivo():
    # 1. Verifica se um arquivo foi enviado na requisição
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']

    # 2. Verifica se o nome do arquivo não está vazio
    if file.filename == '':
        return jsonify({'erro': 'Nome de arquivo inválido'}), 400

    if file:
        # 3. Salva o arquivo PDF de forma segura na pasta 'uploads'
        filename = secure_filename(file.filename)
        caminho_pdf_salvo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(caminho_pdf_salvo)
        print(f"Arquivo recebido e salvo em: {caminho_pdf_salvo}")

        # 4. Chama nosso processador para fazer o trabalho pesado
        caminhos_relativos_audio = processador_pdf.processar_pdf_para_audio(
            caminho_pdf_salvo, 
            app.config['AUDIO_FOLDER']
        )

        # 5. Constrói as URLs completas para os áudios gerados
        base_url = request.host_url
        urls_completas = []
        for caminho_relativo in caminhos_relativos_audio:
            # Converte o caminho do arquivo (ex: static\audios\meu_pdf\pagina_1.mp3)
            # para uma URL válida (ex: http://127.0.0.1:5000/static/audios/meu_pdf/pagina_1.mp3)
            url = base_url + caminho_relativo.replace('\\', '/')
            urls_completas.append(url)

        # 6. Retorna uma resposta JSON com as URLs dos áudios
        return jsonify({
            'status': 'sucesso',
            'paginas_processadas': len(urls_completas),
            'audio_urls': urls_completas
        })

    return jsonify({'erro': 'Ocorreu um erro inesperado'}), 500

# Roda o servidor Flask
if __name__ == '__main__':
    # O host '0.0.0.0' torna o servidor acessível na sua rede local
    # (importante para testar com o celular depois)
    app.run(host='0.0.0.0', port=5000, debug=True)