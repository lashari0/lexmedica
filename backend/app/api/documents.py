"""Document upload and management endpoints."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.models import (
    DocumentUploadResponse,
    Document,
    DocumentListResponse,
    DeleteDocumentResponse,
    DeleteDuplicatesResponse,
)
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
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
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
    # Validate file extension against allowed extensions
    if not file_extension or file_extension[1:] not in settings.allowed_extensions:
        allowed = ", ".join(settings.allowed_extensions)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed extensions: {allowed}. Got: {file_extension}",
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


def _detect_duplicates(documents: List[Dict]) -> List[Dict]:
    """
    Detect duplicate documents based on filename.
    Marks duplicates and identifies the original (keeps the first occurrence).
    
    Args:
        documents: List of document dictionaries
        
    Returns:
        List of documents with duplicate information added
    """
    # Group documents by filename (case-insensitive)
    filename_groups: Dict[str, List[Dict]] = {}
    for doc in documents:
        filename_lower = doc["filename"].lower()
        if filename_lower not in filename_groups:
            filename_groups[filename_lower] = []
        filename_groups[filename_lower].append(doc)
    
    # Mark duplicates (keep first occurrence as original)
    for filename, group in filename_groups.items():
        if len(group) > 1:
            # Sort by uploaded_at to keep the oldest as original
            group.sort(key=lambda x: x.get("uploaded_at", ""))
            original_id = group[0]["id"]
            
            for doc in group:
                if doc["id"] == original_id:
                    doc["is_duplicate"] = False
                    doc["duplicate_of"] = None
                else:
                    doc["is_duplicate"] = True
                    doc["duplicate_of"] = original_id
    
    return documents


@router.get("", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    """
    List all uploaded documents by querying ChromaDB and uploads directory.
    Also detects and marks duplicate documents.
    
    Returns:
        List of document metadata with duplicate information
    """
    documents = []
    try:
        vector_store = VectorStore()
        upload_path = settings.upload_dir
        
        # Get all unique document IDs from ChromaDB
        all_chunks = vector_store.collection.get()
        if all_chunks and all_chunks.get("metadatas"):
            # Extract unique document IDs with their metadata
            doc_metadata_map: Dict[str, Dict] = {}
            
            for i, metadata in enumerate(all_chunks["metadatas"]):
                if metadata and "document_id" in metadata:
                    doc_id = metadata["document_id"]
                    filename = metadata.get("filename", f"{doc_id}.pdf")
                    
                    if doc_id not in doc_metadata_map:
                        doc_metadata_map[doc_id] = {
                            "id": doc_id,
                            "filename": filename,
                            "num_chunks": 0,
                        }
                    doc_metadata_map[doc_id]["num_chunks"] += 1
            
            # Check which files exist and get their upload times
            for doc_id, doc_info in doc_metadata_map.items():
                file_path = upload_path / f"{doc_id}.pdf"
                if file_path.exists():
                    file_stat = file_path.stat()
                    doc_info["uploaded_at"] = datetime.fromtimestamp(
                        file_stat.st_mtime
                    ).isoformat()
                    doc_info["text_length"] = None
                    doc_info["needs_ocr"] = None
                    doc_info["extraction_method"] = None
                    doc_info["num_embeddings"] = doc_info["num_chunks"]
                    doc_info["is_duplicate"] = False
                    doc_info["duplicate_of"] = None
                    doc_info["metadata"] = None
                    
                    documents.append(doc_info)
        
        # Detect duplicates
        documents = _detect_duplicates(documents)
        
        # Count duplicates
        duplicate_count = sum(1 for doc in documents if doc.get("is_duplicate", False))
        
        logger.info(
            f"Listed {len(documents)} documents ({duplicate_count} duplicates)"
        )
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
    
    return DocumentListResponse(
        documents=[Document(**doc) for doc in documents],
        total_documents=len(documents),
        duplicate_count=sum(1 for doc in documents if doc.get("is_duplicate", False)),
    )


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(document_id: str) -> DeleteDocumentResponse:
    """
    Delete a document and all its chunks from ChromaDB.
    
    Args:
        document_id: Document ID to delete
        
    Returns:
        Deletion confirmation with details
    """
    upload_path = settings.upload_dir
    file_path = upload_path / f"{document_id}.pdf"
    
    chunks_deleted = 0
    file_deleted = False
    
    try:
        # Delete from ChromaDB
        vector_store = VectorStore()
        chunks_deleted = vector_store.delete_document(document_id)
        logger.info(f"Deleted {chunks_deleted} chunks for document {document_id}")
    except Exception as e:
        logger.error(f"Failed to delete chunks from ChromaDB: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document chunks: {str(e)}",
        )
    
    # Delete file from disk
    try:
        if file_path.exists():
            file_path.unlink()
            file_deleted = True
            logger.info(f"Deleted file for document {document_id}")
    except Exception as e:
        logger.warning(f"Failed to delete file {file_path}: {str(e)}")
        # Don't fail if file deletion fails, chunks are already deleted
    
    # Remove from in-memory store if present
    if document_id in documents_store:
        del documents_store[document_id]
    
    return DeleteDocumentResponse(
        message="Document deleted successfully",
        document_id=document_id,
        chunks_deleted=chunks_deleted,
        file_deleted=file_deleted,
    )


@router.delete("/duplicates/clean", response_model=DeleteDuplicatesResponse)
async def delete_duplicates() -> DeleteDuplicatesResponse:
    """
    Delete all duplicate documents, keeping only the original (first uploaded) version.
    
    Returns:
        Summary of deletion operation
    """
    try:
        # Get all documents with duplicate info
        list_response = await list_documents()
        documents = list_response.documents
        
        # Find all duplicates
        duplicates = [doc for doc in documents if doc.is_duplicate]
        
        if not duplicates:
            return DeleteDuplicatesResponse(
                message="No duplicate documents found",
                deleted_count=0,
                deleted_ids=[],
            )
        
        deleted_count = 0
        deleted_ids = []
        errors = []
        
        for duplicate in duplicates:
            try:
                result = await delete_document(duplicate.id)
                deleted_count += 1
                deleted_ids.append(duplicate.id)
                logger.info(f"Deleted duplicate document {duplicate.id}")
            except Exception as e:
                error_msg = f"Failed to delete {duplicate.id}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return DeleteDuplicatesResponse(
            message=f"Deleted {deleted_count} duplicate document(s)",
            deleted_count=deleted_count,
            deleted_ids=deleted_ids,
            errors=errors if errors else None,
        )
    except Exception as e:
        logger.error(f"Failed to delete duplicates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete duplicates: {str(e)}",
        )
