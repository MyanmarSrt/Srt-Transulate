import srt
import google.generativeai as genai
import os
import time

def parse_srt(srt_content):
    """Parses SRT content into a list of Subtitle objects."""
    try:
        return list(srt.parse(srt_content))
    except Exception as e:
        print(f"Error parsing SRT: {e}")
        return []

def chunk_subtitles(subtitles, chunk_size=50):
    """Chunks a list of Subtitle objects into smaller lists."""
    chunks = []
    for i in range(0, len(subtitles), chunk_size):
        chunks.append(subtitles[i : i + chunk_size])
    return chunks

def translate_srt_file(srt_content, model_name='gemini-1.5-flash'):
    """Translates the entire SRT content and returns as an SRT string."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    subtitles = parse_srt(srt_content)
    if not subtitles:
        return "Error: Could not parse SRT content."

    translated_subtitles = []
    system_prompt = (
        "You are an expert translator. Translate the following subtitle text into natural, fluent Burmese (Myanmar). "
        "Strictly maintain the original meaning. Do not add any extra explanations or notes."
    )

    for sub in subtitles:
        try:
            if not sub.content.strip():
                translated_subtitles.append(sub)
                continue
                
            response = model.generate_content(f"{system_prompt}\n\nContent:\n{sub.content}")
            sub.content = response.text.strip()
            translated_subtitles.append(sub)
            time.sleep(0.5) # Rate limit မမိအောင် ခဏစောင့်ပေးခြင်း
        except Exception:
            translated_subtitles.append(sub) # Error ဖြစ်ရင် မူရင်းအတိုင်း ထားခဲ့မယ်

    return srt.compose(translated_subtitles)
