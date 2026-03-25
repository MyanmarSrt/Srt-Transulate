import os
import srt
import google.generativeai as genai


# -----------------------------
# 1. Parse SRT
# -----------------------------
def parse_srt(srt_content):
    try:
        return list(srt.parse(srt_content))
    except Exception as e:
        raise ValueError(f"SRT parse error: {e}")


# -----------------------------
# 2. Chunk subtitles
# -----------------------------
def chunk_subtitles(subtitles, chunk_size=20):
    for i in range(0, len(subtitles), chunk_size):
        yield subtitles[i:i + chunk_size]


# -----------------------------
# Format chunk
# -----------------------------
def format_chunk(chunk):
    lines = []
    for i, sub in enumerate(chunk, 1):
        text = sub.content.replace("\n", " ")
        lines.append(f"{i}|{text}")
    return "\n".join(lines)


# -----------------------------
# Safe Gemini response extractor
# -----------------------------
def get_response_text(response):
    try:
        # New SDK
        if hasattr(response, "text") and response.text:
            return response.text.strip()

        # Fallback
        return response.candidates[0].content.parts[0].text.strip()
    except Exception:
        return ""


# -----------------------------
# Apply translation safely
# -----------------------------
def apply_translation(chunk, translated_text):
    lines = translated_text.split("\n")

    result = []
    for i, sub in enumerate(chunk):
        if i < len(lines):
            line = lines[i]

            # remove prefix like "1|" if exists
            if "|" in line:
                line = line.split("|", 1)[1]

            sub.content = line.strip()

        result.append(sub)

    return result


# -----------------------------
# 3. Main function
# -----------------------------
def translate_srt_file(srt_content, model_name="gemini-1.5-flash"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    subtitles = parse_srt(srt_content)
    final_subtitles = []

    for chunk in chunk_subtitles(subtitles):
        formatted = format_chunk(chunk)

        prompt = f"""
Translate into natural Burmese.

STRICT RULES:
- Keep EXACT same number of lines
- Keep same order
- Do NOT skip or merge
- Output format: number|translation

Example:
1|မင်္ဂလာပါ
2|ဘယ်လိုရှိလဲ

Now translate:

{formatted}
"""

        try:
            response = model.generate_content(prompt)
            translated_text = get_response_text(response)

            if not translated_text:
                raise ValueError("Empty response from Gemini")

            updated_chunk = apply_translation(chunk, translated_text)
            final_subtitles.extend(updated_chunk)

        except Exception as e:
            print("Chunk failed, using original:", e)
            final_subtitles.extend(chunk)  # fallback

    return srt.compose(final_subtitles)
