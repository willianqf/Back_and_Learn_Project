# 1. Escolher a imagem base do Python
FROM python:3.10-slim

# 2. Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# 3. Atualizar o sistema e instalar as dependências do sistema (Tesseract OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar o arquivo de dependências do Python e instalá-las
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar todo o resto do código do seu projeto para o contêiner
COPY . .

# 6. Expor a porta que o Flask vai usar
EXPOSE 8080

# 7. Definir o comando para iniciar a aplicação com Gunicorn e um timeout maior
# Aumentamos o timeout para 120 segundos para dar tempo de processar os lotes.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "app:app"]
