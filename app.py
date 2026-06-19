import streamlit as st

from mcq_agent.config import AppConfig, ConfigError
from mcq_agent.document_ai import (
    DocumentExtractionError,
    count_pdf_pages,
    detect_mime_type,
    extract_text_with_document_ai,
    validate_upload_size,
)
from mcq_agent.formatting import format_questions_for_display
from mcq_agent.generator import GenerationError, generate_questions


st.set_page_config(page_title="Grounded MCQ Generator", page_icon="?", layout="centered")
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Grounded MCQ Generator")
st.write("Upload a PDF or Word .docx file, choose a question count, and generate cited multiple-choice questions.")

try:
    config = AppConfig.from_env()
    config_error = None
except ConfigError as exc:
    config = None
    config_error = str(exc)

if config_error:
    st.error(config_error)

if config:
    missing = config.missing_settings()
    if missing:
        st.warning("Missing required settings: " + ", ".join(missing))

    st.info(
        f"Limits: upload a PDF or Word .docx file up to {config.max_upload_mb} MB "
        f"and {config.max_pages} pages; generate up to {config.max_questions} questions."
    )

    # with st.expander("Cost controls", expanded=False):
        # st.write(f"Maximum upload size: {config.max_upload_mb} MB")
        # st.write(f"Maximum PDF pages: {config.max_pages}")
        # st.write(f"Maximum questions per run: {config.max_questions}")
        # st.write("Document AI charges per page and Gemini charges by tokens, so smaller files and fewer questions cost less.")

    uploaded_file = st.file_uploader(
        f"Upload source file (PDF/DOCX, max {config.max_upload_mb} MB, max {config.max_pages} pages)",
        type=["pdf", "docx"],
    )
    question_count = st.number_input(
        f"Number of questions (max {config.max_questions})",
        min_value=1,
        max_value=config.max_questions,
        value=min(5, config.max_questions),
        step=1,
    )

    if st.button("Generate questions", type="primary"):
        if missing:
            st.error("Set the missing environment variables before generating questions.")
        elif uploaded_file is None:
            st.error("Upload a PDF or Word .docx file first.")
        else:
            try:
                file_bytes = uploaded_file.getvalue()
                validate_upload_size(file_bytes, config.max_upload_mb)
                mime_type = detect_mime_type(uploaded_file.name)

                if mime_type == "application/pdf":
                    page_count = count_pdf_pages(file_bytes)
                    if page_count is not None and page_count > config.max_pages:
                        raise DocumentExtractionError(
                            f"PDF has {page_count} pages, above the {config.max_pages} page limit."
                        )

                with st.status("Extracting text with Document AI...", expanded=True) as status:
                    pages = extract_text_with_document_ai(
                        file_bytes=file_bytes,
                        mime_type=mime_type,
                        project_id=config.project_id or "",
                        location=config.document_ai_location,
                        processor_id=config.document_ai_processor_id or "",
                        max_pages=config.max_pages,
                    )
                    status.update(label=f"Extracted text from {len(pages)} page(s).", state="complete")

                with st.status("Generating grounded questions with Gemini...", expanded=True) as status:
                    questions = generate_questions(
                        source_pages=pages,
                        question_count=int(question_count),
                        project_id=config.project_id or "",
                        location=config.vertex_ai_location,
                        model=config.gemini_model,
                        max_source_chars=config.max_source_chars,
                    )
                    status.update(label="Generated and validated questions.", state="complete")

                output = format_questions_for_display(questions)
                st.session_state["generated_output"] = output
            except (DocumentExtractionError, GenerationError) as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Generation failed: {exc}")

if "generated_output" in st.session_state:
    st.subheader("Generated questions")
    st.text_area("Questions and answers", value=st.session_state["generated_output"], height=600)
    st.download_button(
        "Download text file",
        data=st.session_state["generated_output"],
        file_name="generated_mcqs.txt",
        mime="text/plain",
    )
