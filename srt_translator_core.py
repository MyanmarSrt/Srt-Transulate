import srt
import google.generativeai as genai
import os
import time

def parse_srt(srt_content):
    """Parses SRT content into a list of Subtitle objects."""
    return list(srt.parse(srt_content))

def chunk_subtitles(subtitles, chunk_size=50):
    """Chunks a list of Subtitle objects into smaller lists."""
    chunks = []
    for i in range(0, len(subtitles), chunk_size):
        chunks.append(subtitles[i : i + chunk_size])
    return chunks

def translate_srt_file(srt_content, model_name='gemini-1.5-flash'):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    try:
        subtitles = parse_srt(srt_content)
    except Exception as e:
        return f"Error parsing SRT: {str(e)}"

    translated_subtitles = []
    system_prompt = (
        "You are an expert translator. Translate the following SRT subtitle text into natural, fluent Burmese (Myanmar). "
        "Strictly maintain the original SRT format, timestamps, and numbering. Do not add any extra explanations."
    )

    for sub in subtitles:
        try:
            if not sub.content.strip():
                translated_subtitles.append(sub)
                continue
            response = model.generate_content(f"{system_prompt}\n\nContent to translate:\n{sub.content}")
            sub.content = response.text.strip()
            translated_subtitles.append(sub)
            time.sleep(0.3) 
        except Exception:
            translated_subtitles.append(sub)

    return srt.compose(translated_subtitles)
