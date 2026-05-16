import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from flask import Flask, render_template, request, jsonify
import tensorflow as tf
import numpy as np
import pickle
import re
from tensorflow.keras.preprocessing.sequence import pad_sequences
import urllib.request
import shutil

app = Flask(__name__)

# Set vocabulary limit
MAX_VOCAB_SIZE = 40000
sequence_len = 50

def download_file_from_github(github_path, local_path):
    """Download file from GitHub if it doesn't exist locally."""
    print(f"\n📥 Attempting to download {local_path} from GitHub...")
    try:
        # GitHub raw content URL
        raw_url = f"https://raw.githubusercontent.com/ShubhamAIML/Next-Word-Prediction/main/{github_path}"
        print(f"URL: {raw_url}")
        
        with urllib.request.urlopen(raw_url, timeout=30) as response:
            with open(local_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        
        file_size = os.path.getsize(local_path)
        print(f"✅ Downloaded {local_path} ({file_size / (1024*1024):.2f} MB)")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def check_and_fix_lfs_pointer(file_path):
    """Check if file is a Git LFS pointer and download the real file if needed."""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read(100)
        
        if 'version https://git-lfs.github.com/spec' in content:
            print(f"⚠️  {file_path} is a Git LFS POINTER, downloading real file...")
            os.remove(file_path)
            return download_file_from_github(file_path, file_path)
    except Exception as e:
        print(f"Error checking LFS pointer: {e}")
    
    return True

# Load model and tokenizer with vocab limit
try:
    print("\n" + "="*60)
    print("🔄 LOADING MODEL AND TOKENIZER...")
    print("="*60)
    
    model_path = 'next_word_lstm_model.h5'
    tokenizer_path = 'tokenizer.pkl'
    
    # Check and fix LFS pointers
    print(f"\n🔍 Checking {model_path}...")
    if check_and_fix_lfs_pointer(model_path):
        print(f"✅ {model_path} is ready")
    
    print(f"\n🔍 Checking {tokenizer_path}...")
    if check_and_fix_lfs_pointer(tokenizer_path):
        print(f"✅ {tokenizer_path} is ready")
    
    # If files still don't exist, download them
    if not os.path.exists(model_path):
        print(f"\n⚠️  {model_path} missing, downloading...")
        download_file_from_github(model_path, model_path)
    
    if not os.path.exists(tokenizer_path):
        print(f"\n⚠️  {tokenizer_path} missing, downloading...")
        download_file_from_github(tokenizer_path, tokenizer_path)
    
    # Load model
    print(f"\n📂 Loading model from: {os.path.abspath(model_path)}")
    model = tf.keras.models.load_model(model_path)
    print(f"✅ Model loaded! Input shape: {model.input_shape}")
    
    # Load tokenizer
    print(f"\n📂 Loading tokenizer from: {os.path.abspath(tokenizer_path)}")
    with open(tokenizer_path, 'rb') as handle:
        tokenizer = pickle.load(handle)
    print(f"✅ Tokenizer loaded! Vocab size: {len(tokenizer.word_index)}")
    
    # Limit vocabulary to top 40K most frequent words
    original_vocab_size = len(tokenizer.word_index)
    
    if original_vocab_size > MAX_VOCAB_SIZE:
        print(f"\n📊 Original vocabulary: {original_vocab_size} words")
        print(f"📊 Limiting to top {MAX_VOCAB_SIZE} most frequent words...")
        
        # Get word frequencies (assuming word_index is sorted by frequency)
        limited_word_index = {}
        limited_index_word = {}
        
        # Keep top MAX_VOCAB_SIZE words (word_index is 1-indexed)
        for word, index in list(tokenizer.word_index.items())[:MAX_VOCAB_SIZE]:
            limited_word_index[word] = index
            limited_index_word[index] = word
        
        # Update tokenizer
        tokenizer.word_index = limited_word_index
        tokenizer.index_word = limited_index_word
        
        print(f"📊 Vocabulary limited to {len(tokenizer.word_index)} words")
    
    print(f"\n✅✅✅ SUCCESS! Model and tokenizer loaded!")
    print(f"     Model shape: {model.input_shape}")
    print(f"     Vocab size: {len(tokenizer.word_index)} words")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"\n❌❌❌ ERROR LOADING MODEL/TOKENIZER: {e}")
    import traceback
    traceback.print_exc()
    print("="*60 + "\n")
    model = None
    tokenizer = None

