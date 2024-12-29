from typing import List, Dict, Any, Optional
import json
from pydantic import ValidationError
import logging
from openai import OpenAI
import os
from dotenv import load_dotenv
from model_binary_judge import (
    TavilyResult, 
    ContentForJudging, 
    EvaluationOutput, 
    ValidResult,
    QueryResults
)

# Load environment variables
load_dotenv()

class LLMEvaluationError(Exception):
    """Custom exception for LLM evaluation errors"""
    pass

class BatchContentJudge:
    """Evaluates batches of content using DeepSeek LLM"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        batch_size: int = 10,
        base_url: str = "https://api.deepseek.com"
    ):
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("No API key provided and DEEPSEEK_API_KEY not found in environment")
            
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.batch_size = batch_size