
import streamlit as st
import os
import srt
from srt_translator_core import parse_srt, chunk_subtitles, translate_chunk, translate_srt_file

# Set page config
st.set_page_config(page_title="Long-Form SRT Translator", layout="wide")

st.title("Long-Form SRT Translator (Burmese)")
st.markdown("Translate long SRT files into natural, fluent Burmese using Google Gemini 1.5 Flash.")

# API Key Input
api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
else:
    st.sidebar.warning("Please enter your Gemini API Key to proceed.")

# File Uploader
uploaded_file = st.file_uploader("Upload your SRT file", type=["srt"])

if uploaded_file is not None and api_key:
    srt_content = uploaded_file.getvalue().decode("utf-8")
    st.write("File uploaded successfully!")

    # Display original SRT (optional)
    with st.expander("View Original SRT"):
        st.text_area("Original SRT Content", srt_content, height=300)

    if st.button("Start Translation"):
        if not os.environ.get("GEMINI_API_KEY"):
            st.error("Gemini API Key is not set. Please enter it in the sidebar.")
        else:
            st.info("Translation in progress... This may take a while for long files.")
            
            # Initialize progress bar
            progress_text = "Operation in progress. Please wait."
            my_bar = st.progress(0, text=progress_text)

            subtitles = parse_srt(srt_content)
            chunks = chunk_subtitles(subtitles, chunk_size=50) # Using default chunk size
            
            translated_chunks_text = []
            total_chunks = len(chunks)

            for i, chunk in enumerate(chunks):
                my_bar.progress((i + 1) / total_chunks, text=f"Translating chunk {i+1} of {total_chunks}...")
                try:
                    translated_text = translate_chunk(chunk, model_name="gemini-1.5-flash")
                    translated_chunks_text.append(translated_text)
                except Exception as e:
                    st.error(f"Error translating chunk {i+1}: {e}. Skipping this chunk.")
                    # Fallback: if translation fails, append original chunk content
                    translated_chunks_text.append(srt.compose(chunk))
            
            my_bar.progress(1.0, text="Translation complete!")
            st.success("Translation finished!")

            full_translated_srt_content = "\n\n".join(translated_chunks_text)
            
            # Attempt to re-parse the translated content to ensure it's valid SRT
            try:
                re_parsed_subtitles = list(srt.parse(full_translated_srt_content))
                final_translated_srt = srt.compose(re_parsed_subtitles)
            except Exception as e:
                st.warning(f"Could not re-parse translated SRT content. Returning raw translated text. Error: {e}")
                final_translated_srt = full_translated_srt_content

            st.subheader("Translated SRT")
            st.text_area("Translated Content", final_translated_srt, height=400)

            st.download_button(
                label="Download Translated SRT",
                data=final_translated_srt.encode("utf-8"),
                file_name="translated_burmese.srt",
                mime="text/plain"
            )
else:
    if not api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to enable file upload and translation.")
    else:
        st.info("Upload an SRT file to begin translation.")
