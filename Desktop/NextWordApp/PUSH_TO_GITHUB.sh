#!/bin/bash
# NextWordApp - GitHub Push Instructions
# Terminal mein ye commands run karo (apna GitHub URL daalna)

# Step 1: Add GitHub as remote
# git remote add origin https://github.com/YOUR_USERNAME/NextWordApp.git

# Step 2: Rename branch to main (agar chahiye)
# git branch -M main

# Step 3: Push code to GitHub
# git push -u origin master

# Example with actual URL:
# git remote add origin https://github.com/yourname/NextWordApp.git
# git push -u origin master

# Phir GitHub par apni repository mein dekho:
# - model file ✓
# - tokenizer file ✓  
# - Flask app ✓
# Sab upload hona chahiye

# Agar error aaye "authentication failed":
# 1. GitHub Token generate karo: Settings > Developer settings > Personal access tokens
# 2. Terminal mein username aur token se login karo
# 3. Push karo
