# Step 0: Import Libraries
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import pickle
import re

# Step 1: Mount Google Drive and Load Data
from google.colab import drive
drive.mount('/content/drive')

file_path = '/content/drive/My Drive/engilsh_text_tranning_file.txt'

try:
    with open(file_path, 'r', encoding='utf-8') as file:
        text_data = file.read()
    print(f"\nData loaded successfully from Google Drive: {file_path}")
except FileNotFoundError:
    print(f"\nERROR: File not found at '{file_path}'.")
    exit()

# Step 2: Preprocess the Data
print("\n--- Starting Data Preprocessing ---")
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

cleaned_text = clean_text(text_data)
corpus = cleaned_text.split()
print(f"Total words in corpus: {len(corpus)}")

# Step 3: Create Sequences and Tokenize
tokenizer = Tokenizer()
tokenizer.fit_on_texts([corpus])
total_words = len(tokenizer.word_index) + 1
print(f"Total unique words (vocabulary size): {total_words}")

sequence_len = 50
input_sequences = []
for i in range(len(corpus) - sequence_len):
    seq = corpus[i:i + sequence_len + 1]
    input_sequences.append(' '.join(seq))

sequences_as_int = tokenizer.texts_to_sequences(input_sequences)
X = [seq[:-1] for seq in sequences_as_int]
y = [seq[-1] for seq in sequences_as_int]

X = pad_sequences(X, maxlen=sequence_len, padding='pre')
y = np.array(y)

print("\nData prepared for the model.")
print(f"Shape of X: {X.shape}")
print(f"Shape of y: {y.shape}")

# Step 4: Build the LSTM Model
print("\n--- Building the LSTM Model ---")
model = Sequential([
    Embedding(input_dim=total_words, output_dim=100, input_length=sequence_len),
    LSTM(150),
    Dense(total_words, activation='softmax')
])
model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.summary()

# Step 5: Train the Model
print("\n--- Starting Model Training ---")
print("This might take a while, have some patience...")
history = model.fit(X, y, epochs=50, batch_size=128, verbose=1)
print("\n--- Training Complete! ---")

# Step 6: Save the Trained Model and Tokenizer to Google Drive
print("\n--- Saving the model and tokenizer to Google Drive ---")
model.save('/content/drive/My Drive/next_word_lstm_model.h5')
with open('/content/drive/My Drive/tokenizer.pkl', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
print("\nModel and Tokenizer have been saved to your Google Drive.")

# Step 7: TESTING - Predict Next Word in a Paragraph
print("\n--- Starting Live Prediction Test ---")

def predict_next_word_in_paragraph(paragraph, model, tokenizer, sequence_len):
    print(f"\nTesting with paragraph: '{paragraph}'\n")
    words = paragraph.lower().split()

    for i in range(len(words)):
        current_sequence_text = ' '.join(words[:i+1])
        encoded_sequence = tokenizer.texts_to_sequences([current_sequence_text])[0]
        padded_sequence = pad_sequences([encoded_sequence], maxlen=sequence_len, padding='pre')
        predicted_word_index = np.argmax(model.predict(padded_sequence, verbose=0))
        predicted_word = tokenizer.index_word.get(predicted_word_index, '<unknown>')

        print(f"After '{words[i]}':")
        print(f"  Current sequence: '{current_sequence_text}' ---> Predicted next word: **{predicted_word}**\n")

# Test Paragraph
test_paragraph = "he was a man of great"
predict_next_word_in_paragraph(test_paragraph, model, tokenizer, sequence_len)