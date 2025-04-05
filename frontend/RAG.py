import requests
import json
import os
import time

RAG_API_ENDPOINT="https://hackathon-ia-et-crise.fr/admin/rag-system/api/app"
MISTRAL_API_KEY ="pJKvqp2uKF9PkULrp6LywyBsDHWaWnQZ"

def print_step(step_number, step_name):
    """Print a formatted step header"""
    print("\n" + "="*80)
    print(f"STEP {step_number}: {step_name}")
    print("="*80)

def print_json(data):
    """Print formatted JSON data"""
    print(json.dumps(data, indent=2))

def get_collections():
    """Retrieve available collections from the RAG system"""
    print_step(2, "Retrieving Available Collections")
    try:
        url = f"{RAG_API_ENDPOINT}/collection/list/"
        # url = "https://hackathon-ia-et-crise.fr/admin/rag-system/api/app/collection/list/"

        print(f"Calling: {url}")

        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to retrieve collections: {response.status_code}")
            print(f"Response: {response.text}")
            return []

        # Parse the response
        result = response.json()
        print(f"result={result}")
        # collections = [result]

        print("Available Collections:")
        print_json(result)

        return result
    except Exception as e:
        print(f"Error fetching collections: {str(e)}")
        return []

def get_embeddings(query, collection_name):
    """
    Get embeddings for a query using the specified collection.

    Args:
        query (str): The query text to get embeddings for
        collection_name (str):collection name to use

    Returns:
        The embeddings response
    """
    print_step(2, "Getting Embeddings for Query")
    try:
        url = f"{RAG_API_ENDPOINT}/inferencing/get_embeddings"

        params = {
            "query": query,
            "collection_name": collection_name,
            "api_key": MISTRAL_API_KEY
        }
        if isinstance(collection_name, list):
            collection_name = collection_name[0] if collection_name else ""

        collection_name = str(collection_name).strip().strip('"\'[]')

        params = {
            "query": query,
            "collection_name": collection_name,
            "api_key": MISTRAL_API_KEY
        }

        print(f"Calling: {url}")
        print("Parameters:")
        print_json({k: v if k != "api_key" else "****" for k, v in params.items()})

        # Make the request
        response = requests.post(url, params=params)

        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        # Try to parse as JSON
        try:
            result = response.json()
            # print("\nEmbeddings Response:")

            # Check if the result is a string containing a large embedding vector
            if isinstance(result, str) and len(result) > 1000:
                # If it's a very long string (likely an embedding vector), just show a preview
                print(f"Received embedding vector (showing first 100 chars): {result[:100]}...")
                print(f"Full vector length: {len(result)} characters")
            else:
                print_json(result)

            return result
        except json.JSONDecodeError:
            # If it's not JSON, just return the text
            print("\nResponse (text):")
            print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
            return response.text

    except Exception as e:
        print(f"Error getting embeddings: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None


def query_llm_with_embeddings(query, embeddings, messages):
    """
    Send a query to the Mistral LLM along with embeddings for context.

    Args:
        query (str): The user's query
        embeddings: The embeddings from the get_embeddings function
        context (list, optional): Conversation history, updated with the current exchange

    Returns:
        str: The LLM response
    """
    print_step(2, "Querying LLM with Embeddings")
    try:
        print("User Prompt:\n")
        print(f"Query: {query}\n")

        # Mistral API setup
        mistral_api_url = "https://api.mistral.ai/v1/chat/completions"
        mistral_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MISTRAL_API_KEY}"
        }
    
        # Initialize the conversation if not already done
        if messages is None:
            messages = []

        # Compose final request payload
        mistral_data = {
            "model": "mistral-large-latest",
            "max_tokens": 800,
            "messages": messages
        }

        print("\nSending request to Mistral API...")

        # Send the request to Mistral
        mistral_response = requests.post(
            mistral_api_url,
            headers=mistral_headers,
            json=mistral_data
        )

        if mistral_response.status_code != 200:
            print(f"Mistral API call failed with status code: {mistral_response.status_code}")
            print(f"Response: {mistral_response.text}")
            return None

        mistral_result = mistral_response.json()
        llm_text = mistral_result.get('choices', [{}])[0].get('message', {}).get('content', '')

        print("\nMistral Response:")
        print(llm_text[:500] + "..." if len(llm_text) > 500 else llm_text)
        return llm_text
    except Exception as e:
            print(f"Error querying LLM: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None


