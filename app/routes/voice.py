"""Shunya OS — Voice processing endpoint + Bird integration."""
from flask import Blueprint, request, jsonify, send_file, g
from app.routes.auth import login_required
import io

voice_bp = Blueprint("voice", __name__, url_prefix="/voice")


@voice_bp.route("/process", methods=["POST"])
@login_required
def process_voice():
    """Process voice input: audio → STT → Bird → TTS response."""
    from app.shunya.voice import VoicePipeline
    from app.shunya.bird import Bird

    # Get audio file
    audio_file = request.files.get("audio")
    audio_data = audio_file.read() if audio_file else request.get_data()
    language = request.form.get("language") or request.args.get("language")

    if not audio_data:
        return jsonify({"error": "No audio data received"}), 400

    # Transcribe
    result = VoicePipeline.process_voice_input(
        audio_data,
        filename=audio_file.filename if audio_file else "audio.webm",
        language=language,
        tenant_id=g.tenant.id,
        user_id=g.user.id,
    )

    if result.get("error"):
        return jsonify(result), 400

    # Process through Bird
    text = result["text"]
    detected_lang = result.get("language", "en")

    bird = Bird(g.tenant.id, g.user.id, g.user.role, g.user.name)
    bird_response = bird.handle_query(text)

    # Generate audio response
    response_text = f"I heard: {text}. Let me check on that for you."
    audio_bytes, mime = VoicePipeline.speak_response(response_text, detected_lang)

    return jsonify({
        "text": text,
        "language": detected_lang,
        "confidence": result.get("transcription_confidence", 0),
        "response": response_text,
        "bird_context": bird_response,
        "audio_available": len(audio_bytes) > 0,
    })


@voice_bp.route("/speak", methods=["POST"])
@login_required
def speak():
    """Generate TTS audio from text."""
    from app.shunya.voice import VoicePipeline

    data = request.get_json(silent=True) or request.form
    text = data.get("text", "")
    language = data.get("language", "en")
    voice = data.get("voice", "alloy")

    if not text:
        return jsonify({"error": "Text required"}), 400

    audio_bytes, mime = VoicePipeline.speak_response(text, language, voice)

    if not audio_bytes:
        return jsonify({"error": "TTS generation failed"}), 500

    return send_file(
        io.BytesIO(audio_bytes),
        mimetype=mime,
        as_attachment=False,
        download_name="response.mp3",
    )


@voice_bp.route("/languages", methods=["GET"])
def list_languages():
    """List supported languages."""
    from app.shunya.voice import SUPPORTED_LANGUAGES
    return jsonify({"languages": SUPPORTED_LANGUAGES, "count": len(SUPPORTED_LANGUAGES)})