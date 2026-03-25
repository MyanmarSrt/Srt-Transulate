import os
import srt
import datetime
import google.generativeai as genai


# -----------------------------
# 1. Parse SRT content
# -----------------------------
def parse_srt(srt_content):
    """
    Convert SRT string into a list of subtitle objects
    """
    try:
        subtitles = list(srt.parse(srt_content))
        return subtitles
    except Exception as e:
        raise ValueError(f"Failed to parse SRT: {e}")


# -----------------------------
# 2. Chunk subtitles
# -----------------------------
def chunk_subtitles(subtitles, chunk_size=30):
    """
    Break subtitles into chunks to avoid token limits
    """
    for i in range(0, len(subtitles), chunk_size):
        yield subtitles[i:i + chunk_size]


# -----------------------------
# Helper: Format chunk text
# -----------------------------
def format_chunk_for_translation(chunk):
    """
    Convert subtitle chunk into numbered plain text
    """
    lines = []
    for i, sub in enumerate(chunk, start=1):
        clean_text = sub.content.replace("\n", " ")
        lines.append(f"{i}. {clean_text}")
    return "\n".join(lines)


# -----------------------------
# Helper: Apply translated text
# -----------------------------
def apply_translation_to_chunk(chunk, translated_text):
    """
    Map translated lines back to subtitle objects
    """
    translated_lines = translated_text.strip().split("\n")

    for i, sub in enumerate(chunk):
        if i < len(translated_lines):
            # Remove numbering if model returns it
            line = translated_lines[i]
            if "." in line:
                line = line.split(".", 1)[-1].strip()
            sub.content = line.strip()

    return chunk


# -----------------------------
# 3. Main translation function
# -----------------------------
def translate_srt_file(srt_content, model_name="gemini-1.5-flash"):
    """
    Translate SRT content into Burmese using Gemini
    """

    # Load API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    genai.configure(api_key=api_key)

    # Initialize model
    model = genai.GenerativeModel(model_name)

    # Parse subtitles
    subtitles = parse_srt(srt_content)

    translated_subtitles = []

    # Process in chunks
    for chunk in chunk_subtitles(subtitles):
        input_text = format_chunk_for_translation(chunk)

        prompt = f"""
You are a professional subtitle translator.

Translate the following subtitles into **natural, fluent Burmese**.

IMPORTANT RULES:
- Keep the SAME number of lines
- DO NOT merge or split lines
- DO NOT add extra explanation
- DO NOT change meaning
- Keep tone natural (like movie subtitles)
- Return ONLY translated lines in order

Subtitles:
{input_text}
"""

        try:
            response = model.generate_content(prompt)
            translated_text = response.text.strip()

            # Apply translation back
            updated_chunk = apply_translation_to_chunk(chunk, translated_text)
            translated_subtitles.extend(updated_chunk)

        except Exception as e:
            raise RuntimeError(f"Translation failed: {e}")

    # Rebuild SRT content
    final_srt = srt.compose(translated_subtitles)

    return final_srt
