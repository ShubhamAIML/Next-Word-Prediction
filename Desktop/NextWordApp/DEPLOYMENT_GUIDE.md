# 🚀 Render Deployment Guide - AI Word Predictor

This guide walks you through deploying the Next Word Prediction App on Render.

---

## ✅ Pre-Deployment Checklist

- [x] **Procfile created** - Tells Render how to run your app
- [x] **requirements.txt updated** - All dependencies with pinned versions
- [x] **app.py configured** - Uses PORT environment variable
- [x] **.gitignore created** - Prevents unnecessary file uploads
- [x] **render.yaml ready** - Render configuration file

---

## 📋 Deployment Steps

### Step 1: Prepare Your Repository

1. **Initialize Git** (if not already done):
   ```bash
   cd NextWordApp
   git init
   git add .
   git commit -m "Initial commit - ready for Render deployment"
   ```

2. **Push to GitHub** (Render requires a GitHub repository):
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/NextWordApp.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. **Click "New +"** → Select **"Web Service"**
3. **Connect GitHub Repository**:
   - Select your `NextWordApp` repository
   - Allow Render to access your GitHub account

4. **Configure Web Service**:
   - **Name**: `next-word-predictor`
   - **Environment**: `Python 3.11`
   - **Region**: Choose closest region (e.g., Oregon, Frankfurt)
   - **Plan**: Free tier (or upgrade if needed)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

5. **Environment Variables** (optional, but recommended):
   - `PYTHON_VERSION`: `3.11`
   - Leave PORT unset (Render auto-assigns)

6. **Click "Create Web Service"**

### Step 3: Monitor Deployment

- Render will automatically:
  1. Clone your repository
  2. Install dependencies from `requirements.txt`
  3. Start your app using `gunicorn app:app`
  4. Assign a public URL (e.g., `https://next-word-predictor.onrender.com`)

- Watch the **Logs** tab to monitor:
  ```
  🚀 AI Word Predictor Server Starting...
  📚 Vocabulary Size: X words
  ✅ Server ready at http://0.0.0.0:PORT
  ```

---

## 🔧 Important Configuration Details

### Port Handling
- **Local Development**: App runs on port 5000
- **Render Production**: App auto-binds to Render's assigned PORT
- ✅ **Already configured** in `app.py` via `os.environ.get('PORT', 5000)`

### Model Files
- **Location**: `next_word_lstm_model.h5` and `tokenizer.pkl` must be in root directory
- **Size**: Render free tier has 500MB storage limit
  - Model + tokenizer typically ~100-200MB
  - If too large, consider:
    - Model optimization (quantization)
    - Cloud storage (AWS S3, Google Cloud Storage)

### Free Tier Limitations
- **RAM**: 512 MB
- **Storage**: 500 MB
- **Execution Time**: No limitations
- **Sleep**: Spins down after 15 minutes of inactivity (respins on request)

---

## 🐛 Troubleshooting

### Issue: `ModuleNotFoundError` for tensorflow
**Solution**: TensorFlow with CPU support is ~500MB. If deployment fails:
```bash
pip install tensorflow-cpu  # Lighter alternative
```

Update `requirements.txt`:
```
Flask==2.3.3
tensorflow-cpu==2.13.0  # Instead of tensorflow
numpy==1.24.3
gunicorn==21.2.0
```

### Issue: Deployment timeout
**Solution**: Free tier builds can take 10-15 minutes. Be patient and check logs.

### Issue: 500 Internal Server Error
**Check Logs**:
1. Go to **Render Dashboard** → Your Service → **Logs**
2. Look for error messages
3. Common causes:
   - Missing model file (`next_word_lstm_model.h5`)
   - Missing tokenizer (`tokenizer.pkl`)
   - TensorFlow version incompatibility

### Issue: Model files not found
**Solution**: Ensure files are committed to Git:
```bash
git add next_word_lstm_model.h5
git add tokenizer.pkl
git commit -m "Add model files"
git push
```

---

## 📊 Deployment Success Indicators

✅ Green "Active" status in Render Dashboard
✅ No errors in deployment logs
✅ App responds to requests:
```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "Server is running",
  "model_loaded": true,
  "tokenizer_loaded": true
}
```

---

## 🔗 Useful Links

- [Render Documentation](https://render.com/docs)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [TensorFlow Lite (for optimization)](https://www.tensorflow.org/lite/guide)

---

## 💡 Next Steps After Deployment

1. **Add Custom Domain** (Render → Settings → Custom Domain)
2. **Enable Auto-Deploy** (GitHub → Render auto-redeploy on push)
3. **Monitor Performance** (Render Dashboard → Metrics)
4. **Set Up Alerts** (Render → Settings → Alerts)

---

**Happy Deploying! 🎉**