def clean_text(text):
    """Clean text exactly like during training."""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def handle_oov_words(text, tokenizer):
    """Handle Out-of-Vocabulary words with intelligent replacement."""
    words = text.split()
    processed_words = []
    
    for word in words:
        if word in tokenizer.word_index:
            processed_words.append(word)
        else:
            # Try to find similar words in vocabulary
            similar_word = find_similar_word(word, tokenizer.word_index)
            if similar_word:
                processed_words.append(similar_word)
            # Skip OOV words that can't be mapped
    
    return ' '.join(processed_words)

def find_similar_word(target_word, word_index):
    """Find similar word in vocabulary using simple heuristics."""
    # Check for common suffixes/prefixes
    suffixes = ['ing', 'ed', 'er', 's', 'ly', 'tion', 'ness']
    prefixes = ['un', 're', 'pre', 'dis', 'in', 'im']
    
    # Try removing suffixes
    for suffix in suffixes:
        if target_word.endswith(suffix):
            root = target_word[:-len(suffix)]
            if root in word_index and len(root) > 2:
                return root
    
    # Try removing prefixes
    for prefix in prefixes:
        if target_word.startswith(prefix):
            root = target_word[len(prefix):]
            if root in word_index and len(root) > 2:
                return root
    
    # Check for exact substring matches
    for word in word_index:
        if len(word) >= 4 and (target_word in word or word in target_word):
            return word
    
    return None

def get_top_predictions(probabilities, tokenizer, top_k=8):
    """Get top K predictions with better filtering."""
    # Get indices sorted by probability (descending)
    top_indices = np.argsort(probabilities)[-top_k:][::-1]
    
    predictions = []
    for idx in top_indices:
        if idx in tokenizer.index_word:
            word = tokenizer.index_word[idx]
            prob = float(probabilities[idx])
            
            # Filter out very low probability predictions
            if prob > 0.005:  # Minimum probability threshold
                predictions.append({
                    'word': word,
                    'probability': prob
                })
    
    return predictions

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    print("=" * 50)
    print("🔍 PREDICT ENDPOINT CALLED")
    print(f"Model loaded: {model is not None}")
    print(f"Tokenizer loaded: {tokenizer is not None}")
    
    if not model or not tokenizer:
        error_msg = 'Model or tokenizer not loaded.'
        print(f"❌ ERROR: {error_msg}")
        return jsonify({'error': error_msg})

    data = request.get_json()
    seed_text = data.get('text', '')
    print(f"📝 Input text: '{seed_text}'")

    if not seed_text.strip():
        print("⚠️ Empty input text")
        return jsonify({'predictions': []})

    try:
        # Clean and preprocess text
        cleaned_seed_text = clean_text(seed_text)
        print(f"🧹 Cleaned text: '{cleaned_seed_text}'")
        
        if not cleaned_seed_text:
            print("⚠️ Cleaned text is empty")
            return jsonify({'predictions': []})
        
        # Handle OOV words
        processed_text = handle_oov_words(cleaned_seed_text, tokenizer)
        print(f"✅ Processed text: '{processed_text}'")
        
        if not processed_text:
            print("⚠️ Processed text is empty after OOV handling")
            # Fallback to common words if all words are OOV
            common_words = ['the', 'and', 'to', 'of']
            print(f"📌 Returning fallback: {common_words}")
            return jsonify({'predictions': common_words})
        
        # Convert to sequences
        encoded_sequence = tokenizer.texts_to_sequences([processed_text])[0]
        print(f"🔢 Encoded sequence: {encoded_sequence[:20]}..." if len(encoded_sequence) > 20 else f"🔢 Encoded sequence: {encoded_sequence}")
        
        if not encoded_sequence:
            print("⚠️ Encoded sequence is empty")
            return jsonify({'predictions': []})
        
        # Pad sequence
        padded_sequence = pad_sequences([encoded_sequence], maxlen=sequence_len, padding='pre')
        print(f"📏 Padded sequence shape: {padded_sequence.shape}")
        
        # Get predictions
        y_pred_probs = model.predict(padded_sequence, verbose=0)[0]
        print(f"🎯 Model output shape: {y_pred_probs.shape}")
        print(f"🎯 Top 5 probs: {np.argsort(y_pred_probs)[-5:][::-1]} with values {np.sort(y_pred_probs)[-5:][::-1]}")
        
        # Get top predictions with enhanced filtering
        top_predictions = get_top_predictions(y_pred_probs, tokenizer, top_k=8)
        print(f"✨ Top predictions: {top_predictions}")
        
        # Extract just the words for the response
        predictions = [pred['word'] for pred in top_predictions[:4]]
        print(f"📤 Final predictions: {predictions}")
        
        # Ensure we have at least some predictions
        if not predictions:
            fallback_words = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it']
            predictions = fallback_words[:4]
            print(f"📌 Using fallback: {predictions}")
        
        result = {
            'predictions': predictions,
            'vocab_size': len(tokenizer.word_index),
            'processed_input_words': len(processed_text.split())
        }
        print(f"✅ Response: {result}")
        print("=" * 50)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ PREDICTION ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return jsonify({'error': 'Could not process the prediction.'})

