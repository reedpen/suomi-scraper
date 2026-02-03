import os
import io
import logging
from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

class DocumentLoader:
    def load_file(self, file_obj, filename: str) -> str:
        """
        Loads text from a file object (or path).
        Args:
            file_obj: A file path (str) or a file-like object (bytes).
            filename: The name of the file (used for extension detection).
        Returns:
            str: The extracted text.
        """
        ext = os.path.splitext(filename)[1].lower()
        
        try:
            if ext == '.pdf':
                return self._extract_pdf(file_obj)
            elif ext == '.docx':
                return self._extract_docx(file_obj)
            elif ext == '.txt':
                return self._extract_txt(file_obj)
            else:
                logger.warning(f"Unsupported file extension: {ext}")
                return ""
        except Exception as e:
            logger.error(f"Error loading file {filename}: {e}")
            return ""

    def _extract_pdf(self, file_obj) -> str:
        text = []
        try:
            reader = PdfReader(file_obj)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise e
        return "\n".join(text)

    def _extract_docx(self, file_obj) -> str:
        text = []
        try:
            doc = Document(file_obj)
            for para in doc.paragraphs:
                text.append(para.text)
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            raise e
        return "\n".join(text)

    def _extract_txt(self, file_obj) -> str:
        # Handle both path string and file-like object
        if isinstance(file_obj, str):
            with open(file_obj, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Assume bytes IO, decode
            if isinstance(file_obj, io.BytesIO):
                 return file_obj.getvalue().decode('utf-8')
            return str(file_obj.read())

if __name__ == "__main__":
    # Test stub
    pass
