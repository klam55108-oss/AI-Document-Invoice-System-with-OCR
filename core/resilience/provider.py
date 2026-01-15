"""Provider functions for resilient configuration modules."""

from typing import Any
from core.resilience.mapping import get_implementation
from core.config import settings

from core.module_registry import register_module, register_stage, register_contract, ModuleInfo, StageInfo, ContractInfo

def bootstrap_resilience():
    """Register the current functional modules as resilient components."""
    # 1. Register Contracts
    register_contract(ContractInfo(
        contract_id="ocr-v1", name="OCR Extraction", 
        inputs=["image_path"], outputs=["text", "confidence"], guarantees=["UTF-8"]
    ))
    register_contract(ContractInfo(
        contract_id="llm-v1", name="Chat Completion", 
        inputs=["messages"], outputs=["response"], guarantees=["Natural Language"]
    ))

    # 2. Register Stages
    register_stage(StageInfo(stage_id="ocr", name="Text Extraction", order=1, capability_contract_id="ocr-v1"))
    register_stage(StageInfo(stage_id="llm", name="Query Analysis", order=2, capability_contract_id="llm-v1"))

    # 3. Register Modules (Mapping to our current layout)
    register_module(ModuleInfo(
        module_id="paddleocr", name="PaddleOCR (Current)", 
        stage_id="ocr", capability_contract_id="ocr-v1", status="available"
    ))
    register_module(ModuleInfo(
        module_id="deepseek-chat", name="DeepSeek (Current)", 
        stage_id="llm", capability_contract_id="llm-v1", status="available"
    ))

def get_ocr_adapter(module_id: str = "paddleocr") -> Any:
    """Get the OCR processing function."""
    return get_implementation("ocr", module_id)

def get_llm_adapter(module_id: str = "deepseek-chat") -> Any:
    """Get the LLM engine class."""
    return get_implementation("llm", module_id)

def get_vector_retriever_adapter(module_id: str = "supabase-pgvector") -> Any:
    """Get the vector retriever class."""
    return get_implementation("vector_retriever", module_id)

# For MVP purposes, these can be used like:
# ocr_fn = get_ocr_adapter()
# result = await ocr_fn(file_path)
