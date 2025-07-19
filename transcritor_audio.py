import whisper
import os
from pydub import AudioSegment

# Carrega o modelo Whisper. 'base' é recomendado agora que o servidor está estável.
try:
    print("🧠 Carregando o modelo Whisper (modelo: base)...")
    model = whisper.load_model("base")
    print("✅ Modelo Whisper carregado com sucesso.")
except Exception as e:
    print(f"❌ Erro crítico ao carregar o modelo Whisper: {e}")
    model = None

def transcrever_audio_para_texto(caminho_do_audio):
    """
    Recebe o caminho de um ficheiro de áudio, converte para o formato ideal
    e retorna o texto transcrito usando Whisper.
    """
    if not model:
        return "[Erro: O modelo de transcrição não pôde ser carregado no servidor.]"

    caminho_audio_convertido = ""
    try:
        # --- ETAPA DE OTIMIZAÇÃO ---
        print(f"🔊 Otimizando o áudio: {caminho_do_audio}")
        # Carrega o áudio original
        audio = AudioSegment.from_file(caminho_do_audio)
        # Converte para mono e define a taxa de amostragem para 16kHz
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        # Cria um novo nome de arquivo para o áudio otimizado
        caminho_audio_convertido = caminho_do_audio.replace('.m4a', '_optimized.wav')
        
        # Exporta o áudio otimizado em formato WAV
        audio.export(caminho_audio_convertido, format="wav")
        print(f"✅ Áudio otimizado salvo em: {caminho_audio_convertido}")
        # --- FIM DA OTIMIZAÇÃO ---

        print(f"🎤 A iniciar transcrição com Whisper para: {caminho_audio_convertido}")
        
        # Passa o arquivo OTIMIZADO para o Whisper
        result = model.transcribe(caminho_audio_convertido, language="pt", fp16=False)
        
        texto_final = result.get("text", "").strip()

        if texto_final:
            print(f"✅ Transcrição concluída: '{texto_final}'")
        else:
            print("⚠️ A transcrição não produziu texto.")
            texto_final = "[Não foi possível detetar fala no áudio.]"
        
        return texto_final

    except Exception as e:
        print(f"❌ Erro durante a transcrição com Whisper: {e}")
        return f"[Erro no processo de transcrição: {e}]"
    finally:
        # Remove ambos os arquivos de áudio (original e otimizado)
        if os.path.exists(caminho_do_audio):
            os.remove(caminho_do_audio)
        if caminho_audio_convertido and os.path.exists(caminho_audio_convertido):
            os.remove(caminho_audio_convertido)
        print("🗑️ Ficheiros de áudio temporários removidos.")