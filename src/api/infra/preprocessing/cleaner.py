from dataclasses import dataclass, field

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter


@dataclass
class DoclingCleaner:
    _converter: DocumentConverter = field(
        init=False, default_factory=DocumentConverter, repr=False
    )

    def html_to_text(self, html: str | None) -> str:
        if not isinstance(html, str) or html.strip() == "":
            return ""
        result = self._converter.convert_string(html, format=InputFormat.HTML)
        return result.document.export_to_markdown().strip()
