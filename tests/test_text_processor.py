from src.core.text_processor import TextProcessor

def test_clean_text_removes_null_and_extra_spaces():
    t = TextProcessor.__new__(TextProcessor)
    assert t.clean_text(' A   B\x00\n\n C ') == 'A B\nC'


def test_every_chunk_preserves_page_url():
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    processor = TextProcessor()
    processor.splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=10)
    url = 'https://egspec.org/academics'
    document = Document(page_content=f'URL: {url}\n' + 'Official engineering course details. ' * 30,
                        metadata={'source': 'academics.txt'})
    chunks = processor.split_documents([document])
    assert len(chunks) > 1
    assert all(chunk.metadata['source_url'] == url for chunk in chunks)
