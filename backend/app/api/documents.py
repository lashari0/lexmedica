"""Document upload and management endpoints."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.models import DocumentUploadResponse, Document, DocumentListResponse
from app.services.pdf_processor import PDFProcessor
from app.services.chunker import Chunker
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# In-memory document store
# Key: document_id, Value: document metadata dict
documents_store: Dict[str, Dict] = {}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document.

    - Validates file extension (PDF only)
    - Validates file size (max 10MB by default)
    - Saves file to uploads directory with unique document ID
    - Extracts text from PDF
    - Chunks extracted text into semantic pieces
    - Generates embeddings for chunks
    - Returns document ID, filename, text extraction info, chunk count, and embedding count
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_extension = Path(file.filename).suffix.lower()
    if file_extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDF files are allowed. Got: {file_extension}",
        )

    # Check if extension is in allowed list (double check)
    if file_extension[1:] not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{file_extension[1:]}' is not allowed. Allowed: {settings.allowed_extensions}",
        )

    # Generate unique document ID
    document_id = str(uuid.uuid4())

    # Prepare file path
    upload_path = settings.upload_dir
    upload_path.mkdir(parents=True, exist_ok=True)
    file_path = upload_path / f"{document_id}.pdf"

    # Read file content to validate size and save
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size / (1024 * 1024):.1f}MB. Got: {file_size / (1024 * 1024):.1f}MB",
        )

    # Validate file is not empty
    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Save file asynchronously
    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}",
        )

    # Extract text from PDF
    text_length = 0
    needs_ocr = False
    extraction_method = None
    extracted_text = ""
    num_chunks = 0

    try:
        processor = PDFProcessor()
        extraction_result = processor.extract_text(file_path)
        extracted_text = extraction_result.get("text", "")
        text_length = len(extracted_text)
        needs_ocr = extraction_result.get("needs_ocr", False)
        extraction_method = extraction_result.get("method")

        # Log if extraction had errors
        if "error" in extraction_result:
            # Don't fail the upload, but note the extraction issue
            logger.warning(
                f"Text extraction had issues for {document_id}: {extraction_result.get('error')}"
            )
    except Exception as e:
        # Don't fail the upload if text extraction fails
        # Just log the error and continue
        logger.warning(f"Text extraction failed for {document_id}: {str(e)}")
        needs_ocr = True  # Assume OCR needed if extraction fails

    # Chunk extracted text if we have text
    chunks = []
    num_chunks = 0
    num_embeddings = 0

    if extracted_text and not needs_ocr:
        try:
            chunker = Chunker()
            chunks = chunker.chunk_text(
                text=extracted_text,
                document_id=document_id,
                filename=file.filename,
            )
            num_chunks = len(chunks)

            # Generate embeddings for chunks
            if chunks:
                try:
                    embedding_service = EmbeddingService()
                    # Extract text from chunks for embedding
                    chunk_texts = [chunk["text"] for chunk in chunks]
                    embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
                    num_embeddings = len(embeddings)

                    # Add embeddings to chunks
                    for i, chunk in enumerate(chunks):
                        chunk["embedding"] = embeddings[i]

                    logger.info(
                        f"Generated {num_embeddings} embeddings for document {document_id}"
                    )

                    # Store chunks in ChromaDB
                    try:
                        vector_store = VectorStore()
                        chunk_ids = vector_store.add_document_chunks(
                            document_id=document_id,
                            chunks=chunks,
                        )
                        # #region agent log
                        with open(r'e:\projects\lexmedica\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            import json
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"documents.py:159","message":"Chunks stored in ChromaDB","data":{"document_id":document_id,"num_chunks":len(chunk_ids)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                        # #endregion
                        logger.info(
                            f"Stored {len(chunk_ids)} chunks in ChromaDB for document {document_id}"
                        )
                    except Exception as e:
                        # Log error but don't fail the upload
                        logger.error(
                            f"Failed to store chunks in ChromaDB for {document_id}: {str(e)}"
                        )
                except Exception as e:
                    # Don't fail the upload if embedding generation fails
                    logger.warning(
                        f"Embedding generation failed for {document_id}: {str(e)}"
                    )
                    num_embeddings = 0
        except Exception as e:
            # Don't fail the upload if chunking fails
            logger.warning(f"Chunking failed for {document_id}: {str(e)}")
            num_chunks = 0

    # Store document metadata in in-memory store
    documents_store[document_id] = {
        "id": document_id,
        "filename": file.filename,
        "uploaded_at": datetime.utcnow().isoformat(),
        "text_length": text_length,
        "needs_ocr": needs_ocr,
        "extraction_method": extraction_method,
        "num_chunks": num_chunks,
        "num_embeddings": num_embeddings,
    }

    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        message="File uploaded successfully",
        text_length=text_length,
        needs_ocr=needs_ocr,
        extraction_method=extraction_method,
        num_chunks=num_chunks,
        num_embeddings=num_embeddings,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """
    List all uploaded documents.

    Returns:
        List of document metadata
    """
    documents = [
        Document(**doc_data) for doc_data in documents_store.values()
    ]
    return DocumentListResponse(documents=documents)
