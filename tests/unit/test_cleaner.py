import pytest

from api.infra.preprocessing.cleaner import DoclingCleaner


@pytest.fixture(scope="module")
def cleaner() -> DoclingCleaner:
    # DoclingCleaner() takes ~5s to initialize (DocumentConverter model loading) — one instance
    # shared across this whole module keeps the suite fast.
    return DoclingCleaner()


def test_html_to_text_paragraph_with_bold(cleaner):
    result = cleaner.html_to_text("<p>Bonjour <b>le monde</b></p>")

    assert result == "Bonjour **le monde**"


def test_html_to_text_list(cleaner):
    result = cleaner.html_to_text("<ul><li>item 1</li><li>item 2</li></ul>")

    assert result == "- item 1\n- item 2"


def test_html_to_text_none_returns_empty_string(cleaner):
    assert cleaner.html_to_text(None) == ""


def test_html_to_text_empty_string_returns_empty_string(cleaner):
    assert cleaner.html_to_text("") == ""


def test_html_to_text_whitespace_only_returns_empty_string(cleaner):
    assert cleaner.html_to_text("   \n\t  ") == ""


def test_html_to_text_strips_surrounding_whitespace(cleaner):
    result = cleaner.html_to_text("  <p>Texte avec espaces autour</p>  \n")

    assert result == "Texte avec espaces autour"
    assert result == result.strip()
