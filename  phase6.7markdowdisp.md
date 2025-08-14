# 1. Markdownライブラリの導入
## 推奨：marked.js（軽量・高速）
HTMLの<head>セクションに追加：
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

# 2. 結果表示部分の修正
## 現在の観光アナライザーの結果表示関数を以下のように変更：
// 結果表示関数（Markdown対応版）
function displayAnalysisResult(response) {
    const resultContainer = document.getElementById('resultContainer');
    const analysisResult = document.getElementById('analysisResult');
    
    if (response.analysis) {
        // Markdownをパースして表示
        const parsedMarkdown = marked.parse(response.analysis);
        analysisResult.innerHTML = parsedMarkdown;
        
        // 結果コンテナを表示
        resultContainer.style.display = 'block';
        resultContainer.scrollIntoView({ behavior: 'smooth' });
        
        console.log('✅ 解析結果をMarkdown形式で表示しました');
    } else {
        showMessage('解析結果が取得できませんでした', 'error');
    }
}

// 設定でMarkedのオプションをカスタマイズ
marked.setOptions({
    breaks: true,        // 改行を<br>に変換
    gfm: true,          // GitHub Flavored Markdown有効
    headerIds: false,   // ヘッダーIDを生成しない
    mangle: false,      // emailアドレスの自動リンクを無効
    sanitize: false     // HTMLサニタイズ（XSS対策は別途実装）
});

// より高度な設定（必要に応じて）
const renderer = new marked.Renderer();

// カスタムリンクレンダリング（外部リンクは新しいタブで開く）
renderer.link = function(href, title, text) {
    const isExternal = href.startsWith('http');
    const target = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';
    const titleAttr = title ? ` title="${title}"` : '';
    return `<a href="${href}"${titleAttr}${target}>${text}</a>`;
};

// カスタムテーブルスタイリング
renderer.table = function(header, body) {
    return `<div class="table-container">
        <table class="markdown-table">
            <thead>${header}</thead>
            <tbody>${body}</tbody>
        </table>
    </div>`;
};

marked.setOptions({ renderer });

#3. MarkdownスタイリングのCSS追加
/* Markdown表示用スタイル */
#analysisResult {
    line-height: 1.7;
    color: #333;
    font-size: 15px;
}

/* ヘッダー */
#analysisResult h1 {
    font-size: 1.8em;
    color: #2196F3;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 8px;
    margin: 24px 0 16px 0;
    font-weight: 600;
}

#analysisResult h2 {
    font-size: 1.5em;
    color: #1976D2;
    margin: 20px 0 12px 0;
    font-weight: 600;
}

#analysisResult h3 {
    font-size: 1.3em;
    color: #1565C0;
    margin: 16px 0 10px 0;
    font-weight: 500;
}

/* 太字・斜体 */
#analysisResult strong {
    font-weight: 600;
    color: #1976D2;
}

#analysisResult em {
    font-style: italic;
    color: #555;
}

/* リスト */
#analysisResult ul, 
#analysisResult ol {
    padding-left: 20px;
    margin: 12px 0;
}

#analysisResult li {
    margin: 6px 0;
    line-height: 1.6;
}

/* 箇条書きのアイコンカスタマイズ */
#analysisResult ul li::marker {
    content: "🔹 ";
}

/* コード */
#analysisResult code {
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.9em;
    color: #d73a49;
}

#analysisResult pre {
    background: #f8f9fa;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    margin: 16px 0;
}

#analysisResult pre code {
    background: none;
    padding: 0;
    color: #24292e;
}

/* 引用 */
#analysisResult blockquote {
    border-left: 4px solid #2196F3;
    background: #f8f9ff;
    margin: 16px 0;
    padding: 12px 20px;
    font-style: italic;
    color: #555;
}

/* テーブル */
.table-container {
    overflow-x: auto;
    margin: 16px 0;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}

.markdown-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    font-size: 14px;
}

.markdown-table th {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    border: none;
}

.markdown-table td {
    padding: 12px 16px;
    border-bottom: 1px solid #e0e0e0;
    vertical-align: top;
}

.markdown-table tr:nth-child(even) {
    background: #f8f9fa;
}

.markdown-table tr:hover {
    background: #e3f2fd;
}

/* リンク */
#analysisResult a {
    color: #2196F3;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: all 0.2s ease;
}

#analysisResult a:hover {
    border-bottom-color: #2196F3;
    background: rgba(33, 150, 243, 0.1);
    padding: 0 2px;
    border-radius: 2px;
}

/* 画像 */
#analysisResult img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin: 12px 0;
}

/* 区切り線 */
#analysisResult hr {
    border: none;
    height: 2px;
    background: linear-gradient(to right, transparent, #2196F3, transparent);
    margin: 24px 0;
}

/* モバイル対応 */
@media (max-width: 768px) {
    #analysisResult {
        font-size: 14px;
    }
    
    #analysisResult h1 {
        font-size: 1.6em;
    }
    
    #analysisResult h2 {
        font-size: 1.4em;
    }
    
    .markdown-table {
        font-size: 12px;
    }
    
    .markdown-table th,
    .markdown-table td {
        padding: 8px 12px;
    }
}

# 4.セキュリティ対策
XSS攻撃を防ぐため、DOMPurifyも併用することを推奨：
<script src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"></script>
