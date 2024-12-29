import asyncio
from batch_content_judge import BatchContentJudge
from model_binary_judge import TavilyResult
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    # Initialize the judge using API key from environment
    judge = BatchContentJudge(batch_size=10)  # Will automatically use DEEPSEEK_API_KEY from .env

    # Example Tavily results (simulated)
    sample_results = [
        TavilyResult(
            url="https://example.com/article1",
            title="AI Advances in 2024",
            content="Focused summary of AI progress",
            raw_content="Full article about artificial intelligence advances...",
            published_date="2024-01-15"
        ),
        TavilyResult(
            url="https://example.com/blocked",
            title="Market Analysis",
            content="<div>Subscribe to view content</div>",
            raw_content="<div>Subscribe to view content</div>",
            published_date="2024-01-16"
        ),
        TavilyResult(
            url="https://example.com/article2",
            title="Tech Industry Report",
            content="Summary of quarterly report",
            raw_content="Comprehensive analysis of tech industry growth...",
            published_date="2024-01-17"
        )
    ]

    # Process a single query's results
    query = "AI technology trends 2024"
    try:
        results = await judge.evaluate_tavily_results(query, sample_results)
        
        # Print evaluation results
        print(f"\nResults for query: {query}")
        print(f"Total evaluated: {results.total_evaluated}")
        print(f"Total passed: {len(results.valid_results)}")
        
        # Show valid results
        print("\nValid articles:")
        for valid_result in results.valid_results:
            print(f"\nSource: {valid_result.source}")
            print(f"Title: {valid_result.title}")
            print(f"URL: {valid_result.url}")
            print(f"Evaluation reason: {valid_result.evaluation_reason}")

        # Show failure patterns
        if results.failure_reasons:
            print("\nFailure patterns:")
            for reason, count in results.failure_reasons.items():
                print(f"{reason}: {count} occurrences")

    except Exception as e:
        print(f"Error processing results: {e}")

    # Example of processing multiple queries
    queries_and_results = {
        "AI trends": sample_results[:2],
        "Market analysis": sample_results[1:],
    }

    try:
        all_results = {}
        for query, results in queries_and_results.items():
            query_results = await judge.evaluate_tavily_results(query, results)
            all_results[query] = query_results

        # Aggregate metrics across all queries
        total_evaluated = sum(r.total_evaluated for r in all_results.values())
        total_passed = sum(len(r.valid_results) for r in all_results.values())
        
        print(f"\nOverall Statistics:")
        print(f"Total items evaluated: {total_evaluated}")
        print(f"Total items passed: {total_passed}")
        print(f"Overall pass rate: {(total_passed/total_evaluated)*100:.1f}%")

    except Exception as e:
        print(f"Error processing multiple queries: {e}")

if __name__ == "__main__":
    asyncio.run(main())