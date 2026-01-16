"""Data models and schemas."""

from typing import List, Optional

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    """Response model for document upload endpoint."""

    document_id: str
    filename: str
    message: str = "File uploaded successfully"
    text_length: int = 0
    needs_ocr: bool = False
    extraction_method: Optional[str] = None
    num_chunks: int = 0
    num_embeddings: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "research_paper.pdf",
                "message": "File uploaded successfully",
                "text_length": 1234,
                "needs_ocr": False,
                "extraction_method": "pdfplumber",
                "num_chunks": 5,
                "num_embeddings": 5,
            }
        }


class Document(BaseModel):
    """Document model for listing documents."""

    id: str
    filename: str
    uploaded_at: str
    text_length: Optional[int] = None
    needs_ocr: Optional[bool] = None
    extraction_method: Optional[str] = None
    num_chunks: Optional[int] = None
    num_embeddings: Optional[int] = None
    metadata: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "research_paper.pdf",
                "uploaded_at": "2024-01-15T10:30:00",
                "text_length": 1234,
                "needs_ocr": False,
                "extraction_method": "pdfplumber",
                "num_chunks": 5,
                "num_embeddings": 5,
            }
        }


class DocumentListResponse(BaseModel):
    """Response model for document list endpoint."""

    documents: List[Document]

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "research_paper.pdf",
                        "uploaded_at": "2024-01-15T10:30:00",
                        "text_length": 1234,
                        "needs_ocr": False,
                        "extraction_method": "pdfplumber",
                        "num_chunks": 5,
                        "num_embeddings": 5,
                    }
                ]
            }
        }


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    query: str
    top_k: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the side effects of this medication?",
                "top_k": 5,
            }
        }


class Citation(BaseModel):
    """Citation model for query results."""

    document_id: str
    chunk_index: int
    text: str
    page_number: Optional[int] = None
    similarity_score: float

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "chunk_index": 0,
                "text": "The medication showed significant improvement...",
                "page_number": 1,
                "similarity_score": 0.85,
            }
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    answer: str
    citations: List[Citation]
    confidence: float

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the documents...",
                "citations": [
                    {
                        "document_id": "550e8400-e29b-41d4-a716-446655440000",
                        "chunk_index": 0,
                        "text": "The medication showed significant improvement...",
                        "similarity_score": 0.85,
                    }
                ],
                "confidence": 0.85,
            }
        }
