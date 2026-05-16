FROM python:3.11-slim

WORKDIR /app

# Install git and git-lfs
RUN apt-get update && apt-get install -y git git-lfs curl && rm -rf /var/lib/apt/lists/*

# Initialize git-lfs
RUN git lfs install --system

# Copy all files from build context
COPY app.py .
COPY next_word_lstm_model.h5 .
COPY tokenizer.pkl .
COPY .gitattributes .
COPY templates/ templates/
COPY static/ static/
COPY Dataset/ Dataset/

# Debug: Check file sizes
RUN echo "=== Checking file sizes ===" && \
    ls -lh next_word_lstm_model.h5 tokenizer.pkl && \
    echo "=== Checking if files are LFS pointers ===" && \
    head -c 50 next_word_lstm_model.h5 && echo && \
    head -c 50 tokenizer.pkl && echo

# Install Python dependencies
RUN pip install --no-cache-dir \
    Flask==3.0.0 \
    tensorflow==2.15.0 \
    numpy==1.24.3 \
    gunicorn==21.2.0

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "app:app"]
