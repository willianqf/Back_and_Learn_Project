# download_model.py
import whisper

print("Iniciando o download do modelo 'base' durante o build...")
# A função load_model vai baixar o modelo para o cache padrão se não o encontrar
whisper.load_model("base")
print("Download do modelo concluído.")