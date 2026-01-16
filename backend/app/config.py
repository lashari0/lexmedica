"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    api_title: str = Field(default="LexMedica API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    api_description: str = Field(
        default="Medical Research Knowledge Assistant API",
        description="API description",
    )
    debug: bool = Field(default=False, description="Debug mode")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # Vector Database Configuration
    chroma_db_path: Path = Field(
        default=Path("chroma_db"),
        description="ChromaDB persistence directory",
    )
    chroma_collection_name: str = Field(
        default="documents",
        description="ChromaDB collection name",
    )

    # Embeddings Configuration
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformers model name",
    )
    embedding_dimension: int = Field(
        default=384,
        description="Embedding dimension (for all-MiniLM-L6-v2)",
    )

    # LLM Configuration
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider: 'ollama' or 'huggingface'",
    )
    llm_model: str = Field(
        default="deepseek-r1:latest",
        description="LLM model name",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL",
    )
    huggingface_api_key: str = Field(
        default="",
        description="Hugging Face API key",
    )
    huggingface_api_url: str = Field(
        default="https://api-inference.huggingface.co/models",
        description="Hugging Face API URL",
    )

    # Retrieval Configuration
    top_k: int = Field(
        default=5,
        description="Number of top chunks to retrieve",
    )
    similarity_threshold: float = Field(
        default=0.3,
        description="Minimum similarity score for retrieval",
    )
    
    # LLM Context Configuration (for memory optimization)
    max_context_chunks: int = Field(
        default=3,
        description="Maximum number of context chunks to send to LLM (reduces memory usage)",
    )
    max_chunk_length: int = Field(
        default=300,
        description="Maximum characters per chunk when sending to LLM (reduces memory usage)",
    )

    # Chunking Configuration
    chunk_size: int = Field(
        default=500,
        description="Chunk size in characters",
    )
    chunk_overlap: int = Field(
        default=50,
        description="Chunk overlap in characters",
    )

    # File Upload Configuration
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file size in bytes",
    )
    allowed_extensions: List[str] = Field(
        default=["pdf"],
        description="Allowed file extensions",
    )
    upload_dir: Path = Field(
        default=Path("uploads"),
        description="Directory for uploaded files",
    )

    # OCR Configuration (for future use)
    enable_ocr: bool = Field(
        default=False,
        description="Enable OCR for scanned PDFs",
    )
    tesseract_cmd: str = Field(
        default="tesseract",
        description="Tesseract OCR command path",
    )

    def __init__(self, **kwargs):
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.chroma_db_path.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
