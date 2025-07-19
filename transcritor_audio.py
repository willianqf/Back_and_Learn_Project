import os
from pydub import AudioSegment
import whisper

# --- INÍCIO DA CORREÇÃO ---
# 1. Não carregamos o modelo aqui. A variável 'model' começa como None.
model = None

def carregar_modelo():
    """
    Função para carregar o modelo Whisper. Garante que ele seja carregado apenas uma vez.
    """
    global model
    if model is None:
        try:
            print("🧠 Carregando o modelo Whisper (modelo: base) pela primeira vez...")
            # Usamos 'base' pois o servidor agora iniciará rápido.
            model = whisper.load_model("tiny")
            print("✅ Modelo Whisper carregado com sucesso.")
        except Exception as e:
            print(f"❌ Erro crítico ao carregar o modelo Whisper: {e}")
            # Se falhar, definimos como um objeto de erro para não tentar de novo.
            model = {"error": str(e)}
    return model
# --- FIM DA CORREÇÃO ---


def transcrever_audio_para_texto(caminho_do_audio):
    """
    Recebe o caminho de um ficheiro de áudio, converte para o formato ideal
    e retorna o texto transcrito usando Whisper.
    """
    # 2. Chamamos a função para garantir que o modelo esteja carregado.
    loaded_model = carregar_modelo()

    # Verifica se o modelo foi carregado com sucesso
    if isinstance(loaded_model, dict) and "error" in loaded_model:
        return f"[Erro: O modelo de transcrição não pôde ser carregado no servidor: {loaded_model['error']}]"
    if not loaded_model:
        return "[Erro: O modelo de transcrição não pôde ser carregado no servidor.]"

    caminho_audio_convertido = ""
    try:
        # --- ETAPA DE OTIMIZAÇÃO (sem alterações) ---
        print(f"🔊 Otimizando o áudio: {caminho_do_audio}")
        audio = AudioSegment.from_file(caminho_do_audio)
        audio = audio.set_channels(1).set_frame_rate(16000)
        caminho_audio_convertido = caminho_do_audio.replace('.m4a', '_optimized.wav')
        audio.export(caminho_audio_convertido, format="wav")
        print(f"✅ Áudio otimizado salvo em: {caminho_audio_convertido}")
        # --- FIM DA OTIMIZAÇÃO ---

        print(f"🎤 A iniciar transcrição com Whisper para: {caminho_audio_convertido}")
        
        # 3. Usamos a variável do modelo carregado
        result = loaded_model.transcribe(caminho_audio_convertido, language="pt", fp16=False)
        
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
        if os.path.exists(caminho_do_audio):
            os.remove(caminho_do_audio)
        if caminho_audio_convertido and os.path.exists(caminho_audio_convertido):
            os.remove(caminho_audio_convertido)
        print("🗑️ Ficheiros de áudio temporários removidos.")