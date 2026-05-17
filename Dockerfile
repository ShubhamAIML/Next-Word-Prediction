FROM python:3.11-slim

WORKDIR /app

# Install git (for potential fallback operations)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY app.py .
COPY next_word_lstm_model.h5 .
COPY tokenizer.pkl .
COPY templates/ templates/
COPY static/ static/
COPY Dataset/ Dataset/

# Install Python dependencies
RUN pip install --no-cache-dir \
    Flask==3.0.0 \
    tensorflow==2.14.0 \
    numpy==1.24.3 \
    gunicorn==21.2.0

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health', timeout=10)" || exit 1

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "180", "app:app"]
