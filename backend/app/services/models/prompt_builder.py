"""Prompt building logic for RAG queries."""

from typing import List, Tuple


# Base rules that apply to all questions
BASE_RULES = """
    ANSWERING RULES (MANDATORY):
    - Use ONLY the information provided in the context sections.
    - Do NOT use prior knowledge or inference.
    - Each bullet MUST end with a citation in the form [Context N].
    - Do NOT combine information from multiple contexts in a single bullet.
    - Do NOT write narrative paragraphs.
    - Do NOT speculate or generalize beyond the text.

    MEDICAL SAFETY PROTOCOLS:
    - NEVER imply clinical recommendations unless context explicitly uses "recommend", "should", or "guideline"
    - Replace subjective terms: 
        "important" → "documented in context"
        "risk" → "reported association"
        "effect" → "observed outcome"
    - For drug/device mentions: ALWAYS include qualifiers like "in the context" or "as reported in [Context N]"
- If discussing mortality/morbidity: USE EXACT PHRASING from context (e.g., "30% increased risk" NOT "high risk")

    REFUSAL RULE:
    - If the context does not contain sufficient information to answer the question,
    respond with exactly:
    "• Insufficient evidence in the provided context to answer this question"
    """

# Rules specific to document characterization
DOCUMENT_SUMMARY_RULES = """
    DOCUMENT CHARACTERIZATION RULES:
    - Answer MUST be in bullet point format (2–4 bullets maximum).
    - You are characterizing the document's intent and analytical scope.
    - Bullets describe document-level purpose, NOT isolated facts.
    - Use neutral descriptive verbs: "examines", "discusses", "analyzes", "reviews", "describes".
    - AVOID prescriptive verbs: "focuses on", "emphasizes", "provides", "recommends" 
      (unless the context explicitly states these actions).
    - Explicitly mark events/cases as examples: "using [X] as an illustrative example".
    - Do NOT imply examples are central to the document's purpose unless explicitly stated.
    - Do NOT imply recommendations, guidance, or practice implications unless explicitly stated.
    - Do NOT generalize scope with interpretive language like "routinely", "commonly", "typically"
      unless these qualifiers appear in the source text.
    - Structure: First bullet = analytical purpose, subsequent = scope/methodology.
    - Characterize analytical intent, NOT just topic coverage.

    VALID EXAMPLES:
    • Analyzes methodological approaches for pediatric exposure assessment [Context 1]
    • Reviews epidemiological evidence using Bradford Hill criteria, with Bhopal incident as illustration [Context 2]

    INVALID EXAMPLES (STRICTLY PROHIBITED):
    • This document focuses on chemical risks for children [Context 1]  (banned verb + topic enumeration)
    • Discusses Bhopal and melamine contamination [Context 2]  (fails to describe analytical purpose)
    """

# Rules for factual questions
FACTUAL_RULES = """
    FACTUAL ANSWERING RULES:
    - Answer MUST be in bullet point format (3–6 bullets maximum).
    - Each bullet MUST contain exactly one factual claim.
    - Do NOT describe document intent or purpose.
    """

# Banned terms for document summary validation
BANNED_TERMS = [
    "highlights",
    "emphasizes",
    "focuses on",
    "provides guidance",
    "recommends",
    "routinely",
    "commonly",
    "everyday",
    "typically",
    "usually",
    "often"
]

# Phrases that indicate document characterization questions
DOCUMENT_QUESTION_PHRASES = [
    "what is this document about",
    "what does this document",
    "describe this document",
    "document is about",
    "document focuses",
    "document discusses",
    "what is the document",
    "document's purpose",
    "document's intent"
]


def is_document_question(query: str) -> bool:
    """
    Detect if a query is asking about document characterization.
    
    Args:
        query: User query text
        
    Returns:
        True if query is about document purpose/intent, False otherwise
    """
    query_lower = query.lower()
    return any(phrase in query_lower for phrase in DOCUMENT_QUESTION_PHRASES)


def violates_summary_contract(answer: str) -> bool:
    """
    Check if answer violates document summary contract.
    
    Args:
        answer: Generated answer text
        
    Returns:
        True if banned terms are found, False otherwise
    """
    lower = answer.lower()
    return any(term in lower for term in BANNED_TERMS)


def build_context_blocks(context_chunks: List[str], prefix: str) -> str:
    """
    Build context blocks with guaranteed 1-based indexing.
    
    Args:
        context_chunks: List of text chunks
        prefix: Prefix for context blocks (e.g., "### Context" or "[Context]")
        
    Returns:
        Formatted context text with numbered blocks
    """
    return "\n\n".join(
        f"{prefix} {i + 1}:\n{chunk}"
        for i, chunk in enumerate(context_chunks)
    )


def build_rag_prompt(
    query: str,
    context_chunks: List[str],
    model: str,
) -> Tuple[str, bool]:
    """
    Build a strict, evidence-bound RAG prompt.
    
    Enforces:
    - Evidence-only answering
    - Bullet format (3–6 bullets for factual, 2–4 for document summaries)
    - Mandatory context citations per bullet
    - Explicit refusal when evidence is insufficient
    
    Args:
        query: User query/question
        context_chunks: List of text chunks retrieved from documents
        model: Model name (used to determine if Qwen format is needed)
        
    Returns:
        Tuple of (prompt string, is_document_question bool)
    """
    is_qwen = "qwen" in model.lower()
    is_doc_question = is_document_question(query)
    
    # Compose rules based on question type
    if is_doc_question:
        format_and_safety_rules = BASE_RULES + DOCUMENT_SUMMARY_RULES
    else:
        format_and_safety_rules = BASE_RULES + FACTUAL_RULES
    
    # Build context blocks
    if is_qwen:
        context_text = build_context_blocks(context_chunks, "### Context")
        
        prompt = f"""<|im_start|>system
        You are a medical evidence assistant operating under strict evidence constraints.

        {format_and_safety_rules}
        <|im_end|>
        <|im_start|>user
        Context sections:
        {context_text}

        Question:
        {query}
        <|im_end|>
        <|im_start|>assistant
        """
    else:
        context_text = build_context_blocks(context_chunks, "[Context]")
        
        prompt = f"""You are a medical evidence assistant operating under strict evidence constraints.

        {format_and_safety_rules}

        Context:
        {context_text}

        Question:
        {query}

        Answer:"""
    
    return prompt, is_doc_question
