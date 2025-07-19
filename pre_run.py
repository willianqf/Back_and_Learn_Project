# pre_run.py
import transcritor_audio

# Esta linha executa a função que carrega o modelo, 
# exatamente como no seu endpoint /health.
print("Iniciando o pré-carregamento do modelo Whisper...")
transcritor_audio.carregar_modelo()
print("✅ Modelo pré-carregado e pronto para uso.")