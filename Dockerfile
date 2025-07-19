# 1. Escolher a imagem base do Python
FROM python:3.10-slim

# 2. Definir o diretório de trabalho
WORKDIR /app

# 3. NOVO: Atualizar e instalar ffmpeg, que é uma dependência do Whisper
RUN apt-get update && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar as dependências Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- INÍCIO DA MODIFICAÇÃO ---
# 5. Copiar APENAS o script de download e baixá-lo.
# Isso otimiza o cache do Docker. O modelo só será baixado novamente
# se o requirements.txt ou o download_model.py mudarem.
COPY download_model.py .
RUN python download_model.py
# --- FIM DA MODIFICAÇÃO ---

# 6. Copiar o resto do código da aplicação
COPY . .

# 7. Expor a porta
EXPOSE 8080

# 8. Comando para iniciar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "app:app"]