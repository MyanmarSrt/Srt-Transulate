
import srt
from google import genai
import os

def parse_srt(srt_content: str) -> list[srt.Subtitle]:
    """Parses SRT content into a list of Subtitle objects."""
    return list(srt.parse(srt_content))

def chunk_subtitles(subtitles: list[srt.Subtitle], chunk_size: int = 50) -> list[list[srt.Subtitle]]:
    """Chunks a list of Subtitle objects into smaller lists."""
    chunks = []
    for i in range(0, len(subtitles), chunk_size):
        chunks.append(subtitles[i:i + chunk_size])
    return chunks

def format_timedelta(td):
    """Formats a timedelta object into SRT timestamp format (HH:MM:SS,mmm)."""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def generate_translation_prompt(subtitle_chunk: list[srt.Subtitle]) -> tuple[str, str]:
    """
    Generates the system prompt and user prompt for Gemini translation.
    """
    system_prompt = (
        "You are a highly skilled translation AI. Your task is to translate the provided SRT subtitle "
        "chunk into natural, fluent Burmese Unicode. You MUST strictly preserve the original SRT "
        "formatting, including subtitle numbers, timestamps (e.g., 00:01:20,000 --> 00:01:25,000), "
        "and line breaks. Only translate the text content of each subtitle. Do not add any extra "
        "text or commentary. Maintain the original numbering sequence and timestamps exactly as they are."
    )

    user_prompt_parts = []
    for sub in subtitle_chunk:
        start_str = format_timedelta(sub.start)
        end_str = format_timedelta(sub.end)
        user_prompt_parts.append(f"{sub.index}\n{start_str} --> {end_str}\n{sub.content}")
    
    user_prompt = "\n\n".join(user_prompt_parts)
    return system_prompt, user_prompt

def translate_chunk(subtitle_chunk: list[srt.Subtitle], model_name: str = "gemini-1.5-flash") -> str:
    """Translates a single chunk of subtitles using the Gemini API."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    
    client = genai.Client(api_key=api_key)
    system_prompt, user_prompt = generate_translation_prompt(subtitle_chunk)
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=f"{system_prompt}\n\n{user_prompt}"
        )
        return response.text
    except Exception as e:
        print(f"Error translating chunk: {e}")
        # In case of an error, return the original content to avoid data loss
        return srt.compose(subtitle_chunk)

def translate_srt_file(srt_content: str, chunk_size: int = 50, model_name: str = "gemini-1.5-flash") -> str:
    """Translates an entire SRT file by chunking and using the Gemini API."""
    subtitles = parse_srt(srt_content)
    chunks = chunk_subtitles(subtitles, chunk_size)
    
    translated_chunks_text = []
    for i, chunk in enumerate(chunks):
        translated_text = translate_chunk(chunk, model_name)
        translated_chunks_text.append(translated_text)
        
    full_translated_srt_content = "\n\n".join(translated_chunks_text)
    
    try:
        re_parsed_subtitles = list(srt.parse(full_translated_srt_content))
        return srt.compose(re_parsed_subtitles)
    except Exception as e:
        print(f"Warning: Could not re-parse translated SRT content. Returning raw translated text. Error: {e}")
        return full_translated_srt_content
