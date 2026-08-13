import pytest
from pathlib import Path
import pypdf

from app.loaders.factory import LoaderFactory
from app.loaders.txt_loader import TextLoader
from app.loaders.pdf_loader import PDFLoader
from app.loaders.image_loader import ImageLoader
from app.loaders.docx_loader import DOCXLoader
from app.core.errors import UnsupportedFormatError, InvalidFileError


def test_loader_factory_retrieval():
    loader_txt = LoaderFactory.get_loader("txt")
    assert isinstance(loader_txt, TextLoader)

    loader_pdf = LoaderFactory.get_loader(".pdf")
    assert isinstance(loader_pdf, PDFLoader)

    loader_img = LoaderFactory.get_loader("png")
    assert isinstance(loader_img, ImageLoader)

    loader_docx = LoaderFactory.get_loader_for_file("sample.docx")
    assert isinstance(loader_docx, DOCXLoader)

    with pytest.raises(UnsupportedFormatError):
        LoaderFactory.get_loader("unsupported_extension_xyz")


def test_text_loader(tmp_path):
    file_path = tmp_path / "sample.txt"
    sample_text = "Multimodal RAG with Context Engineering."
    file_path.write_text(sample_text, encoding="utf-8")

    loader = TextLoader()
    doc = loader.load(file_path, metadata={"author": "Unit Test"})

    assert doc.source_type == "txt"
    assert doc.source_name == "sample.txt"
    assert doc.content == sample_text
    assert doc.metadata["author"] == "Unit Test"


def test_pdf_loader(tmp_path):
    pdf_path = tmp_path / "sample.pdf"

    # Create a minimal valid PDF using pypdf Writer
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with pdf_path.open("wb") as f:
        writer.write(f)

    loader = PDFLoader()
    doc = loader.load(pdf_path)

    assert doc.source_type == "pdf"
    assert doc.source_name == "sample.pdf"
    assert doc.metadata["num_pages"] == 1


def test_text_loader_missing_file():
    loader = TextLoader()
    with pytest.raises(InvalidFileError):
        loader.load("non_existent_file.txt")
