from app.services.chunking_service import chunk_pages


def test_chunking_respects_pages():
    pages = [(1, "Paragraph one. Sentence two.\n\nParagraph three."), (2, "Page two content.")]
    chunks = chunk_pages(pages, chunk_size=1000, overlap=0)
    assert len(chunks) >= 1
    assert any(c.page == 1 for c in chunks)
    assert any(c.page == 2 for c in chunks)


def test_chunking_splits_large_paragraph():
    long_para = " ".join([f"Sentence number {i} about testing." for i in range(200)])
    chunks = chunk_pages([(1, long_para)], chunk_size=50, overlap=5)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) > 0


def test_empty_page_produces_no_chunks():
    chunks = chunk_pages([(1, "")])
    assert chunks == []
