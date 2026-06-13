"""
Multi-provider LLM Client - re-exports from shared
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.llm import llm_client, MultiLLMClient, ModelProvider, get_available_models, SYSTEM_PROMPT
