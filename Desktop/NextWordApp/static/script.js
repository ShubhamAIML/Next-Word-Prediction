document.addEventListener('DOMContentLoaded', () => {
  const textInput       = document.getElementById('text-input');
  const predictionsCtl  = document.getElementById('predictions-container');
  const saveBtn         = document.getElementById('save-btn');
  const mdBtn           = document.getElementById('export-md');
  const pdfBtn          = document.getElementById('export-pdf');
  const micBtn          = document.getElementById('mic-btn');
  const themeToggle     = document.getElementById('theme-toggle');
  const statWords       = document.getElementById('stat-words');
  const statAccepted    = document.getElementById('stat-accepted');
  const statAccuracy    = document.getElementById('stat-accuracy');

  let debounceTimeout,
      currentPredictions = [],
      selectedIndex      = 0,
      isShowingGhost     = false,
      lastValue          = '',
      wordsCount         = 0,
      offered            = 0,
      accepted           = 0,
      recognition,
      isVoiceActive      = false,
      currentTheme       = localStorage.getItem('theme') || 'dark';

  /*── Theme Toggle ──────────────────────────*/
  const icons = { dark:'🌙', light:'☀️', copilot:'🤖' };
  document.body.setAttribute('data-theme', currentTheme);
  themeToggle.textContent = icons[currentTheme];
  themeToggle.onclick = () => {
    const order = ['dark','light','copilot'];
    currentTheme = order[(order.indexOf(currentTheme)+1)%3];
    document.body.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    themeToggle.textContent = icons[currentTheme];
  };

  /*── Enhanced Ghost Overlay Creation ───────────────*/
  (function(){
    if (document.getElementById('ghost-overlay')) return;
    const ov = document.createElement('div');
    ov.id = 'ghost-overlay';
    ov.style.cssText = `
      position:absolute; top:0; left:0;
      width:100%; height:100%;
      padding:20px; color:transparent;
      pointer-events:none; z-index:2;
      font-family:'JetBrains Mono',monospace;
      font-size:1rem; line-height:1.6;
      overflow:hidden; white-space:pre-wrap; word-wrap:break-word;
      box-sizing:border-box;
    `;
    textInput.parentNode.appendChild(ov);
  })();
  const ghostOverlay = document.getElementById('ghost-overlay');

  /*── Voice Recognition ─────────────────────*/
  if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
    recognition = new (window.SpeechRecognition||window.webkitSpeechRecognition)();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    micBtn.onclick = () => {
      if (!isVoiceActive) {
        isVoiceActive=true; micBtn.classList.add('active'); micBtn.textContent='⏹️';
        recognition.start();
      } else {
        isVoiceActive=false; micBtn.classList.remove('active'); micBtn.textContent='🎙️';
        recognition.stop();
      }
    };

    recognition.onresult = e => {
      let finalT='';
      for (let i=e.resultIndex;i<e.results.length;i++){
        const t=e.results[i][0].transcript;
        if (e.results[i].isFinal) finalT+=t;
      }
      if (finalT){
        const ct=textInput.value;
        const space=ct&& !ct.endsWith(' ') ? ' ' : '';
        textInput.value = ct+space+finalT+' ';
        updateStats();
        setTimeout(()=> getPredictions(textInput.value),100);
      }
    };
    recognition.onerror = err=>{
      if(isVoiceActive && err.error!=='no-speech') setTimeout(()=>recognition.start(),500);
    };
    recognition.onend = ()=> {
      if(isVoiceActive) recognition.start();
    };
  } else micBtn.style.display='none';

  /*── Stop voice on focus/click ─────────────*/
  textInput.addEventListener('focus', ()=>{ if(isVoiceActive) micBtn.click(); });
  textInput.addEventListener('click', ()=>{ if(isVoiceActive) micBtn.click(); updateGhostVisibility(); });

  /*── Update stats ──────────────────────────*/
  function updateStats(){
    const txt=textInput.value.trim();
    wordsCount = txt? txt.split(/\s+/).length:0;
    statWords.textContent = wordsCount;
    statAccepted.textContent = accepted;
    statAccuracy.textContent = offered? Math.round(accepted/offered*100)+'%':'0%';
  }

  /*── Input & Debounce ─────────────────────*/
  textInput.addEventListener('input', ()=>{
    clearTimeout(debounceTimeout);
    hideGhost();
    predictionsCtl.innerHTML=''; updateStats();
    lastValue = textInput.value;
    if (!lastValue.trim()) return;
    if (lastValue.endsWith(' ')) {
      debounceTimeout = setTimeout(()=> {
        if(textInput.value===lastValue) getPredictions(lastValue);
      },300);
    }
  });

  /*── Enhanced Scroll Sync ───────────────────────────*/
  textInput.addEventListener('scroll', ()=>{
    if (ghostOverlay) {
      ghostOverlay.scrollTop = textInput.scrollTop;
      ghostOverlay.scrollLeft = textInput.scrollLeft;
    }
    if (isShowingGhost) {
      updateGhost();
    }
  });

  /*── Keyboard nav & accept ─────────────────*/
  textInput.addEventListener('keydown', e=>{
    if(e.key==='Tab'&&isShowingGhost){e.preventDefault(); acceptGhost();}
    if(isShowingGhost && textInput.selectionStart===textInput.value.length){
      if(e.key==='ArrowRight'){ e.preventDefault(); selectedIndex=(selectedIndex+1)%currentPredictions.length; updateGhost(); highlightButtons(); }
      if(e.key==='ArrowLeft'){ e.preventDefault(); selectedIndex=(selectedIndex-1+currentPredictions.length)%currentPredictions.length; updateGhost(); highlightButtons(); }
    }
    if(e.key==='Escape') hideGhost();
    if(e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey) hideGhost();
  });
  textInput.addEventListener('keyup',e=>{
    if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(e.key)) updateGhostVisibility();
  });

  /*── Fetch Predictions ────────*/
  async function getPredictions(txt){
    hideGhost();
    try {
      const res = await fetch('/predict',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({text:txt})
      });
      const {predictions} = await res.json();
      currentPredictions=predictions||[];
      selectedIndex=0;
      if(currentPredictions.length){
        offered++;
        showGhost();
        renderButtons();
      }
    }catch(err){
      console.error('Prediction error:', err);
    }
  }

  /*── Enhanced Multi-line Ghost Positioning Functions ───────────────────────*/
  function showGhost(){
    if(!currentPredictions.length || textInput.selectionStart!==textInput.value.length) return;
    updateGhost(); isShowingGhost=true;
  }

  // Advanced function to check if suggestion needs new line
  function needsNewLine(currentText, suggestion) {
    const lines = currentText.split('\n');
    const lastLine = lines[lines.length - 1];
    
    // Check if last line has no spaces (continuous word)
    const hasNoSpaces = !lastLine.includes(' ');
    
    // Estimate character width based on textarea width and font
    const textareaStyles = window.getComputedStyle(textInput);
    const textareaWidth = textInput.clientWidth - (parseInt(textareaStyles.paddingLeft) + parseInt(textareaStyles.paddingRight));
    
    // Rough estimate: monospace font = ~0.6em per character
    const fontSize = parseInt(textareaStyles.fontSize);
    const charWidth = fontSize * 0.6; // Approximate character width
    const maxCharsPerLine = Math.floor(textareaWidth / charWidth);
    
    // Check if adding suggestion would exceed line limit
    const totalLineLength = lastLine.length + suggestion.length + 4; // +4 for "tab" text
    
    return hasNoSpaces && totalLineLength > maxCharsPerLine;
  }

  function updateGhost(){
    if(!currentPredictions.length) return;
    
    const currentText = textInput.value;
    const suggestion = currentPredictions[selectedIndex];
    
    // Sync scroll position first
    ghostOverlay.scrollTop = textInput.scrollTop;
    ghostOverlay.scrollLeft = textInput.scrollLeft;
    
    // Check if we need to move suggestion to new line
    const moveToNewLine = needsNewLine(currentText, suggestion);
    
    if (moveToNewLine) {
      // Add suggestion on new line
      ghostOverlay.innerHTML = `${currentText}\n<span id="ghost-suggestion" style="color: #666 !important; opacity: 0.7 !important; font-style: italic !important; background: rgba(0,212,255,0.05) !important; border-radius: 3px !important; padding: 0 2px !important;">${suggestion}<span class="ghost-tab-text" style="font-size: 0.6rem !important; opacity: 0.8 !important; margin-left: 6px !important; background: rgba(0,212,255,0.3) !important; border: 1px solid rgba(0,212,255,0.4) !important; padding: 1px 4px !important; border-radius: 2px !important; text-transform: lowercase !important;">tab</span></span>`;
    } else {
      // Add suggestion inline (original behavior)
      ghostOverlay.innerHTML = `${currentText}<span id="ghost-suggestion" style="color: #666 !important; opacity: 0.7 !important; font-style: italic !important; background: rgba(0,212,255,0.05) !important; border-radius: 3px !important; padding: 0 2px !important;">${suggestion}<span class="ghost-tab-text" style="font-size: 0.6rem !important; opacity: 0.8 !important; margin-left: 6px !important; background: rgba(0,212,255,0.3) !important; border: 1px solid rgba(0,212,255,0.4) !important; padding: 1px 4px !important; border-radius: 2px !important; text-transform: lowercase !important;">tab</span></span>`;
    }
    
    isShowingGhost = true;
  }

  function hideGhost(){
    ghostOverlay.innerHTML='';
    isShowingGhost=false;
    currentPredictions=[];
  }

  function updateGhostVisibility(){
    if(currentPredictions.length && textInput.selectionStart===textInput.value.length) {
      showGhost();
    } else {
      hideGhost();
    }
  }

  /*── Accept Ghost with New Line Support ──────────────────────────*/
  function acceptGhost(){
    if(!currentPredictions.length) return;
    
    const suggestion = currentPredictions[selectedIndex];
    const currentText = textInput.value;
    
    // Check if suggestion was on new line
    const wasOnNewLine = needsNewLine(currentText, suggestion);
    
    if (wasOnNewLine) {
      // Add suggestion with new line
      textInput.value = currentText + '\n' + suggestion + ' ';
    } else {
      // Add suggestion inline
      textInput.value = currentText + suggestion + ' ';
    }
    
    textInput.focus();
    accepted++;
    updateStats();
    hideGhost();
    setTimeout(()=> textInput.value.endsWith(' ') && getPredictions(textInput.value),100);
  }

  /*── Render Buttons ─────────────────────────*/
  function renderButtons(){
    predictionsCtl.innerHTML='';
    currentPredictions.forEach((w,i)=>{
      const btn=document.createElement('button');
      btn.className = i===selectedIndex?'prediction-btn selected':'prediction-btn';
      btn.innerHTML = `${w} ${i===selectedIndex?'<span class="tab-hint">tab</span>':''}`;
      btn.onclick = ()=>{ selectedIndex=i; updateGhost(); acceptGhost(); };
      predictionsCtl.appendChild(btn);
    });
  }

  function highlightButtons(){
    predictionsCtl.querySelectorAll('button').forEach((b,i)=> {
      b.className = i===selectedIndex?'prediction-btn selected':'prediction-btn';
      b.innerHTML = `${currentPredictions[i]} ${i===selectedIndex?'<span class="tab-hint">tab</span>':''}`;
    });
  }

  /*── Export Functions (unchanged) ────────────────────────────────*/
  function download(name,content,type='text/plain'){
    const blob=new Blob([content],{type});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url; a.download=name;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  }

  saveBtn.onclick = ()=>{
    const t=textInput.value.trim();
    if(!t)return alert('Write something first!');
    download(`ai-document-${Date.now()}.txt`,t);
    
    const original = saveBtn.innerHTML;
    saveBtn.innerHTML = '✅ Saved!';
    saveBtn.style.background = '#28a745';
    setTimeout(() => {
      saveBtn.innerHTML = original;
      saveBtn.style.background = '';
    }, 2000);
  };

  mdBtn.onclick = ()=>{
    const t=textInput.value.trim();
    if(!t)return alert('Write something first!');
    const content = `# AI Generated Document\n\n${t}\n\n---\n*Generated with AI Word Predictor on ${new Date().toLocaleDateString()}*`;
    download(`ai-document-${Date.now()}.md`, content);
    
    const original = mdBtn.innerHTML;
    mdBtn.innerHTML = '✅';
    setTimeout(() => {
      mdBtn.innerHTML = original;
    }, 1500);
  };

  pdfBtn.onclick = ()=>{
    const t=textInput.value.trim();
    if(!t)return alert('Write something first!');
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>AI Generated Document</title>
        <style>
          @page { margin: 2cm; }
          body {
            font-family: 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #000;
            background: #fff;
            margin: 0;
          }
          .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
          }
          .content {
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-bottom: 30px;
            text-align: justify;
          }
          .footer {
            position: fixed;
            bottom: 1cm;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 9pt;
            color: #666;
            border-top: 1px solid #ddd;
            padding-top: 10px;
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>AI Generated Document</h1>
          <p>Created on ${new Date().toLocaleDateString()}</p>
        </div>
        <div class="content">${t}</div>
        <div class="footer">Generated with AI Word Predictor</div>
        <script>
          window.onload = function() {
            setTimeout(function() {
              window.print();
              window.close();
            }, 500);
          }
        </script>
      </body>
      </html>
    `);
    printWindow.document.close();
    
    const original = pdfBtn.innerHTML;
    pdfBtn.innerHTML = '📄';
    pdfBtn.style.background = '#28a745';
    setTimeout(() => {
      pdfBtn.innerHTML = original;
      pdfBtn.style.background = '';
    }, 2000);
  };

  // Initialize
  updateStats();
});
