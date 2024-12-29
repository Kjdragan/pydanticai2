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

    def _create_batch_evaluation_prompt(self, items: List[ContentForJudging]) -> dict:
        """Create evaluation prompt for content items that ensures JSON output"""
        
        system_prompt = """You are a content evaluation system. Your task is to evaluate web content and output a JSON object containing evaluations for each item.
        
For each content item, determine if it contains substantial article content vs HTML markup, navigation elements, or error messages.
For valid articles, identify an appropriate source citation.

EXAMPLE INPUTS AND OUTPUTS:

Content Item 1:
URL: https://tech.example.com/article1
Title: Breaking News
Content: <div class="nav">Home About Contact</div><ul class="menu"><li>News</li><li>Sports</li></ul>

Content Item 2:
URL: https://news.reuters.com/markets/article
Title: Market Analysis: Q4 Results
Content: The fourth quarter showed strong growth across all sectors. Analysts point to several key factors that contributed to this performance. The technology sector led gains with a 15% increase. Industry experts suggest this trend will continue into the next quarter, citing strong fundamentals and increasing demand.

Content Item 3:
URL: https://example.com/article
Title: Latest Updates
Content: Please subscribe to view this content. Subscribe now for full access to our premium articles.

Content Item 4:
URL: https://blocked.com/news
Title: Technology News
Content: Error 403: Access Denied. Your IP address has been blocked.

Content Item 5:
URL: https://news.example.com/story
Title: Short Update
Content: Market closed up today. More updates coming soon.

EXAMPLE JSON OUTPUT:
{
    "evaluations": [
        {
            "item_id": "1",
            "is_valid": false,
            "source": null,
            "reason": "mainly html markup - contains only navigation elements and menu structure"
        },
        {
            "item_id": "2",
            "is_valid": true,
            "source": "Reuters Markets (reuters.com)",
            "reason": "comprehensive market analysis with data and expert insights"
        },
        {
            "item_id": "3",
            "is_valid": false,
            "source": null,
            "reason": "paywall content - only subscription message visible"
        },
        {
            "item_id": "4",
            "is_valid": false,
            "source": null,
            "reason": "scraping blocked - access denied error message"
        },
        {
            "item_id": "5",
            "is_valid": false,
            "source": null,
            "reason": "too short - content is only two sentences without substantial information"
        }
    ],
    "total_evaluated": 5,
    "total_valid": 1
}"""

        # Format the actual content items
        content_items = []
        for i, item in enumerate(items, 1):
            item_prompt = f"""Content Item {i}:
URL: {item.url}
Title: {item.title}
Content: {item.raw_content[:1000]}{"..." if len(item.raw_content) > 1000 else ""}"""
            content_items.append(item_prompt)

        user_prompt = f"""Evaluate these {len(items)} content items and provide a JSON object with your evaluations.
Each evaluation should indicate if the content is valid for research use and include a source citation for valid articles.

{chr(10).join(content_items)}"""

        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"}
        }

    async def _get_llm_evaluation(self, prompt_data: dict) -> dict:
        """Get evaluation from DeepSeek with error handling"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=prompt_data["messages"],
                response_format=prompt_data["response_format"],
                max_tokens=4000,
                temperature=0.1  # Low temperature for consistent formatting
            )
            
            # Parse JSON response
            try:
                return json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                raise LLMEvaluationError(f"Invalid JSON in LLM response: {str(e)}")
                
        except Exception as e:
            logging.error(f"LLM API call failed: {str(e)}")
            raise LLMEvaluationError(f"LLM evaluation failed: {str(e)}")

    def _parse_evaluations(self, llm_response: dict) -> List[EvaluationOutput]:
        """Parse and validate LLM response into evaluation outputs"""
        try:
            # Validate basic structure
            if not isinstance(llm_response, dict):
                raise LLMEvaluationError("LLM response is not a dictionary")
            
            evaluations = llm_response.get("evaluations")
            if not evaluations or not isinstance(evaluations, list):
                raise LLMEvaluationError("Missing or invalid 'evaluations' array in response")

            # Process each evaluation
            outputs: List[EvaluationOutput] = []
            
            for eval_data in evaluations:
                try:
                    # Validate required fields
                    if not isinstance(eval_data, dict):
                        raise LLMEvaluationError(f"Invalid evaluation format: {eval_data}")
                    
                    # Extract fields with validation
                    is_valid = eval_data.get("is_valid")
                    if not isinstance(is_valid, bool):
                        raise LLMEvaluationError(f"Invalid or missing 'is_valid' field: {eval_data}")
                    
                    reason = eval_data.get("reason")
                    if not reason or not isinstance(reason, str):
                        raise LLMEvaluationError(f"Invalid or missing 'reason' field: {eval_data}")
                    
                    # Source is optional and only for valid content
                    source = eval_data.get("source") if is_valid else None
                    if is_valid and (not source or not isinstance(source, str)):
                        raise LLMEvaluationError(f"Missing source for valid content: {eval_data}")

                    # Create EvaluationOutput
                    output = EvaluationOutput(
                        is_valid=is_valid,
                        source=source,
                        reason=reason
                    )
                    outputs.append(output)
                
                except ValidationError as ve:
                    # Handle Pydantic validation errors
                    logging.error(f"Validation error for evaluation: {ve}")
                    # Create an error evaluation
                    outputs.append(EvaluationOutput(
                        is_valid=False,
                        source=None,
                        reason=f"evaluation_error: {str(ve)}"
                    ))
                except Exception as e:
                    # Handle any other errors in individual evaluation
                    logging.error(f"Error processing evaluation: {e}")
                    outputs.append(EvaluationOutput(
                        is_valid=False,
                        source=None,
                        reason=f"processing_error: {str(e)}"
                    ))

            # Verify we have the right number of evaluations
            expected_count = llm_response.get("total_evaluated", 0)
            if len(outputs) != expected_count:
                logging.warning(
                    f"Mismatch in evaluation count. Expected: {expected_count}, Got: {len(outputs)}"
                )

            return outputs

        except Exception as e:
            logging.error(f"Fatal error parsing LLM response: {e}")
            raise LLMEvaluationError(f"Failed to parse LLM response: {str(e)}")

    async def evaluate_tavily_results(
        self, 
        query: str, 
        results: List[TavilyResult]
    ) -> QueryResults:
        """Process a group of Tavily results for a single query"""
        
        # Convert to internal format
        content_items = [
            ContentForJudging(
                id=f"{query}-{i}",
                query=query,
                raw_content=result.raw_content or result.content,
                url=result.url,
                title=result.title,
                metadata={
                    "focused_content": result.content,
                    "published_date": result.published_date
                }
            )
            for i, result in enumerate(results)
        ]
        
        # Process in batches
        all_evaluations = await self._process_batches(content_items)
        
        # Collect results
        query_results = QueryResults(
            query=query,
            total_evaluated=len(results)
        )
        
        # Process evaluations
        for item, eval_output in zip(content_items, all_evaluations):
            if eval_output.is_valid:
                valid_result = ValidResult(
                    url=item.url,
                    title=item.title,
                    source=eval_output.source,
                    focused_content=item.metadata["focused_content"],
                    raw_content=item.raw_content,
                    published_date=item.metadata.get("published_date"),
                    query=item.query,
                    evaluation_reason=eval_output.reason
                )
                query_results.valid_results.append(valid_result)
                query_results.total_passed += 1
            
            # Track failure reasons
            if not eval_output.is_valid:
                query_results.failure_reasons[eval_output.reason] = \
                    query_results.failure_reasons.get(eval_output.reason, 0) + 1
                    
        return query_results

    async def _process_batches(
        self, 
        items: List[ContentForJudging]
    ) -> List[EvaluationOutput]:
        """Process items in batches"""
        
        batches = [
            items[i:i + self.batch_size] 
            for i in range(0, len(items), self.batch_size)
        ]
        
        all_results = []
        for batch in batches:
            prompt_data = self._create_batch_evaluation_prompt(batch)
            response = await self._get_llm_evaluation(prompt_data)
            batch_results = self._parse_evaluations(response)
            all_results.extend(batch_results)
            
        return all_results