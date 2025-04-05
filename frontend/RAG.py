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
            print("\nEmbeddings Response:")

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
    

def query_llm_with_embeddings(query, embeddings, context=None):
    """
    Send a query to the Mistral LLM along with embeddings for context.

    Args:
        query (str): The user's query
        embeddings: The embeddings from the get_embeddings function
        context (dict, optional): Additional context for the query

    Returns:
        The LLM response
    """
    print_step(2, "Querying LLM with Embeddings")
    try:
        # Prepare Mistral API request
        mistral_api_url = "https://api.mistral.ai/v1/chat/completions"

        # Format embeddings for inclusion in the prompt
        embeddings_text = str(embeddings)
        if len(embeddings_text) > 1000:
            embeddings_text = f"[Embedding vector with {len(embeddings_text)} characters]"

        # Create system prompt
        system_prompt = """
        Tu es une application qui remplace les formateurs de la Croix-Rouge. Tu dois proposer à l'utilisateur (bénévole formé aux premiers secours) 
        des cas concrets en utilisant les embeddings fournis comme contexte pour entrainer l'utilisateur, en ne lui donnant pas toutes les informations en même temps, mais au fur et à mesure de leur découverte. 
        Par exemple, au départ, tu ne lui donnes que les informations pour lesquelles il a été appelé. 
        Puis, lorsque l'utilisateur arrive sur place, tu lui fournis les informations visuelles qu'il peut constater en regardant la scène dans son ensemble, 
        avant de lui demander ce qu'il ferait dans cette situation. 
        Tu lui fournir des informations supplémentaires en fonction de sa réponse: Par exemple, s'il te dit « interroger les témoins », tu lui donnes les informations correspondantes. 
        S'il te dit prendre la tension de la victime, tu lui donnes l'information correspondante, puis tu attends sa prochaine action. 
        Tu dois évaluer ses actions et son analyse sur la base de la partie Évaluation de la fiche de cas.
        Fournis toujours une réponse claire et concise basée sur le sens sémantique capturé par les embeddings. 
        Commence directement par le scénario sans dire "Bien sûr, voici...".
        Ne rappelle pas les étapes à suivre et finis toujours par la question "Que faites vous ou qu'en déduisez-vous?"
        """

        # Create user prompt with embeddings
        user_prompt = f"""
        Query: {query}

        Embedding context: {embeddings_text}
        """

        if context:
            user_prompt += f"\nAdditional context: {json.dumps(context)}"

        print("User Prompt:")
        print(user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt)

        # Prepare Mistral API request
        mistral_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MISTRAL_API_KEY}"
        }

        mistral_data = {
            "model": "mistral-large-latest",
            "max_tokens": 800,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        print("\nSending request to Mistral API...")

        # Make the request to Mistral API
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

        # Extract the content from the Mistral response
        llm_text = mistral_result.get('choices', [{}])[0].get('message', {}).get('content', '')

        print("\nMistral Response:")
        print(llm_text[:500] + "..." if len(llm_text) > 500 else llm_text)

        return llm_text

    except Exception as e:
        print(f"Error querying LLM: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None


