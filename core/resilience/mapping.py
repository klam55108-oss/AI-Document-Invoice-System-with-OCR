"""Static mapping for resilient configuration to current functional layout."""

from typing import Any, Callable, Dict
import ingestion.image_processor as image_processor
import brain.chatbot.engine as chat_engine
import brain.chatbot.vector_retriever as vector_retriever

# Static mapping of stage_id -> {module_id: implementation_reference}
# This links the "conceptual" modules from the resilient docs to our actual code.
MODULE_MAPPING: Dict[str, Dict[str, Any]] = {
    "ocr": {
        "paddleocr": image_processor.process_image,
        # We can add deepseek-ocr here later if we implement it
    },
    "llm": {
        "deepseek-chat": chat_engine.ChatbotEngine,
        # We can add openai-gpt here later
    },
    "vector_retriever": {
        "supabase-pgvector": vector_retriever.VectorRetriever,
    }
}

def get_implementation(stage_id: str, module_id: str) -> Any:
    """Retrieve the code implementation for a given stage and module."""
    stage = MODULE_MAPPING.get(stage_id)
    if not stage:
        raise ValueError(f"Stage {stage_id} not found in resilience mapping.")
    
    implementation = stage.get(module_id)
    if not implementation:
        raise ValueError(f"Module {module_id} not found in stage {stage_id}.")
        
    return implementation
