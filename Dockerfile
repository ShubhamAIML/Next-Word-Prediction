FROM python:3.11-slim

WORKDIR /app

# Copy all files
COPY app.py .
COPY next_word_lstm_model.h5 .
COPY tokenizer.pkl .
COPY templates/ templates/
COPY static/ static/

# Install dependencies directly (no requirements.txt needed)
RUN pip install --no-cache-dir Flask==3.0.0 tensorflow==2.15.0 numpy==1.24.3 gunicorn==21.2.0

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "app:app"]
