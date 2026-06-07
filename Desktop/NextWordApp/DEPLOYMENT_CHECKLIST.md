# 🚀 Deployment Checklist

## ✅ Required Files for Deployment

These files MUST be present in your repository for the app to work:

### Model & Data Files
- [x] `next_word_lstm_model.h5` - LSTM model file (~required for predictions)
- [x] `tokenizer.pkl` - Pickle file with word tokenizer (~required for text processing)

### Python Files
- [x] `app.py` - Main Flask application
- [x] `requirements.txt` - Python dependencies
- [x] `runtime.txt` - Python version specification
- [x] `Procfile` or `render.yaml` - Deployment configuration

### Template & Static Files
- [x] `templates/index.html` - Main HTML page
- [x] `templates/debug.html` - Debug/health check page
- [x] `static/script.js` - Frontend JavaScript
- [x] `static/style.css` - Frontend styling

## 🔍 How to Check if Files are Tracked

Run these commands in your terminal:

```bash
# Check if model file is tracked
git ls-files | grep next_word_lstm_model.h5

# Check if tokenizer file is tracked
git ls-files | grep tokenizer.pkl

# Check git status
git status
```

## ⚠️ If Files Are NOT Showing

Your model and tokenizer files might be in `.gitignore`. This will break deployment!

### Fix 1: Remove from .gitignore (if they're there)
Edit `.gitignore` and remove or comment out lines that exclude these files:
```
# Remove this if present:
# next_word_lstm_model.h5
# tokenizer.pkl
```

### Fix 2: Force Add Files to Git
```bash
git add -f next_word_lstm_model.h5
git add -f tokenizer.pkl
git commit -m "Add model and tokenizer files"
git push
```

### Fix 3: Check File Sizes
If your files are too large for GitHub (>100MB), you may need:
- **Option A**: Use Git LFS (Large File Storage)
  ```bash
  git lfs install
  git lfs track "*.h5"
  git lfs track "*.pkl"
  git add .gitattributes
  git commit -m "Setup Git LFS for large files"
  ```
- **Option B**: Use a deployment environment that can download files from elsewhere

## 🌐 Render.io Deployment Steps

1. Push your code to GitHub (including model and tokenizer files)
2. Connect your GitHub repo to Render
3. Create a new Web Service:
   - Name: `next-word-predictor`
   - Runtime: Python 3.11
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 120 app:app`
4. Set Environment Variables:
   - `PYTHON_VERSION`: 3.11
   - `PORT`: (auto)
5. Deploy!

## 🧪 Testing After Deployment

Once deployed, test these URLs:

1. **Main App**: `https://your-app-name.onrender.com/`
2. **Debug Panel**: `https://your-app-name.onrender.com/debug`
3. **Health Check**: `https://your-app-name.onrender.com/health`
4. **Vocab Stats**: `https://your-app-name.onrender.com/vocab_stats`

## 🐛 Troubleshooting

### "Model or tokenizer not loaded"
- Check the debug page: `/debug`
- The model or tokenizer files are missing in deployment
- Ensure both files are tracked in Git and pushed

### "Predictions not working"
- Visit `/health` endpoint to check status
- Test with `/test_word/the` to check if tokenizer works
- Check server logs for errors

### "Files too large for deployment"
- Use Git LFS for files > 100MB
- Or upload model files separately and download them during app startup

## 📦 Requirements.txt Dependencies

Make sure all these are in `requirements.txt`:
- Flask==2.3.3
- tensorflow==2.13.0
- numpy==1.24.3
- gunicorn==21.2.0
- Werkzeug==2.3.7

## 🎯 Quick Fix Summary

If predictions aren't working after deployment:

```bash
# 1. Check if files are tracked
git ls-files | grep -E "(model|tokenizer)"

# 2. If not tracked, force add them
git add -f *.h5 *.pkl
git commit -m "Add model files"
git push

# 3. Redeploy on Render (manual or via git push)
```

That's it! Your app should work now. 🚀
