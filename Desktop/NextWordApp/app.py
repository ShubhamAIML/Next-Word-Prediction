import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from flask import Flask, render_template, request, jsonify
import tensorflow as tf
import numpy as np
import pickle
import re
from tensorflow.keras.preprocessing.sequence import pad_sequences

app = Flask(__name__)

# Set vocabulary limit
MAX_VOCAB_SIZE = 40000
sequence_len = 50

# Get port from environment variable (Render requirement)
port = int(os.environ.get('PORT', 5000))

# Get the app directory for proper file loading
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(APP_DIR, 'next_word_lstm_model.h5')
TOKENIZER_PATH = os.path.join(APP_DIR, 'tokenizer.pkl')

print(f"🔍 App Directory: {APP_DIR}")
print(f"🔍 Model Path: {MODEL_PATH} - Exists: {os.path.exists(MODEL_PATH)}")
print(f"🔍 Tokenizer Path: {TOKENIZER_PATH} - Exists: {os.path.exists(TOKENIZER_PATH)}")

# Load model and tokenizer with vocab limit
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    if not os.path.exists(TOKENIZER_PATH):
        raise FileNotFoundError(f"Tokenizer file not found at {TOKENIZER_PATH}")
    
    model = tf.keras.models.load_model(MODEL_PATH)
    
    with open(TOKENIZER_PATH, 'rb') as handle:
        tokenizer = pickle.load(handle)
    
    # Limit vocabulary to top 40K most frequent words
    original_vocab_size = len(tokenizer.word_index)
    
    if original_vocab_size > MAX_VOCAB_SIZE:
        print(f"Original vocabulary: {original_vocab_size} words")
        print(f"Limiting to top {MAX_VOCAB_SIZE} most frequent words...")
        
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
        
        print(f"Vocabulary limited to {len(tokenizer.word_index)} words")
    
    print(f"✅ Model and tokenizer loaded successfully!")
    print(f"✅ Final vocabulary size: {len(tokenizer.word_index)} words")
    print(f"✅ Model input shape: {model.input_shape}")
    
except FileNotFoundError as e:
    print(f"❌ FILE NOT FOUND ERROR: {e}")
    print(f"❌ Make sure next_word_lstm_model.h5 and tokenizer.pkl are in the root directory!")
    print(f"❌ App Directory: {APP_DIR}")
    print(f"❌ Files in directory: {os.listdir(APP_DIR)}")
    model = None
    tokenizer = None
except Exception as e:
    print(f"❌ ERROR loading model or tokenizer: {e}")
    import traceback
    traceback.print_exc()
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

@app.route('/debug')
def debug():
    """Debug page to check model and tokenizer status."""
    return render_template('debug.html', 
                         model_loaded=model is not None,
                         tokenizer_loaded=tokenizer is not None,
                         vocab_size=len(tokenizer.word_index) if tokenizer else 0,
                         app_dir=APP_DIR)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if not model or not tokenizer:
        return jsonify({'error': 'Model or tokenizer not loaded.'})

    data = request.get_json()
    seed_text = data.get('text', '')

    if not seed_text.strip():
        return jsonify({'predictions': []})

    try:
        # Clean and preprocess text
        cleaned_seed_text = clean_text(seed_text)
        
        if not cleaned_seed_text:
            return jsonify({'predictions': []})
        
        # Handle OOV words
        processed_text = handle_oov_words(cleaned_seed_text, tokenizer)
        
        if not processed_text:
            # Fallback to common words if all words are OOV
            common_words = ['the', 'and', 'to', 'of']
            return jsonify({'predictions': common_words})
        
        # Convert to sequences
        encoded_sequence = tokenizer.texts_to_sequences([processed_text])[0]
        
        if not encoded_sequence:
            return jsonify({'predictions': []})
        
        # Pad sequence
        padded_sequence = pad_sequences([encoded_sequence], maxlen=sequence_len, padding='pre')
        
        # Get predictions
        y_pred_probs = model.predict(padded_sequence, verbose=0)[0]
        
        # Get top predictions with enhanced filtering
        top_predictions = get_top_predictions(y_pred_probs, tokenizer, top_k=8)
        
        # Extract just the words for the response
        predictions = [pred['word'] for pred in top_predictions[:4]]
        
        # Ensure we have at least some predictions
        if not predictions:
            fallback_words = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it']
            predictions = fallback_words[:4]
        
        return jsonify({
            'predictions': predictions,
            'vocab_size': len(tokenizer.word_index),
            'processed_input_words': len(processed_text.split())
        })
        
    except Exception as e:
        print(f"Prediction error: {e}")
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
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'tokenizer_loaded': tokenizer is not None,
        'vocabulary_size': len(tokenizer.word_index) if tokenizer else 0,
        'max_vocab_limit': MAX_VOCAB_SIZE
    })

if __name__ == '__main__':
    # Print startup info
    if tokenizer:
        print(f"\n🚀 AI Word Predictor Server Starting...")
        print(f"📚 Vocabulary Size: {len(tokenizer.word_index):,} words")
        print(f"🎯 Maximum Vocabulary Limit: {MAX_VOCAB_SIZE:,} words")
        print(f"🔢 Sequence Length: {sequence_len}")
        print(f"✅ Server ready at http://localhost:{port}")
        print(f"📊 Vocab stats: http://localhost:{port}/vocab_stats")
        print(f"❤️ Health check: http://localhost:{port}/health\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
