import requests
from settings.config import settings
from dotenv import load_dotenv
import os
import streamlit as st
import json


# Load environment variables from .client_env
load_dotenv(".client_env")

# Get environment variables, with fallbacks
DOMAIN_NAME = os.getenv("DOMAIN_NAME", "localhost")
ROOT_PATH = os.getenv("ROOT_PATH", "")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8090")
RAG_API_ENDPOINT=os.getenv("RAG_API_ENDPOINT", "")
MISTRAL_API_KEY=os.getenv("ANTHROPIC_API_KEY", "")

def call_backend_test():
    try:
        # Construct URL with proper protocol and format
        # url = f"https://{DOMAIN_NAME}{ROOT_PATH}/api/app/test/"
        url = "http://localhost:8000/api/app/test/"
        print(f"Calling backend URL: {url}")

        params = {}
        response = requests.get(url, params=params)
        print(f"Response status: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error calling backend: {str(e)}")
        return {"error": str(e)}

    
def query_collections(self, prompt, collections):
    """
    Query the RAG system with a custom prompt.
    
    Args:
        prompt: The prompt to send to the RAG system
        collections: List of collection names to query
        
    Returns:
        RAG system response
    """
    url = f"{self.base_url}/inferencing/retrieve_answer_using_collections/"
    params = {
        "query": prompt,
        "collection_name": json.dumps(collections)
    }
    
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error querying RAG system: {str(e)}")

def get_collections():
    """
    Retrieve available collections from the RAG system.
    
    Returns:
        List of collections with metadata
    """
    try:
        # First try to use the cached collections if available
        if "rag_collections" not in st.session_state:
            url = f"{RAG_API_ENDPOINT}/collection/list/"
            
            response = requests.get(url)
            
            if response.status_code != 200:
                st.error(f"Failed to retrieve collections: {response.status_code}")
                return []
            
           # Parse the response
            result = response.json()
            collections = [result]
            
            # Cache the collections for future use
            st.session_state.rag_collections = collections
            
        return st.session_state.rag_collections
    except Exception as e:
        st.error(f"Error fetching collections: {str(e)}")
        return []

def get_scenario(context, collection):
    """
    Request scenario from the backend.
    
    Args:
        context: Dictionary with emergency details
        collection: String with the selected collection name
    
    Returns:
        List containing [RAG_extraction, LLM_response]
    """
    try:
        host = "https://hackathon-ia-et-crise.fr/admin/rag-system"
        
        # Ensure collection is properly formatted
        if isinstance(collection, list):
            collection_name = collection[0] if collection else ""
        else:
            collection_name = collection
            
        # Clean up the collection name
        collection_name = collection_name.strip().strip('"\'[]')
        
        # Step 1: Use the correct endpoint path
        retrieval_url = f"{host}/api/app/inferencing/retrieve_answer_using_collections"
        
        query_text = f"""
        Emergency situation:
        Situation: {context["situation"]}
        Emergency Type: {context["emergency_type"]}
        Severity: {context["severity"]}
        Age Group: {context["age_group"]}
        """
        
        retrieval_system_prompt = """
        Extract and retrieve relevant information for this emergency situation. 
        Focus on factual information from the collection.
        """
        
        # Format collection name as a JSON array string
        collection_list = json.dumps([collection_name])
        
        retrieval_params = {
            "query": query_text,
            "model_family": "anthropic",
            "model_name": "claude-3-haiku-20240307",
            "api_key": ANTHROPIC_API_KEY,
            "prompt": retrieval_system_prompt,
            "collection_name": collection_list,
            "history_data": json.dumps([])
        }
        
        
        retrieval_response = requests.post(retrieval_url, params=retrieval_params)
        
        if retrieval_response.status_code != 200:
            st.error(f"Failed to retrieve from collections: {retrieval_response.status_code}")
            st.error(f"Response: {retrieval_response.text}")
            return [None, None]
        
        try:
            rag_extraction = retrieval_response.json()
        except json.JSONDecodeError:
            rag_extraction = retrieval_response.text
        
        # Step 2: Use Claude API directly with HTTP request instead of the SDK
        
        # Extract useful content from the retrieval response
        retrieval_content = ""
        if isinstance(rag_extraction, str):
            retrieval_content = rag_extraction
        else:
            retrieval_content = json.dumps(rag_extraction, indent=2)
        
        # Prepare Claude API request
        claude_api_url = "https://api.anthropic.com/v1/messages"
        
        guidance_system_prompt = """
        You are an emergency response assistant. Use the provided retrieved information to give guidance for the emergency situation described.
        
        Provide a comprehensive response in JSON format with the following structure:
        {
            "summary": "Brief summary of immediate actions",
            "steps": [
                {"step": 1, "title": "Step title", "description": "Detailed instruction"},
                ...
            ],
            "checklist": [
                "Checklist item 1",
                "Checklist item 2",
                ...
            ],
            "sources": [
                {"title": "Source document title", "relevance": "Relevance description"}
            ]
        }
        """
        
        guidance_user_prompt = f"""
        Emergency situation:
        Situation: {context["situation"]}
        Emergency Type: {context["emergency_type"]}
        Severity: {context["severity"]}
        Age Group: {context["age_group"]}
        
        Retrieved information:
        {retrieval_content}
        """
        
        # Prepare Claude API request
        claude_headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        claude_data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1000,
            "system": guidance_system_prompt,
            "messages": [
                {"role": "user", "content": guidance_user_prompt}
            ]
        }
        
        # Make the request to Claude API
        claude_response = requests.post(
            claude_api_url,
            headers=claude_headers,
            json=claude_data
        )
        
        if claude_response.status_code != 200:
            st.error(f"Failed to get Claude response: {claude_response.status_code}")
            st.error(f"Response: {claude_response.text}")
            return [rag_extraction, None]
        
        claude_result = claude_response.json()
        
        # Extract the content from the Claude response
        llm_text = claude_result.get('content', [{'text': ''}])[0].get('text', '')
        
        # Try to parse as JSON
        try:
            llm_response = json.loads(llm_text)
        except json.JSONDecodeError:
            st.error("Claude response could not be parsed as JSON:")
            st.error(llm_text[:500])
            llm_response = llm_text
        
        return [rag_extraction, llm_response]
        
    except Exception as e:
        st.error(f"Error in emergency guidance process: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return [None, None]