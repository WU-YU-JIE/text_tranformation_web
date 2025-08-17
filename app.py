# app.py
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import json

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 使用記憶體儲存
text_storage = {
    'content': '',
    'last_update': None,
    'version': 0
}

# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雲端文字傳輸平台</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft JhengHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            font-size: 14px;
        }
        
        .status-bar {
            background: linear-gradient(135deg, #f0f0f0, #e0e0e0);
            padding: 12px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }
        
        .status-dot.syncing {
            background: #FFC107;
        }
        
        .status-dot.error {
            background: #f44336;
            animation: none;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.7; }
        }
        
        textarea {
            width: 100%;
            min-height: 400px;
            padding: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 16px;
            line-height: 1.6;
            resize: vertical;
            transition: all 0.3s;
            font-family: inherit;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .button-container {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }
        
        button {
            padding: 15px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .copy-button {
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
        }
        
        .copy-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(72, 187, 120, 0.3);
        }
        
        .copy-button.copied {
            background: linear-gradient(135deg, #805ad5, #6b46c1);
        }
        
        .share-button {
            background: linear-gradient(135deg, #ed8936, #dd6b20);
            color: white;
        }
        
        .share-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(237, 137, 54, 0.3);
        }
        
        .info-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 14px;
            color: #666;
        }
        
        .char-count {
            font-weight: bold;
            color: #667eea;
        }
        
        .sync-badge {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 25px;
            font-size: 14px;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s;
            z-index: 1000;
        }
        
        .sync-badge.show {
            opacity: 1;
            transform: translateY(0);
        }
        
        .debug-info {
            position: fixed;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            font-family: monospace;
        }
        
        @media (max-width: 600px) {
            .button-container {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>☁️ 雲端文字傳輸平台</h1>
            <div class="subtitle">即時同步・全球訪問・免費使用</div>
        </div>
        
        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">連線中</span>
            </div>
            <div>
                版本: <span id="versionDisplay">{{ version }}</span>
            </div>
        </div>
        
        <textarea 
            id="textContent" 
            placeholder="在此輸入文字，將即時同步到所有連線的裝置..."
            spellcheck="false"
        >{{ content }}</textarea>
        
        <div class="button-container">
            <button class="copy-button" onclick="copyText()" id="copyBtn">
                <span>📋</span>
                <span id="copyBtnText">複製全部文字</span>
            </button>
            <button class="share-button" onclick="shareLink()">
                <span>🔗</span>
                <span>分享連結</span>
            </button>
        </div>
        
        <div class="info-bar">
            <div>
                字數: <span class="char-count" id="charCount">0</span>
            </div>
            <div id="lastUpdate">
                {% if last_update %}
                最後更新: {{ last_update }}
                {% endif %}
            </div>
        </div>
    </div>
    
    <div class="sync-badge" id="syncBadge">✨ 已同步</div>
    
    <!-- Debug 資訊 -->
    <div class="debug-info" id="debugInfo"></div>
    
    <script>
        let currentVersion = {{ version }};
        let isTyping = false;
        let typingTimer;
        let saveTimer;
        let syncFailCount = 0;
        
        const textArea = document.getElementById('textContent');
        const charCount = document.getElementById('charCount');
        const syncBadge = document.getElementById('syncBadge');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const debugInfo = document.getElementById('debugInfo');
        const versionDisplay = document.getElementById('versionDisplay');
        
        // 初始化
        updateCharCount();
        startSync();
        
        // 顯示 debug 資訊
        function updateDebug(msg) {
            debugInfo.textContent = `[${new Date().toLocaleTimeString()}] ${msg} | Ver: ${currentVersion}`;
        }
        
        // 監聽輸入
        textArea.addEventListener('input', function() {
            isTyping = true;
            clearTimeout(typingTimer);
            clearTimeout(saveTimer);
            updateCharCount();
            
            // 顯示同步中狀態
            statusDot.classList.add('syncing');
            statusText.textContent = '同步中...';
            
            // 立即儲存
            saveTimer = setTimeout(() => {
                saveText();
            }, 200);
            
            // 停止輸入後標記
            typingTimer = setTimeout(() => {
                isTyping = false;
            }, 1000);
        });
        
        // 儲存文字
        async function saveText() {
            try {
                const response = await fetch('/api/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        content: textArea.value,
                        version: currentVersion 
                    })
                });
                
                if (!response.ok) throw new Error('Save failed');
                
                const data = await response.json();
                currentVersion = data.version;
                versionDisplay.textContent = currentVersion;
                
                showSyncBadge();
                updateLastUpdate(data.last_update);
                updateDebug(`已儲存 v${currentVersion}`);
                
                // 恢復正常狀態
                statusDot.classList.remove('syncing', 'error');
                statusText.textContent = '已連線';
                syncFailCount = 0;
                
            } catch (error) {
                console.error('儲存失敗:', error);
                statusDot.classList.add('error');
                statusText.textContent = '儲存失敗';
                updateDebug('儲存失敗: ' + error.message);
            }
        }
        
        // 檢查更新
        async function checkUpdate() {
            if (isTyping) {
                updateDebug('輸入中，跳過同步');
                return;
            }
            
            try {
                const response = await fetch('/api/sync?v=' + currentVersion);
                
                if (!response.ok) throw new Error('Sync failed');
                
                const data = await response.json();
                
                if (data.version !== currentVersion) {
                    updateDebug(`發現新版本 v${data.version}`);
                    currentVersion = data.version;
                    versionDisplay.textContent = currentVersion;
                    
                    // 保存游標位置
                    const cursorPos = textArea.selectionStart;
                    const scrollPos = textArea.scrollTop;
                    
                    // 更新內容
                    textArea.value = data.content;
                    
                    // 恢復游標位置
                    if (!document.hasFocus() || document.activeElement !== textArea) {
                        textArea.selectionStart = cursorPos;
                        textArea.selectionEnd = cursorPos;
                        textArea.scrollTop = scrollPos;
                    }
                    
                    updateCharCount();
                    updateLastUpdate(data.last_update);
                    showSyncBadge();
                }
                
                // 更新狀態
                statusDot.classList.remove('error', 'syncing');
                statusText.textContent = '已連線';
                syncFailCount = 0;
                
            } catch (error) {
                syncFailCount++;
                console.error('同步失敗:', error);
                updateDebug('同步失敗 #' + syncFailCount);
                
                if (syncFailCount > 3) {
                    statusDot.classList.add('error');
                    statusText.textContent = '連線中斷';
                }
            }
        }
        
        // 開始同步循環
        function startSync() {
            setInterval(checkUpdate, 1000);  // 每秒檢查
            updateDebug('同步已啟動');
        }
        
        // 複製文字
        function copyText() {
            const copyBtn = document.getElementById('copyBtn');
            const copyBtnText = document.getElementById('copyBtnText');
            
            navigator.clipboard.writeText(textArea.value)
                .then(() => {
                    copyBtn.classList.add('copied');
                    copyBtnText.textContent = '已複製！';
                    setTimeout(() => {
                        copyBtn.classList.remove('copied');
                        copyBtnText.textContent = '複製全部文字';
                    }, 2000);
                })
                .catch(() => {
                    textArea.select();
                    document.execCommand('copy');
                });
        }
        
        // 分享連結
        function shareLink() {
            const url = window.location.href;
            
            if (navigator.share) {
                navigator.share({
                    title: '雲端文字傳輸平台',
                    text: '使用這個連結即時分享文字',
                    url: url
                });
            } else {
                navigator.clipboard.writeText(url).then(() => {
                    alert('連結已複製！');
                });
            }
        }
        
        // 更新字數
        function updateCharCount() {
            charCount.textContent = textArea.value.length.toLocaleString();
        }
        
        // 顯示同步標記
        function showSyncBadge() {
            syncBadge.classList.add('show');
            setTimeout(() => {
                syncBadge.classList.remove('show');
            }, 1500);
        }
        
        // 更新時間
        function updateLastUpdate(time) {
            const lastUpdate = document.getElementById('lastUpdate');
            if (time) {
                lastUpdate.textContent = '最後更新: ' + time;
            }
        }
        
        // 頁面關閉前儲存
        window.addEventListener('beforeunload', function() {
            if (textArea.value && textArea.value !== '') {
                navigator.sendBeacon('/api/save', JSON.stringify({ 
                    content: textArea.value,
                    version: currentVersion
                }));
            }
        });
        
        // 監測連線狀態
        window.addEventListener('online', () => {
            statusText.textContent = '重新連線中...';
            checkUpdate();
        });
        
        window.addEventListener('offline', () => {
            statusDot.classList.add('error');
            statusText.textContent = '離線';
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        content=text_storage['content'],
        last_update=text_storage['last_update'],
        version=text_storage['version']
    )

@app.route('/api/save', methods=['POST'])
def save():
    try:
        # 處理不同的 Content-Type
        if request.content_type == 'application/json':
            data = request.json
        else:
            data = json.loads(request.data)
        
        text_storage['content'] = data.get('content', '')
        text_storage['version'] += 1
        text_storage['last_update'] = datetime.now().strftime('%m/%d %H:%M:%S')
        
        print(f"[SAVE] Version {text_storage['version']}, {len(text_storage['content'])} chars")
        
        return jsonify({
            'status': 'success',
            'version': text_storage['version'],
            'last_update': text_storage['last_update']
        })
    except Exception as e:
        print(f"[ERROR] Save failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/sync')
def sync():
    try:
        client_version = request.args.get('v', 0, type=int)
        
        # 只在版本不同時回傳內容
        if client_version != text_storage['version']:
            print(f"[SYNC] Client v{client_version} -> Server v{text_storage['version']}")
        
        return jsonify({
            'content': text_storage['content'],
            'version': text_storage['version'],
            'last_update': text_storage['last_update']
        })
    except Exception as e:
        print(f"[ERROR] Sync failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'version': text_storage['version']})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
