"""Extract text page by page from uploaded PDF / TXT files."""
import io
import re
from pypdf import PdfReader
from pypdf.errors import PyPdfError


class IngestionError(ValueError):
    pass


# PDF bullets (Wingdings/Symbol fonts) are extracted as private-use characters that browsers show as empty boxes.
_PRIVATE_USE = re.compile(r"[\ue000-\uf8ff]")


def clean_text(text: str) -> str:
    return _PRIVATE_USE.sub("\u2022", text)


def extract_pages(filename: str, data: bytes) -> list[str]:
    """Return a list of page texts (a .txt file counts as one page)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "txt":
        return [clean_text(data.decode("utf-8", errors="ignore"))]
    if ext == "pdf":
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise IngestionError("Encrypted PDFs are not supported.")
            return [clean_text(page.extract_text() or "") for page in reader.pages]
        except PyPdfError as exc:
            raise IngestionError(f"Could not read PDF: {exc}") from exc
    raise IngestionError("Only .pdf and .txt files are supported.")