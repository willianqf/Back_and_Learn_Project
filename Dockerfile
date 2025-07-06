# 1. Escolher a imagem base do Python
FROM python:3.10-slim

# 2. Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# 3. Atualizar o sistema e instalar as dependências do sistema (Tesseract OCR)
# Esta é a parte mais importante para o seu projeto!
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

# 6. Expor a porta que o Flask vai usar (geralmente 8080 em produção)
EXPOSE 8080

# 7. Definir o comando para iniciar a aplicação com Gunicorn
# Isso vai procurar por uma variável 'app' no arquivo 'app.py'
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]