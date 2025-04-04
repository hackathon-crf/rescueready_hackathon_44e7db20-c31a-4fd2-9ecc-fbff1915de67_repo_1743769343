import os
from mistralai import Mistral
import csv
import datetime

MODEL_NAME= "mistral-large-latest"
LOG_FILE = "mistral_usage_log.csv"

def call_mistral():

    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)

    try:
        # Make the API call
        chat_response = client.chat.complete(
            model= MODEL_NAME,
            messages = [
                {
                    "role": "user",
                    "content": "Tu es un formateur de la croix rouge aux premiers secours. \
                    Imagine un scénario d'apprentissage pour un bénévole, decris lui juste la situation de base pour laquelle il est appelé",
                },
            ]
        )

        # --- Usage Monitoring ---
        model_used = chat_response.model
        prompt_tokens = chat_response.usage.prompt_tokens
        completion_tokens = chat_response.usage.completion_tokens
        total_tokens = chat_response.usage.total_tokens

        print(f"Model Used: {model_used}")
        print(f"Prompt Tokens: {prompt_tokens}")
        print(f"Completion Tokens: {completion_tokens}")
        print(f"Total Tokens: {total_tokens}")
        log_usage_to_csv(model_used, prompt_tokens, completion_tokens, total_tokens)
        return(chat_response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        # Optionally log errors separately, but don't log token usage for failed calls
        return None

# --- CSV Logging Function ---
import threading
log_lock = threading.Lock() # Use lock if making concurrent calls

def log_usage_to_csv(model, prompt_tokens, completion_tokens, total_tokens):
    """Appends usage data to the CSV log file."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    fieldnames = ["TimestampUTC", "Model", "PromptTokens", "CompletionTokens", "TotalTokens"]
    data_row = {
        "TimestampUTC": timestamp,
        "Model": model,
        "PromptTokens": prompt_tokens,
        "CompletionTokens": completion_tokens,
        "TotalTokens": total_tokens,
    }

    with log_lock: # Ensure thread-safe file writing
        file_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists or os.path.getsize(LOG_FILE) == 0:
                writer.writeheader() # Write header only if file is new/empty
            writer.writerow(data_row)
    print(f"Logged usage to {LOG_FILE}")

# --- Example Usage ---
if __name__ == "__main__":
    prompt = "What is the capital of France?"
    response_content = call_mistral_and_log(prompt)
    if response_content:
        print(f"\nMistral Response:\n{response_content}")

    # Example 2
    prompt_2 = "Explain the concept of recursion in programming."
    response_content_2 = call_mistral_and_log(prompt_2)
    if response_content_2:
        print(f"\nMistral Response 2:\n{response_content_2}")
      


