# tools/ingest.py — document ingestion pipeline
from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from loguru import logger

from config import CHUNK_SIZE, CHUNK_OVERLAP


LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".docx": Docx2txtLoader,
}


def load_documents(file_paths: List[str | Path]) -> List[Document]:
    docs: List[Document] = []
    for fp in file_paths:
        fp = Path(fp)
        suffix = fp.suffix.lower()
        loader_cls = LOADER_MAP.get(suffix)
        if loader_cls is None:
            logger.warning(f"Unsupported file type: {fp}")
            continue
        try:
            loader = loader_cls(str(fp))
            loaded = loader.load()
            for doc in loaded:
                doc.metadata.setdefault("source", fp.name)
            docs.extend(loaded)
            logger.info(f"Loaded {len(loaded)} chunks from {fp.name}")
        except Exception as e:
            logger.error(f"Failed to load {fp}: {e}")
    return docs


def split_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)
    logger.info(f"Split into {len(chunks)} chunks")
    return chunks
