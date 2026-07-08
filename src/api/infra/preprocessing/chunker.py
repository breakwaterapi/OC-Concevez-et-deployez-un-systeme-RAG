from dataclasses import dataclass, field
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
import mistral_common
from mistral_common.tokens.tokenizers.tekken import Tekkenizer


def _load_tekkenizer() -> Tekkenizer:
    data_dir = Path(mistral_common.__file__).parent / "data"
    tokenizer_files = sorted(data_dir.glob("tekken_*.json"), reverse=True)
    return Tekkenizer.from_file(str(tokenizer_files[0]))


@dataclass
class TextChunker:
    chunk_max_tokens: int = 256
    chunk_overlap_tokens: int = 20
    _tokenizer: Tekkenizer = field(init=False, repr=False)
    _splitter: RecursiveCharacterTextSplitter = field(init=False, repr=False)

    def __post_init__(self):
        self._tokenizer = _load_tekkenizer()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_max_tokens,
            chunk_overlap=self.chunk_overlap_tokens,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=self.count_tokens,
        )

    def count_tokens(self, text: str) -> int:
        return len(self._tokenizer.encode(text, bos=False, eos=False))

    def split_text(self, text: str, reserved_tokens: int = 0) -> list[str]:
        if not text or not text.strip():
            return []
        if reserved_tokens <= 0:
            return self._splitter.split_text(text)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_max_tokens,
            chunk_overlap=self.chunk_overlap_tokens,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=lambda t: self.count_tokens(t) + reserved_tokens,
        )
        return splitter.split_text(text)
