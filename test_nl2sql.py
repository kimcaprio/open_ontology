#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.nl2sql_service import nl2sql_service

async def test_nl2sql():
    try:
        print("Testing NL2SQL service...")
        result = await nl2sql_service.convert_natural_language_to_sql('show me all users')
        print(f"Success: {result.sql_query}")
        print(f"Confidence: {result.confidence}")
        print(f"Explanation: {result.explanation}")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_nl2sql()) 