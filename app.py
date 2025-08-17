# app.py
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# 使用記憶體儲存（適合免費方案）
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
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.7; }
        }
        
        .connection-count {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 13px;
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
            animation: success 0.5s;
        }
        
        .share-button {
            background: linear-gradient(135deg, #ed8936, #dd6b20);
            color: white;
        }
        
        .share-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(237, 137, 54, 0.3);
        }
        
        @keyframes success {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
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
        
        .warning {
            background: #fff5f5;
            border: 1px solid #feb2b2;
            color: #c53030;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
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
        
        <div class="warning">
            ⚠️ 提醒：此為公開網址，請勿儲存敏感資料。伺服器重啟後資料會清空。
        </div>
        
        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span>雲端連線中</span>
            </div>
            <div class="connection-count">
                <span id="viewCount">1</span> 個裝置連線
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
    
    <div class="sync-badge" id="syncBadge">
        ✨ 已同步
    </div>
    
    <script>
        let currentVersion = {{ version }};
        let isTyping = false;
        let typingTimer;
        let saveTimer;
        const textArea = document.getElementById('textContent');
        const charCount = document.getElementById('charCount');
        const syncBadge = document.getElementById('syncBadge');
        
        // 初始化
        updateCharCount();
        updateViewCount();
        
        // 監聽輸入 - 防抖動儲存
        textArea.addEventListener('input', function() {
            isTyping = true;
            clearTimeout(typingTimer);
            clearTimeout(saveTimer);
            updateCharCount();
            
            // 300ms 後儲存
            saveTimer = setTimeout(() => {
                saveText();
            }, 300);
            
            // 1秒後解除輸入狀態
            typingTimer = setTimeout(() => {
                isTyping = false;
            }, 1000);
        });
        
        // 儲存文字
        function saveText() {
            const content = textArea.value;
            
            fetch('/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: content })
            })
            .then(response => response.json())
            .then(data => {
                currentVersion = data.version;
                showSyncBadge();
                updateLastUpdate(data.last_update);
            })
            .catch(error => {
                console.error('儲存失敗:', error);
            });
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
                    copyBtn.classList.add('copied');
                    copyBtnText.textContent = '已複製！';
                    setTimeout(() => {
                        copyBtn.classList.remove('copied');
                        copyBtnText.textContent = '複製全部文字';
                    }, 2000);
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
                }).catch(() => {
                    copyLink(url);
                });
            } else {
                copyLink(url);
            }
        }
        
        function copyLink(url) {
            navigator.clipboard.writeText(url)
                .then(() => {
                    alert('連結已複製！\n' + url);
                })
                .catch(() => {
                    prompt('複製此連結：', url);
                });
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
        
        // 更新最後更新時間
        function updateLastUpdate(time) {
            const lastUpdate = document.getElementById('lastUpdate');
            if (time) {
                lastUpdate.textContent = '最後更新: ' + time;
            }
        }
        
        // 更新連線數
        function updateViewCount() {
            fetch('/active-count')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('viewCount').textContent = data.count;
                });
        }
        
        // 自動同步 - 每1.5秒
        setInterval(() => {
            if (isTyping) return;
            
            fetch('/check-update')
                .then(response => response.json())
                .then(data => {
                    if (data.version !== currentVersion) {
                        currentVersion = data.version;
                        textArea.value = data.content;
                        updateCharCount();
                        updateLastUpdate(data.last_update);
                        showSyncBadge();
                    }
                });
        }, 1500);
        
        // 每5秒更新連線數
        setInterval(updateViewCount, 5000);
        
        // 頁面關閉前儲存
        window.addEventListener('beforeunload', function() {
            if (textArea.value) {
                navigator.sendBeacon('/save', JSON.stringify({ 
                    content: textArea.value 
                }));
            }
        });
    </script>
</body>
</html>
'''

# 追蹤活躍連線
active_connections = {}

@app.route('/')
def index():
    client_ip = request.remote_addr
    active_connections[client_ip] = datetime.now()
    
    # 清理超過10秒未活動的連線
    now = datetime.now()
    active_connections_copy = active_connections.copy()
    for ip, last_seen in active_connections_copy.items():
        if (now - last_seen).seconds > 10:
            del active_connections[ip]
    
    return render_template_string(
        HTML_TEMPLATE,
        content=text_storage['content'],
        last_update=text_storage['last_update'],
        version=text_storage['version']
    )

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    text_storage['content'] = data.get('content', '')
    text_storage['last_update'] = datetime.now().strftime('%m/%d %H:%M:%S')
    text_storage['version'] += 1
    
    return jsonify({
        'status': 'success',
        'version': text_storage['version'],
        'last_update': text_storage['last_update']
    })

@app.route('/check-update')
def check_update():
    client_ip = request.remote_addr
    active_connections[client_ip] = datetime.now()
    
    return jsonify({
        'content': text_storage['content'],
        'last_update': text_storage['last_update'],
        'version': text_storage['version']
    })

@app.route('/active-count')
def active_count():
    # 清理超過10秒未活動的連線
    now = datetime.now()
    active_connections_copy = active_connections.copy()
    for ip, last_seen in active_connections_copy.items():
        if (now - last_seen).seconds > 10:
            del active_connections[ip]
    
    return jsonify({'count': len(active_connections)})

if __name__ == '__main__':
    # Render 會設定 PORT 環境變數
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
