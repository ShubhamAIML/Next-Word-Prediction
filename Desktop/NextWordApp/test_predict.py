import tensorflow as tf
import pickle
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re

# Load model and tokenizer
print('Loading model and tokenizer...')
model = tf.keras.models.load_model('next_word_lstm_model.h5')
with open('tokenizer.pkl', 'rb') as f:
    tokenizer = pickle.load(f)

sequence_len = 50

def clean_text(text):
    """Clean text exactly like during training."""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Test prediction
test_inputs = [
    "the quick brown",
    "hello world",
    "i love machine",
    "artificial intelligence is"
]

print('\n' + '='*60)
print('🧪 TESTING PREDICTIONS')
print('='*60)

for test_text in test_inputs:
    print(f'\nInput: "{test_text}"')
    
    # Clean text
    cleaned = clean_text(test_text)
    print(f'Cleaned: "{cleaned}"')
    
    # Tokenize
    encoded = tokenizer.texts_to_sequences([cleaned])[0]
    print(f'Encoded: {encoded}')
    
    # Pad
    padded = pad_sequences([encoded], maxlen=sequence_len, padding='pre')
    
    # Predict
    predictions = model.predict(padded, verbose=0)[0]
    
    # Get top 5
    top_indices = np.argsort(predictions)[-5:][::-1]
    print('Top predictions:')
    for idx in top_indices:
        if idx in tokenizer.index_word:
            word = tokenizer.index_word[idx]
            prob = predictions[idx]
            print(f'  - {word}: {prob:.4f}')

print('\n' + '='*60)
print('✅ PREDICTION TEST COMPLETE!')
print('='*60)
