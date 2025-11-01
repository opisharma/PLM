# download_model.py
import os
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- Configuration ---
MODEL_NAME = "distilgpt2"
CACHE_DIR = os.path.join(".", "model_cache", MODEL_NAME)

def download_model():
    """
    Downloads and saves the specified Hugging Face model and tokenizer
    to a local directory for offline use.
    """
    print(f"--- 🧠 Downloading Model: {MODEL_NAME} ---")
    
    # Create the cache directory if it doesn't exist
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"✅ Created cache directory: {CACHE_DIR}")

    try:
        # Download and save the tokenizer
        print("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        tokenizer.save_pretrained(CACHE_DIR)
        print("✅ Tokenizer downloaded and saved successfully.")

        # Download and save the model
        print("Downloading model (this may take a moment)...")
        model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
        model.save_pretrained(CACHE_DIR)
        print("✅ Model downloaded and saved successfully.")
        
        print(f"\n--- 🎉 Model '{MODEL_NAME}' is ready for offline use in '{CACHE_DIR}' ---")

    except Exception as e:
        print(f"❌ An error occurred during download: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    download_model()
