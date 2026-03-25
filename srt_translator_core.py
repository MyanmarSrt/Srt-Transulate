import srt
import google.generativeai as genai
import os
import time

def translate_srt_file(srt_content, model_name='gemini-1.5-flash'):
    # API Key ကို Streamlit Secrets ကနေ ဆွဲယူခြင်း
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    try:
        subtitles = list(srt.parse(srt_content))
    except Exception as e:
        return f"Error parsing SRT: {str(e)}"

    translated_subtitles = []
    
    # Prompt ကို မြန်မာလို သေချာဖြစ်အောင် ပြင်ထားပါတယ်
    system_prompt = (
        "You are an expert translator. Translate the following SRT subtitle text into natural, fluent Burmese (Myanmar). "
        "Strictly maintain the original SRT format, timestamps, and numbering. Do not add any extra explanations."
    )

    for sub in subtitles:
        try:
            response = model.generate_content(f"{system_prompt}\n\nContent to translate:\n{sub.content}")
            sub.content = response.text.strip()
            translated_subtitles.append(sub)
            time.sleep(0.5) # API limit မမိအောင် ခဏစောင့်ခြင်း
        except Exception:
            translated_subtitles.append(sub) # Error တက်ရင် မူရင်းအတိုင်း ထားခဲ့မယ်

    return srt.compose(translated_subtitles)
