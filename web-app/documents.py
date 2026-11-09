"""Extract selectable text from a local PDF or modern PowerPoint deck."""
from pathlib import Path
from zipfile import ZipFile

from pptx import Presentation
from pypdf import PdfReader


class DocumentLimitError(ValueError):
    pass


def extract_text(upload):
    if not upload or not upload.filename:
        return ""
    extension = Path(upload.filename).suffix.lower()
    if extension not in {".pdf", ".pptx"}:
        raise ValueError("Choose a PDF or PPTX file.")
    try:
        if extension == ".pptx":
            with ZipFile(upload.stream) as archive:
                members = archive.infolist()
                if len(members) > 2_000 or sum(m.file_size for m in members) > 32_000_000:
                    raise DocumentLimitError("The expanded presentation is too large.")
            upload.stream.seek(0)
            presentation = Presentation(upload.stream)
            sections = []
            for number, slide in enumerate(presentation.slides, 1):
                texts = [shape.text for shape in slide.shapes if hasattr(shape, "text") and shape.text.strip()]
                if texts:
                    sections.append(f"Slide {number}\n" + "\n".join(texts))
        else:
            reader = PdfReader(upload.stream)
            if reader.is_encrypted or len(reader.pages) > 100:
                raise DocumentLimitError("Choose an unencrypted PDF with at most 100 pages.")
            sections = [(page.extract_text() or "") for page in reader.pages]
        result = "\n".join(sections).strip()
    except DocumentLimitError:
        raise
    except Exception as exc:
        raise ValueError("The document could not be read.") from exc
    if not result:
        raise ValueError("The document contains no extractable text.")
    if len(result) > 60_000:
        raise ValueError("Choose a shorter document (60,000 characters maximum).")
    return result
