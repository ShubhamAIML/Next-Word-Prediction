import tensorflow as tf
import pickle
import os

print('🔍 Checking files...')
print(f'Model exists: {os.path.exists("next_word_lstm_model.h5")}')
print(f'Tokenizer exists: {os.path.exists("tokenizer.pkl")}')

print('\n📦 Loading model...')
try:
    model = tf.keras.models.load_model('next_word_lstm_model.h5')
    print(f'✅ Model loaded successfully')
except Exception as e:
    print(f'❌ Error loading model: {e}')
    exit(1)

print('\n🔤 Loading tokenizer...')
try:
    with open('tokenizer.pkl', 'rb') as f:
        tokenizer = pickle.load(f)
    print(f'✅ Tokenizer loaded successfully')
    print(f'   Vocab size: {len(tokenizer.word_index)}')
except Exception as e:
    print(f'❌ Error loading tokenizer: {e}')
    exit(1)

print('\n✅ All files loaded successfully!')
print(f'📊 Model ready for predictions')
print(f'   Input shape: {model.input_shape}')
print(f'   Output shape: {model.output_shape}')