@app.route('/vocab_stats')
def vocab_stats():
    """Get vocabulary statistics."""
    if not tokenizer:
        return jsonify({'error': 'Tokenizer not loaded'})
    
    vocab_size = len(tokenizer.word_index)
    sample_words = list(tokenizer.word_index.keys())[:50]  # First 50 most frequent words
    
    return jsonify({
        'total_vocabulary_size': vocab_size,
        'max_allowed_size': MAX_VOCAB_SIZE,
        'most_frequent_words': sample_words,
        'model_loaded': model is not None
    })

@app.route('/test_word/<word>')
def test_word(word):
    """Test if a word exists in vocabulary."""
    if not tokenizer:
        return jsonify({'error': 'Tokenizer not loaded'})
    
    word = word.lower()
    exists = word in tokenizer.word_index
    
    result = {
        'word': word,
        'in_vocabulary': exists
    }
    
    if exists:
        result['word_index'] = tokenizer.word_index[word]
    else:
        # Try to find similar word
        similar = find_similar_word(word, tokenizer.word_index)
        if similar:
            result['suggested_similar'] = similar
    
    return jsonify(result)

@app.route('/health')
def health():
    """Health check endpoint."""
    print("\n📋 HEALTH CHECK CALLED")
    health_data = {
        'status': 'healthy',
        'model_loaded': model is not None,
        'tokenizer_loaded': tokenizer is not None,
        'vocabulary_size': len(tokenizer.word_index) if tokenizer else 0,
        'max_vocab_limit': MAX_VOCAB_SIZE
    }
    print(f"Health data: {health_data}\n")
    return jsonify(health_data)

@app.route('/debug_predict')
def debug_predict():
    """Test prediction with hardcoded text."""
    print("\n🧪 DEBUG PREDICT CALLED (no input needed)")
    
    if not model or not tokenizer:
        return jsonify({'error': 'Model or tokenizer not loaded'})
    
    # Use a simple test sentence
    test_text = "the quick brown"
    print(f"Using test text: '{test_text}'")
    
    try:
        cleaned_text = clean_text(test_text)
        processed_text = handle_oov_words(cleaned_text, tokenizer)
        print(f"Processed: '{processed_text}'")
        
        encoded = tokenizer.texts_to_sequences([processed_text])[0]
        print(f"Encoded: {encoded}")
        
        padded = pad_sequences([encoded], maxlen=sequence_len, padding='pre')
        print(f"Padded shape: {padded.shape}")
        
        probs = model.predict(padded, verbose=0)[0]
        print(f"Predictions shape: {probs.shape}")
        print(f"Top 5 indices: {np.argsort(probs)[-5:][::-1]}")
        print(f"Top 5 probs: {np.sort(probs)[-5:][::-1]}")
        
        top_words = []
        for idx in np.argsort(probs)[-5:][::-1]:
            if idx in tokenizer.index_word:
                word = tokenizer.index_word[idx]
                prob = float(probs[idx])
                top_words.append({'word': word, 'prob': prob})
                print(f"  - {word}: {prob:.4f}")
        
        return jsonify({'test_predictions': top_words})
    except Exception as e:
        print(f"ERROR in debug_predict: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    # Print startup info
    if tokenizer:
        print(f"\n🚀 AI Word Predictor Server Starting...")
        print(f"📚 Vocabulary Size: {len(tokenizer.word_index):,} words")
        print(f"🎯 Maximum Vocabulary Limit: {MAX_VOCAB_SIZE:,} words")
        print(f"🔢 Sequence Length: {sequence_len}")
        print(f"✅ Server ready at http://localhost:5000")
        print(f"📊 Vocab stats: http://localhost:5000/vocab_stats")
        print(f"❤️ Health check: http://localhost:5000/health\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
