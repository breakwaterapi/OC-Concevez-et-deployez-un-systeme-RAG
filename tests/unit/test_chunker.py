import pytest

from api.infra.preprocessing.chunker import TextChunker


@pytest.fixture(scope="module")
def chunker():
    return TextChunker(chunk_max_tokens=20, chunk_overlap_tokens=2)


def test_count_tokens_non_empty(chunker):
    assert chunker.count_tokens("Bonjour le monde !") > 0


def test_count_tokens_empty(chunker):
    assert chunker.count_tokens("") == 0


def test_split_text_short(chunker):
    chunks = chunker.split_text("Court texte.")

    assert len(chunks) == 1
    assert "Court texte" in chunks[0]


def test_split_text_empty_string(chunker):
    assert chunker.split_text("") == []


def test_split_text_whitespace_only(chunker):
    assert chunker.split_text("   ") == []


def test_split_text_long_text_produces_multiple_chunks(chunker):
    long_text = " ".join(["événement culturel fascinant"] * 20)

    chunks = chunker.split_text(long_text)

    assert len(chunks) > 1


def test_split_text_chunks_respect_max_tokens(chunker):
    long_text = " ".join(["mot"] * 200)

    for chunk in chunker.split_text(long_text):
        assert chunker.count_tokens(chunk) <= chunker.chunk_max_tokens * 1.5


def test_split_text_reserved_tokens_shrinks_fragments(chunker):
    long_text = " ".join(["mot"] * 200)
    reserved = 10

    for fragment in chunker.split_text(long_text, reserved_tokens=reserved):
        assert chunker.count_tokens(fragment) + reserved <= chunker.chunk_max_tokens * 1.5


def test_split_text_reserved_tokens_zero_matches_default(chunker):
    long_text = " ".join(["mot"] * 200)

    assert chunker.split_text(long_text, reserved_tokens=0) == chunker.split_text(long_text)