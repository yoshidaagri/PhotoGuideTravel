/**
 * Main Application Module for Tourism Analyzer v1.3
 * メインアプリケーション機能
 */

// API Configuration
const API_BASE_URL = 'https://f4n095fm2j.execute-api.ap-northeast-1.amazonaws.com/dev';

// Global variables
let currentFile = null;
let isAnalyzing = false;
let selectedLanguage = 'ja';
let selectedAnalysisType = 'store';
let eventListenersSetup = false; // イベントリスナー重複防止フラグ

/**
 * Initialize main application after authentication
 * 認証後のメインアプリケーション初期化
 */
function initializeMainApplication() {
    console.log('🎯 Initializing main application features...');
    
    try {
        // Check for payment result from URL parameters
        checkPaymentResult();
        // Initialize UI elements
        initializeUI();
        
        // Set up event listeners
        setupEventListeners();
        
        // Initialize language
        initializeLanguage();
        
        // Load saved location settings
        loadLocationSettings();
        
        // Initialize Stripe if needed
        initializeStripe();
        
        // Setup Markdown processing
        initializeMarkdown();
        
        console.log('✅ Main application initialized successfully');
        
    } catch (error) {
        console.error('🚨 Error initializing main application:', error);
        showMessage('アプリケーションの初期化に失敗しました', 'error');
    }
}

/**
 * Initialize UI elements and their states
 * UI要素と状態の初期化
 */
function initializeUI() {
    // Get UI elements
    const uploadSection = document.getElementById('uploadSection');
    const imageInput = document.getElementById('imageInput');
    const previewSection = document.getElementById('previewSection');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    
    // Set initial states with proper hidden class management
    if (previewSection) {
        previewSection.style.display = 'none';
        previewSection.classList.add('hidden');
    }
    if (loadingSection) {
        loadingSection.style.display = 'none';
        loadingSection.classList.add('hidden');
        console.log('🔍 Debug: Loading section initial classes:', loadingSection.className);
    }
    if (resultsSection) {
        resultsSection.style.display = 'none';
        resultsSection.classList.add('hidden');
    }
    
    console.log('🎨 UI elements initialized');
    console.log('🔍 Debug: Elements found in initializeUI:', {
        uploadSection: !!uploadSection,
        imageInput: !!imageInput,
        previewSection: !!previewSection,
        loadingSection: !!loadingSection,
        resultsSection: !!resultsSection
    });
}

/**
 * Setup event listeners for user interactions
 * ユーザーインタラクション用イベントリスナー設定
 */
function setupEventListeners() {
    // 重複登録を防ぐ
    if (eventListenersSetup) {
        console.log('⚠️ Event listeners already set up, skipping...');
        return;
    }
    
    // File upload listeners
    const uploadSection = document.getElementById('uploadSection');
    const imageInput = document.getElementById('imageInput');
    
    console.log('🔍 Debug: Setting up event listeners...', {
        uploadSection: !!uploadSection,
        imageInput: !!imageInput
    });
    
    if (uploadSection && imageInput) {
        uploadSection.addEventListener('click', () => imageInput.click());
        uploadSection.addEventListener('dragover', handleDragOver);
        uploadSection.addEventListener('dragleave', handleDragLeave);
        uploadSection.addEventListener('drop', handleDrop);
        imageInput.addEventListener('change', handleFileSelect);
        console.log('✅ Debug: Upload event listeners set up successfully');
    } else {
        console.error('🚨 Debug: Could not set up upload event listeners!');
    }
    
    // Language selection listeners
    const languageOptions = document.querySelectorAll('input[name="language"]');
    languageOptions.forEach(option => {
        option.addEventListener('change', handleLanguageChange);
    });
    
    // Analysis type selection listeners
    const analysisTypeOptions = document.querySelectorAll('input[name="analysisType"]');
    analysisTypeOptions.forEach(option => {
        option.addEventListener('change', handleAnalysisTypeChange);
    });
    
    // Analysis button listener
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', handleAnalyzeClick);
    }
    
    // New analysis button listener
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', handleNewAnalysisClick);
    }
    
    // フラグを設定して重複を防ぐ
    eventListenersSetup = true;
    console.log('🔗 Event listeners set up (once only)');
}

/**
 * Initialize language settings
 * 言語設定初期化
 */
function initializeLanguage() {
    const savedLanguage = getCurrentLanguage();
    selectedLanguage = savedLanguage;
    
    // Update language radio button
    const languageOption = document.querySelector(`input[name="language"][value="${savedLanguage}"]`);
    if (languageOption) {
        languageOption.checked = true;
    }
    
    // Update UI language
    updateLanguageUI(savedLanguage);
    
    console.log(`🌐 Language initialized: ${savedLanguage}`);
}

/**
 * Handle language change
 * 言語変更処理
 */
function handleLanguageChange(event) {
    selectedLanguage = event.target.value;
    updateLanguageUI(selectedLanguage);
    console.log(`🌐 Language changed to: ${selectedLanguage}`);
}

/**
 * Handle analysis type change
 * 解析タイプ変更処理
 */
function handleAnalysisTypeChange(event) {
    selectedAnalysisType = event.target.value;
    console.log(`🔍 Analysis type changed to: ${selectedAnalysisType}`);
}

/**
 * Handle file selection
 * ファイル選択処理
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    console.log('📁 File selected:', file ? file.name : 'No file');
    
    if (file) {
        processFile(file);
        // ファイル選択後にinputをクリアして重複を防ぐ
        event.target.value = '';
        console.log('🧹 File input cleared to prevent duplicate selection');
    }
}

/**
 * Handle drag over event
 * ドラッグオーバーイベント処理
 */
function handleDragOver(event) {
    event.preventDefault();
    const uploadSection = document.getElementById('uploadSection');
    if (uploadSection) {
        uploadSection.classList.add('dragover');
    }
}

/**
 * Handle drag leave event
 * ドラッグ離脱イベント処理
 */
function handleDragLeave(event) {
    event.preventDefault();
    const uploadSection = document.getElementById('uploadSection');
    if (uploadSection) {
        uploadSection.classList.remove('dragover');
    }
}

/**
 * Handle file drop event
 * ファイルドロップイベント処理
 */
function handleDrop(event) {
    event.preventDefault();
    const uploadSection = document.getElementById('uploadSection');
    if (uploadSection) {
        uploadSection.classList.remove('dragover');
    }
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

/**
 * Process uploaded file
 * アップロードファイル処理
 */
function processFile(file) {
    console.log('📁 Processing file:', file.name);
    
    // Validate file
    if (!validateFile(file)) {
        return;
    }
    
    currentFile = file;
    
    // Show preview
    showImagePreview(file);
}

/**
 * Validate uploaded file
 * アップロードファイル検証
 */
function validateFile(file) {
    // Check file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        showMessage('JPG、PNG、GIF形式の画像ファイルを選択してください', 'error');
        return false;
    }
    
    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showMessage('ファイルサイズが10MBを超えています', 'error');
        return false;
    }
    
    return true;
}

/**
 * Show image preview
 * 画像プレビュー表示
 */
function showImagePreview(file) {
    const previewSection = document.getElementById('previewSection');
    const previewImage = document.getElementById('previewImage');
    const imageDetails = document.getElementById('imageDetails'); // 正しいIDに修正
    
    console.log('🔍 Debug: Preview elements check:', {
        previewSection: !!previewSection,
        previewImage: !!previewImage,
        imageDetails: !!imageDetails
    });
    
    if (!previewSection || !previewImage || !imageDetails) {
        console.error('Preview elements not found');
        console.error('Missing elements:', {
            previewSection: !previewSection,
            previewImage: !previewImage,
            imageDetails: !imageDetails
        });
        return;
    }
    
    // Create file reader
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        imageDetails.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`; // imageDetailsに修正
        previewSection.style.display = 'block';
        previewSection.classList.remove('hidden'); // hiddenクラスも削除
        
        console.log('✅ Image preview displayed successfully');
        
        // Scroll to preview
        previewSection.scrollIntoView({ behavior: 'smooth' });
    };
    reader.readAsDataURL(file);
}

/**
 * Handle analyze button click
 * 解析ボタンクリック処理
 */
async function handleAnalyzeClick() {
    if (!currentFile || isAnalyzing) {
        return;
    }
    
    console.log('🔍 Starting image analysis...');
    
    // Debug: Check authentication status
    const token = getAuthToken();
    const userInfo = localStorage.getItem('userInfo');
    console.log('🔐 Debug auth status:', {
        hasToken: !!token,
        tokenLength: token ? token.length : 0,
        tokenPreview: token ? token.substring(0, 20) + '...' : null,
        hasUserInfo: !!userInfo,
        userInfo: userInfo ? JSON.parse(userInfo) : null
    });
    
    if (!token) {
        showMessage('認証トークンが見つかりません。再ログインしてください。', 'error');
        window.location.href = './lp.html';
        return;
    }
    
    // 緊急ログインでも実際のAPI解析を試行
    if (token === 'emergency-login-token-dev') {
        console.log('🛠️ Emergency login detected, but attempting real API analysis');
    }
    
    isAnalyzing = true;
    
    try {
        // Show loading state
        showLoadingState();
        
        // Perform analysis
        const result = await analyzeImage(currentFile, selectedLanguage, selectedAnalysisType);
        
        // Show results
        showAnalysisResults(result);
        
        // Refresh user info to update usage count after successful analysis
        console.log('🔄 Refreshing user info after successful analysis');
        await refreshUserInfo();
        
    } catch (error) {
        console.error('🚨 Analysis error:', error);
        
        // Enhanced error handling for 401
        if (error.message.includes('401')) {
            console.log('🚨 401 Authentication error detected - may be cache issue');
            
            // Check if forceClearAndRelogin function is available
            if (typeof forceClearAndRelogin === 'function') {
                if (confirm('認証エラーが発生しました。キャッシュをクリアして再ログインしますか？\n(Cancel を押すと通常のログイン画面に移動します)')) {
                    forceClearAndRelogin();
                    return;
                }
            }
            
            showMessage('認証が無効です。再ログインしてください。', 'error');
            setTimeout(() => {
                window.location.href = './lp.html';
            }, 2000);
        } else if (error.message.includes('403')) {
            // Usage limit exceeded - show upgrade modal
            console.log('🚨 403 Usage limit error detected');
            
            try {
                // Parse error response to check for upgrade requirement
                const errorMatch = error.message.match(/403 - (.+)$/);
                if (errorMatch) {
                    const errorData = JSON.parse(errorMatch[1]);
                    if (errorData.upgrade_required) {
                        console.log('📈 Showing upgrade modal for usage limit');
                        hideLoadingState();
                        showUpgradeModal();
                        return;
                    }
                }
            } catch (parseError) {
                console.error('Error parsing 403 response:', parseError);
            }
            
            showMessage('無料プランの解析回数に達しました。プレミアムプランをご検討ください。', 'error');
        } else {
            showMessage('解析中にエラーが発生しました: ' + error.message, 'error');
        }
        hideLoadingState();
    } finally {
        isAnalyzing = false;
    }
}

/**
 * Analyze image using backend API
 * バックエンドAPIを使用した画像解析
 */
async function analyzeImage(file, language, analysisType) {
    console.log(`🤖 Analyzing image: ${file.name} (${language}, ${analysisType})`);
    
    // Step 1: Upload image to S3 first (for images table record)
    console.log('📤 Step 1: Uploading image to S3 for record keeping...');
    let uploadResult = null;
    try {
        uploadResult = await uploadImageToS3(file);
        console.log('✅ S3 upload successful:', uploadResult);
    } catch (uploadError) {
        console.warn('⚠️ S3 upload failed, proceeding with analysis only:', uploadError);
    }
    
    // Step 2: Convert file to base64 for direct analysis
    const base64Data = await fileToBase64(file);
    
    // Step 3: Perform direct analysis with base64 data (include image_id if available)
    const analysisResult = await performImageAnalysis(base64Data, language, analysisType, uploadResult);
    
    return analysisResult;
}

/**
 * Upload image to S3
 * S3への画像アップロード
 */
async function uploadImageToS3(file) {
    console.log('📤 Starting S3 upload for:', file.name);
    
    // Convert file to base64
    const base64Data = await fileToBase64(file);
    const token = getAuthToken();
    const userId = getCurrentUserId();
    
    const uploadBody = {
        image: base64Data,
        filename: file.name,
        userId: userId,
        analysisType: selectedAnalysisType,
        language: selectedLanguage
    };
    
    console.log('🔍 Upload request details:', {
        filename: file.name,
        userId: userId,
        analysisType: selectedAnalysisType,
        language: selectedLanguage,
        imageSize: base64Data.length,
        token: token ? token.substring(0, 20) + '...' : 'No token'
    });
    
    const response = await fetch(`${API_BASE_URL}/upload-image`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(uploadBody)
    });
    
    console.log('📊 Upload response status:', response.status);
    
    if (!response.ok) {
        let errorDetails = 'Unknown error';
        try {
            const errorResponse = await response.text();
            console.error('❌ Upload error response:', errorResponse);
            errorDetails = errorResponse;
        } catch (e) {
            console.error('❌ Could not read upload error response:', e);
        }
        throw new Error(`Upload failed: ${response.status} - ${errorDetails}`);
    }
    
    const result = await response.json();
    console.log('✅ Upload successful:', result);
    return result;
}

/**
 * Perform image analysis
 * 画像解析実行
 */
async function performImageAnalysis(base64Data, language, analysisType, uploadResult = null) {
    const token = getAuthToken();
    
    const requestBody = {
        image: base64Data,  // バックエンドは'image'でbase64データを期待
        language: language,
        type: analysisType  // バックエンドは'type'を期待
    };
    
    // Include image_id and s3Url if upload was successful
    if (uploadResult && uploadResult.image_id) {
        requestBody.imageId = uploadResult.image_id;
        requestBody.s3Url = uploadResult.s3_url;
        console.log('📎 Including upload result in analysis:', {
            imageId: uploadResult.image_id,
            s3Url: uploadResult.s3_url
        });
    }
    
    const payloadSize = JSON.stringify(requestBody).length;
    console.log('🔍 Analysis request details:', {
        imageSize: base64Data.length,
        payloadSize: payloadSize,
        payloadSizeMB: (payloadSize / 1024 / 1024).toFixed(2),
        language: language,
        analysisType: analysisType,
        requestBody: { ...requestBody, image: '[BASE64_DATA_TRUNCATED]' },
        token: token ? token.substring(0, 20) + '...' : 'No token'
    });
    
    // Check payload size before sending
    const maxPayloadMB = 6; // API Gateway limit is 10MB, keep some buffer
    if (payloadSize > maxPayloadMB * 1024 * 1024) {
        throw new Error(`Payload too large: ${(payloadSize / 1024 / 1024).toFixed(2)}MB exceeds ${maxPayloadMB}MB limit`);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('📊 Analysis response status:', response.status);
        console.log('📊 Response headers:', {
            'content-type': response.headers.get('content-type'),
            'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
            'content-length': response.headers.get('content-length')
        });
        
        if (!response.ok) {
            // エラーレスポンスの詳細を取得
            let errorDetails = 'Unknown error';
            try {
                const errorResponse = await response.text();
                console.error('❌ Analysis error response:', errorResponse);
                errorDetails = errorResponse;
            } catch (e) {
                console.error('❌ Could not read error response:', e);
            }
            throw new Error(`Analysis failed: ${response.status} - ${errorDetails}`);
        }
        
        const result = await response.json();
        console.log('✅ Analysis successful:', result);
        return result;
        
    } catch (error) {
        console.error('🚨 Fetch error details:', {
            message: error.message,
            name: error.name,
            stack: error.stack
        });
        throw error;
    }
}

/**
 * Show loading state
 * ローディング状態表示
 */
function showLoadingState() {
    const previewSection = document.getElementById('previewSection');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    
    if (previewSection) {
        previewSection.style.display = 'none';
        previewSection.classList.add('hidden');
    }
    
    if (loadingSection) {
        loadingSection.style.display = 'block';
        loadingSection.classList.remove('hidden'); // hiddenクラスを削除
        console.log('🔍 Debug: Loading section shown, hidden class removed');
    }
    
    if (resultsSection) {
        resultsSection.style.display = 'none';
        resultsSection.classList.add('hidden');
    }
    
    // Start loading counter animation
    startLoadingCounter();
    
    // Scroll to loading section
    if (loadingSection) {
        loadingSection.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Start loading counter animation (0, 1, 2...)
 * ローディングカウンターアニメーション開始
 */
function startLoadingCounter() {
    const counterElement = document.getElementById('loadingCounter');
    const loadingSection = document.getElementById('loadingSection');
    const spinnerContainer = document.querySelector('.loading-spinner-container');
    const spinner = document.querySelector('.loading-spinner');
    
    console.log('🔍 Debug: Loading elements check:', {
        counterElement: !!counterElement,
        loadingSection: !!loadingSection,
        spinnerContainer: !!spinnerContainer,
        spinner: !!spinner,
        loadingSectionDisplay: loadingSection ? getComputedStyle(loadingSection).display : 'not found',
        loadingSectionClasses: loadingSection ? loadingSection.className : 'not found'
    });
    
    if (!counterElement) {
        console.error('❌ Loading counter element not found');
        return;
    }
    
    let count = 0;
    counterElement.textContent = count;
    
    console.log('⏱️ Starting loading counter animation...');
    
    // Clear any existing counter interval
    if (window.loadingCounterInterval) {
        clearInterval(window.loadingCounterInterval);
    }
    
    // Start counter animation
    window.loadingCounterInterval = setInterval(() => {
        count++;
        counterElement.textContent = count;
        console.log(`🔢 Loading counter: ${count}`);
        
        // Add visual feedback at certain milestones
        if (count === 5) {
            counterElement.style.color = '#66BB6A';
        } else if (count === 10) {
            counterElement.style.color = '#4CAF50';
        } else if (count === 15) {
            counterElement.style.color = '#2E7D32';
        }
        
        // Stop counter at reasonable limit (prevent infinite counting)
        if (count >= 30) {
            clearInterval(window.loadingCounterInterval);
            console.log('⏹️ Loading counter stopped at limit');
        }
    }, 1000); // Count every second
}

/**
 * Stop loading counter animation
 * ローディングカウンターアニメーション停止
 */
function stopLoadingCounter() {
    if (window.loadingCounterInterval) {
        clearInterval(window.loadingCounterInterval);
        window.loadingCounterInterval = null;
        console.log('⏹️ Loading counter stopped');
    }
    
    // Reset counter appearance
    const counterElement = document.getElementById('loadingCounter');
    if (counterElement) {
        counterElement.style.color = ''; // Reset to CSS default
    }
}

/**
 * Hide loading state
 * ローディング状態非表示
 */
function hideLoadingState() {
    const loadingSection = document.getElementById('loadingSection');
    if (loadingSection) {
        loadingSection.style.display = 'none';
    }
    
    // Stop loading counter
    stopLoadingCounter();
}

/**
 * Show analysis results
 * 解析結果表示
 */
function showAnalysisResults(result) {
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent'); // 正しいIDに修正
    
    console.log('🔍 Debug: Results elements check:', {
        loadingSection: !!loadingSection,
        resultsSection: !!resultsSection,
        resultsContent: !!resultsContent
    });
    
    // Stop loading counter before hiding loading section
    stopLoadingCounter();
    
    if (loadingSection) {
        loadingSection.style.display = 'none';
        loadingSection.classList.add('hidden');
    }
    
    if (resultsSection) {
        resultsSection.style.display = 'block';
        resultsSection.classList.remove('hidden');
    }
    
    if (resultsContent && result) {
        resultsContent.innerHTML = formatAnalysisResults(result);
        console.log('✅ Analysis results displayed successfully');
    } else {
        console.error('❌ Results content element not found or no result data');
    }
    
    // Scroll to results
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Format analysis results for display (元の実装を正確に移行)
 * 解析結果の表示フォーマット
 */
function formatAnalysisResults(result) {
    console.log('📝 formatAnalysisResults called with result:', result);
    
    let html = '<div class="analysis-result">';
    
    if (result.analysis) {
        // Markdownテキストを適切にフォーマット
        const formattedContent = formatAnalysisText(result.analysis);
        html += `<div class="analysis-content">${formattedContent}</div>`;
    }
    
    if (result.confidence) {
        html += `<div class="confidence-score">信頼度: ${Math.round(result.confidence * 100)}%</div>`;
    }
    
    html += '</div>';
    
    return html;
}

/**
 * Format analysis text with Markdown processing (元の実装を正確に移行)
 * テキストをHTMLに変換（改行とURLリンク化）
 */
function formatAnalysisText(text) {
    console.log('📝 formatAnalysisText called with text:', text?.substring(0, 100) + '...');
    
    // marked.jsとDOMPurifyの利用可能性をチェック
    const isMarkedAvailable = typeof marked !== 'undefined';
    const isDOMPurifyAvailable = typeof DOMPurify !== 'undefined';
    
    console.log('🔧 Library availability:', { 
        marked: isMarkedAvailable, 
        DOMPurify: isDOMPurifyAvailable 
    });
    
    if (!isMarkedAvailable) {
        console.warn('⚠️ marked.js is not available, using fallback HTML formatting');
        return formatAsPlainHTML(text);
    }
    
    if (!isDOMPurifyAvailable) {
        console.warn('⚠️ DOMPurify is not available, security risk exists');
    }
    
    try {
        console.log('🚀 Attempting to parse Markdown...');
        // Markdownをパースして表示
        const parsedMarkdown = marked.parse(text);
        console.log('✅ Markdown parsed successfully, length:', parsedMarkdown.length);
        
        if (isDOMPurifyAvailable) {
            // DOMPurifyでセキュリティ対策（XSS対策）
            const sanitizedHtml = DOMPurify.sanitize(parsedMarkdown, {
                ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'a', 'code', 'pre', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img', 'hr', 'div', 'span'],
                ALLOWED_ATTR: ['href', 'target', 'rel', 'title', 'class', 'id', 'src', 'alt']
            });
            console.log('🛡️ HTML sanitized successfully');
            return sanitizedHtml;
        } else {
            console.log('⚠️ Using unsanitized HTML (DOMPurify not available)');
            return parsedMarkdown;
        }
        
    } catch (error) {
        console.error('❌ Markdown parsing error:', error);
        console.log('🔄 Falling back to plain HTML formatting');
        return formatAsPlainHTML(text);
    }
}

/**
 * Fallback HTML formatting when Markdown is not available
 * Markdownが利用できない場合のフォールバック処理
 */
function formatAsPlainHTML(text) {
    if (!text) return '';
    
    return text
        // HTMLエスケープ
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
        // 改行を<br>に変換
        .replace(/\n/g, '<br>')
        // URLを自動リンク化
        .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
        // 太字（**text**）
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // 斜体（*text*）
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

/**
 * Handle new analysis button click
 * 新しい解析ボタンクリック処理
 */
function handleNewAnalysisClick() {
    console.log('🔄 Starting new analysis reset...');
    
    // Reset state
    currentFile = null;
    isAnalyzing = false;
    
    // Stop any running loading counter
    stopLoadingCounter();
    
    // Hide sections and add hidden classes
    const previewSection = document.getElementById('previewSection');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    
    if (previewSection) {
        previewSection.style.display = 'none';
        previewSection.classList.add('hidden');
    }
    if (loadingSection) {
        loadingSection.style.display = 'none';
        loadingSection.classList.add('hidden');
    }
    if (resultsSection) {
        resultsSection.style.display = 'none';
        resultsSection.classList.add('hidden');
    }
    
    // Clear file input completely
    const imageInput = document.getElementById('imageInput');
    if (imageInput) {
        imageInput.value = '';
        imageInput.files = null; // ファイルリストもクリア
        console.log('🧹 File input completely cleared');
    }
    
    // Scroll to upload section
    const uploadSection = document.querySelector('.upload-section');
    if (uploadSection) {
        uploadSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    console.log('✅ Reset for new analysis completed');
}

/**
 * Initialize Stripe
 * Stripe初期化
 */
function initializeStripe() {
    if (typeof Stripe !== 'undefined') {
        window.stripe = Stripe('pk_live_51Rvua8DBgr9iXlaH9i3mgCrJm5z4QcmPjYMhqo3ojLf7Za4ZprvBc2W7v44HZkW44dCh8YScmSJSWrwgiP7Lj4dw00xrliG0Ly');
        console.log('💳 Stripe initialized');
    }
}

/**
 * Initialize Markdown processing (元の実装を正確に移行)
 * Markdown処理初期化
 */
function initializeMarkdown() {
    try {
        // ライブラリの利用可能性をチェック
        const isMarkedAvailable = typeof marked !== 'undefined';
        const isDOMPurifyAvailable = typeof DOMPurify !== 'undefined';
        
        console.log('📚 Library status at init:', {
            marked: isMarkedAvailable,
            DOMPurify: isDOMPurifyAvailable
        });
        
        if (!isMarkedAvailable) {
            console.error('❌ marked.js is not loaded! Markdown parsing will fail.');
            return;
        }
        
        if (!isDOMPurifyAvailable) {
            console.warn('⚠️ DOMPurify is not loaded! XSS vulnerability exists.');
        }
        
        console.log('🔧 Configuring marked.js options...');
        
        // Markedのオプション設定
        marked.setOptions({
            breaks: true,        // 改行を<br>に変換
            gfm: true,          // GitHub Flavored Markdown有効
            headerIds: false,   // ヘッダーIDを生成しない
            mangle: false,      // emailアドレスの自動リンクを無効
            sanitize: false     // HTMLサニタイズはDOMPurifyで行う
        });
        
        console.log('🎨 Setting up custom renderer...');
        
        // カスタムレンダラー設定
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
        
        console.log('✅ marked.js configuration completed successfully');
        
        // テスト用のMarkdown解析
        const testMarkdown = '## Test\n**Bold text** and *italic text*\n- List item 1\n- List item 2';
        const testResult = marked.parse(testMarkdown);
        console.log('🧪 Markdown test:', { input: testMarkdown, output: testResult });
        
    } catch (error) {
        console.error('❌ Error during Markdown initialization:', error);
    }
}

/**
 * Show upgrade modal
 * アップグレードモーダル表示
 */
function showUpgradeModal() {
    console.log('⭐ Showing upgrade modal');
    
    // Check if upgrade modal exists, if not create it
    let upgradeModal = document.getElementById('upgradeModal');
    if (!upgradeModal) {
        createUpgradeModal();
        upgradeModal = document.getElementById('upgradeModal');
    }
    
    if (upgradeModal) {
        upgradeModal.style.display = 'flex';
        console.log('✅ Upgrade modal displayed');
    } else {
        console.error('❌ Failed to create upgrade modal');
        showMessage('アップグレード機能の準備中です', 'info');
    }
}

/**
 * Create upgrade modal HTML
 * アップグレードモーダルHTML作成
 */
function createUpgradeModal() {
    const modalHTML = `
    <div id="upgradeModal" class="upgrade-modal" style="display: none;">
        <div class="upgrade-content">
            <h2 class="upgrade-title">⭐ プレミアムプランにアップグレード</h2>
            <p style="color: #666; margin-bottom: 2rem;">無制限でAI解析をお楽しみください</p>
            
            <div class="plan-options">
                <div class="plan-card" onclick="selectPlan('3days')" id="plan3days">
                    <div class="plan-name">3日間プラン</div>
                    <div class="plan-price">¥980</div>
                    <div class="plan-features">
                        • 無制限AI解析<br>
                        • 高品質レポート<br>
                        • 優先サポート
                    </div>
                </div>
                
                <div class="plan-card popular" onclick="selectPlan('7days')" id="plan7days">
                    <div class="plan-badge">人気プラン</div>
                    <div class="plan-name">7日間プラン</div>
                    <div class="plan-price">¥1,980</div>
                    <div class="plan-features">
                        • 無制限AI解析<br>
                        • 高品質レポート<br>
                        • 優先サポート<br>
                        • 詳細分析機能
                    </div>
                </div>
            </div>
            
            <div class="modal-actions">
                <button onclick="proceedToPayment()" id="proceedPaymentBtn" class="proceed-btn" disabled>
                    💳 決済へ進む
                </button>
                <button onclick="closeUpgradeModal()" class="cancel-btn">キャンセル</button>
            </div>
        </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    console.log('✅ Upgrade modal HTML created');
}

/**
 * Close upgrade modal
 * アップグレードモーダルを閉じる
 */
function closeUpgradeModal() {
    const upgradeModal = document.getElementById('upgradeModal');
    if (upgradeModal) {
        upgradeModal.style.display = 'none';
    }
}

/**
 * Select plan
 * プラン選択
 */
function selectPlan(planType) {
    // Remove previous selection
    document.querySelectorAll('.plan-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Add selection to clicked plan
    const selectedCard = document.getElementById(`plan${planType}`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    // Enable proceed button
    const proceedBtn = document.getElementById('proceedPaymentBtn');
    if (proceedBtn) {
        proceedBtn.disabled = false;
    }
    
    // Store selected plan
    window.selectedPlan = planType;
    console.log(`📋 Plan selected: ${planType}`);
}

/**
 * Proceed to payment
 * 決済処理
 */
async function proceedToPayment() {
    if (!window.selectedPlan) {
        showMessage('プランを選択してください', 'error');
        return;
    }
    
    // Check authentication
    if (!isUserAuthenticated()) {
        showMessage('決済にはログインが必要です', 'info');
        closeUpgradeModal();
        window.location.href = './lp.html';
        return;
    }
    
    const currentUser = getCurrentUser();
    if (!currentUser || !currentUser.user_id) {
        showMessage('ユーザー情報の取得に失敗しました', 'error');
        return;
    }
    
    console.log(`💳 Proceeding to payment for plan: ${window.selectedPlan}`);
    
    // Show loading state
    const proceedBtn = document.getElementById('proceedBtn');
    if (proceedBtn) {
        proceedBtn.disabled = true;
        proceedBtn.textContent = '決済画面に移動中...';
    }
    
    try {
        // Call backend to create Stripe Checkout Session
        const response = await fetch(`${API_BASE_URL}/payment/create-checkout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                planType: window.selectedPlan,
                userId: currentUser.user_id
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Checkout session creation failed');
        }
        
        const data = await response.json();
        console.log('✅ Checkout session created:', data.session_id);
        
        // Redirect to Stripe Checkout
        window.location.href = data.checkout_url;
        
    } catch (error) {
        console.error('❌ Payment initiation error:', error);
        showMessage('決済処理でエラーが発生しました: ' + error.message, 'error');
        
        // Reset button state
        if (proceedBtn) {
            proceedBtn.disabled = false;
            proceedBtn.textContent = '決済に進む';
        }
    }
}

/**
 * Check payment result from URL parameters
 * URLパラメータから決済結果をチェック
 */
function checkPaymentResult() {
    const urlParams = new URLSearchParams(window.location.search);
    const paymentStatus = urlParams.get('payment');
    const sessionId = urlParams.get('session_id');
    
    if (paymentStatus === 'success' && sessionId) {
        console.log('💳 Payment success detected:', sessionId);
        
        // Show success message
        showMessage('✅ 決済が完了しました！プレミアムプランをお楽しみください。', 'success');
        
        // Clean URL parameters
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
        
        // Refresh user info to show premium status
        setTimeout(() => {
            if (typeof updateUserInfoDisplay === 'function') {
                updateUserInfoDisplay();
            }
        }, 2000);
        
    } else if (paymentStatus === 'cancel') {
        console.log('💳 Payment cancelled');
        
        // Show cancel message
        showMessage('決済がキャンセルされました。', 'info');
        
        // Clean URL parameters
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }
}

/**
 * Refresh user info from server
 * サーバーからユーザー情報を再取得してUI更新
 */
async function refreshUserInfo() {
    try {
        const token = getAuthToken();
        if (!token) {
            console.warn('⚠️ No auth token found for user info refresh');
            return;
        }
        
        // Emergency login token handling
        if (token === 'emergency-login-token-dev') {
            console.log('🛠️ Emergency login - skipping server refresh');
            return;
        }
        
        console.log('🔄 Fetching updated user info from server...');
        
        const response = await fetch(`${API_BASE_URL}/auth/user-info`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const updatedUserInfo = await response.json();
            console.log('✅ User info refreshed:', updatedUserInfo);
            
            // Update global user info
            // Update localStorage first
            localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo));
            
            // Update currentUser in auth.js (global variable)
            if (typeof window !== 'undefined' && typeof currentUser !== 'undefined') {
                currentUser = updatedUserInfo;
                console.log('🔄 Updated global currentUser variable');
            }
            
            // Update UI display
            if (typeof updateUserInfoDisplay === 'function') {
                updateUserInfoDisplay();
                console.log('🎨 User info display updated');
            } else {
                console.warn('⚠️ updateUserInfoDisplay function not available');
            }
        } else {
            console.warn('⚠️ Failed to refresh user info:', response.status);
        }
        
    } catch (error) {
        console.error('🚨 Error refreshing user info:', error);
        // Don't throw error to avoid disrupting the main flow
    }
}

/**
 * Resize image (元の実装を正確に移行)
 * 画像リサイズ
 */
function resizeImage(file, maxSize = 800) {
    // 🔍 デバッグ: 圧縮設定確認用ログ
    console.log('🖼️ Image compression settings:', {
        maxSize: maxSize,
        originalFileName: file.name,
        originalSize: (file.size / 1024).toFixed(1) + 'KB',
        timestamp: new Date().toISOString()
    });
    
    return new Promise((resolve, reject) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        img.onload = function() {
            // Calculate new dimensions
            let { width, height } = img;
            
            if (width <= maxSize && height <= maxSize) {
                // No resize needed
                resolve(file);
                return;
            }
            
            // Calculate resize ratio
            const ratio = Math.min(maxSize / width, maxSize / height);
            width *= ratio;
            height *= ratio;
            
            // Set canvas size
            canvas.width = width;
            canvas.height = height;
            
            // Draw resized image
            ctx.drawImage(img, 0, 0, width, height);
            
            // Convert to blob with quality setting
            const quality = 0.75;  // 最適化後の品質設定
            console.log('🎨 Converting to blob with quality:', quality);
            canvas.toBlob((blob) => {
                if (blob) {
                    // Create new File object
                    const resizedFile = new File([blob], file.name, {
                        type: file.type,
                        lastModified: Date.now()
                    });
                    
                    console.log(`Image resized: ${img.width}x${img.height} → ${width}x${height}`);
                    console.log(`File size: ${(file.size/1024).toFixed(1)}KB → ${(resizedFile.size/1024).toFixed(1)}KB`);
                    
                    resolve(resizedFile);
                } else {
                    reject(new Error('Failed to resize image'));
                }
            }, file.type, quality);
        };
        
        img.onerror = () => reject(new Error('Failed to load image'));
        img.src = URL.createObjectURL(file);
    });
}

/**
 * Convert file to base64 (元の実装を正確に移行)
 * ファイルをbase64に変換
 */
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        // Resize image if needed
        resizeImage(file, 800).then(resizedFile => {
            const reader = new FileReader();
            reader.onload = () => {
                // Remove data:image/jpeg;base64, prefix
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(resizedFile);
        }).catch(error => {
            console.error('Image resize error:', error);
            // Fallback to original file
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    });
}

/**
 * Get current user ID from authentication
 * 認証情報から現在のユーザーIDを取得
 */
function getCurrentUserId() {
    try {
        const userInfo = localStorage.getItem('userInfo');
        if (userInfo) {
            const userData = JSON.parse(userInfo);
            return userData.user_id || userData.email || 'anonymous';
        }
        return 'anonymous';
    } catch (error) {
        console.error('Error getting user ID:', error);
        return 'anonymous';
    }
}

/**
 * Create mock analysis result for emergency login
 * 緊急ログイン用のモック解析結果作成
 */
function createMockAnalysisResult(filename, language) {
    const mockResults = {
        ja: {
            title: '🛠️ 開発モード - モック解析結果',
            analysis: `
# 📸 ${filename} の解析結果（開発用）

## 🏔️ 観光地情報
**場所**: 札幌市内観光地（推定）  
**評価**: ⭐⭐⭐⭐⭐ 5.0/5.0
            `,
            confidence: 0.95
        },
        ko: {
            title: '🛠️ 개발 모드 - 모의 분석 결과',
            analysis: `
# 📸 ${filename} 분석 결과 (개발용)

## 🏔️ 관광지 정보
**장소**: 삿포로시 내 관광지 (추정)  
**평가**: ⭐⭐⭐⭐⭐ 5.0/5.0
            `,
            confidence: 0.95
        },
        zh: {
            title: '🛠️ 开发模式 - 模拟分析结果',
            analysis: `
# 📸 ${filename} 分析结果（开发用）

## 🏔️ 旅游景点信息
**地点**: 札幌市内旅游景点（推测）  
**评价**: ⭐⭐⭐⭐⭐ 5.0/5.0
            `,
            confidence: 0.95
        },
        en: {
            title: '🛠️ Development Mode - Mock Analysis Result',
            analysis: `
# 📸 ${filename} Analysis Result (Development)

## 🏔️ Tourist Destination Information
**Location**: Tourist spot in Sapporo City (estimated)  
**Rating**: ⭐⭐⭐⭐⭐ 5.0/5.0
            `,
            confidence: 0.95
        }
    };
    
    return mockResults[language] || mockResults['ja'];
}

/**
 * Show message to user
 * ユーザーへのメッセージ表示
 */
function showMessage(message, type = 'info') {
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // Create or update message element
    let messageEl = document.getElementById('message-display');
    if (!messageEl) {
        messageEl = document.createElement('div');
        messageEl.id = 'message-display';
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            max-width: 400px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        document.body.appendChild(messageEl);
    }
    
    // Set style based on type
    const styles = {
        success: 'background: #d1edda; color: #155724; border-left: 4px solid #28a745;',
        error: 'background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545;',
        info: 'background: #d1ecf1; color: #0c5460; border-left: 4px solid #17a2b8;'
    };
    
    messageEl.style.cssText += styles[type] || styles.info;
    messageEl.textContent = message;
    messageEl.style.display = 'block';
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        if (messageEl) {
            messageEl.style.display = 'none';
        }
    }, 5000);
}

/**
 * Save location settings to backend
 * 地域設定をバックエンドに保存
 */
async function saveLocationSettings() {
    console.log('📍 Saving location settings...');
    
    const countryInput = document.getElementById('countryInput');
    const cityInput = document.getElementById('cityInput');
    const saveBtn = document.getElementById('saveLocationBtn');
    
    if (!countryInput || !cityInput) {
        console.error('❌ Location input elements not found');
        return;
    }
    
    const country = countryInput.value.trim();
    const city = cityInput.value.trim();
    
    // Validate at least one field is filled
    if (!country && !city) {
        showMessage('国名または都市名のいずれかを入力してください', 'error');
        return;
    }
    
    // Show loading state
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span>💾 保存中...</span>';
    }
    
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('認証トークンが見つかりません');
        }
        
        const requestBody = {
            country: country || '',
            city: city || ''
        };
        
        console.log('📤 Sending location update:', requestBody);
        
        const response = await fetch(`${API_BASE_URL}/auth/update-location`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`保存に失敗しました: ${response.status} - ${errorData}`);
        }
        
        const result = await response.json();
        console.log('✅ Location saved successfully:', result);
        
        // Show success message
        showMessage('地域設定を保存しました', 'success');
        
        // Switch to display mode
        displayLocationInfo(country, city);
        
        // Update localStorage for quick access
        localStorage.setItem('userLocation', JSON.stringify({ country, city }));
        
    } catch (error) {
        console.error('🚨 Error saving location:', error);
        showMessage('地域設定の保存に失敗しました: ' + error.message, 'error');
    } finally {
        // Reset button state
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<span data-i18n="saveLocation">💾 保存</span>';
        }
    }
}

/**
 * Edit location settings (switch to input mode)
 * 地域設定編集（入力モードに切り替え）
 */
function editLocationSettings() {
    console.log('✏️ Switching to location edit mode...');
    
    const locationInputs = document.querySelector('.location-inputs');
    const locationActions = document.querySelector('.location-actions');
    const locationDisplay = document.getElementById('locationDisplay');
    const saveBtn = document.getElementById('saveLocationBtn');
    const editBtn = document.getElementById('editLocationBtn');
    
    // Show input fields and save button
    if (locationInputs) locationInputs.style.display = 'flex';
    if (saveBtn) saveBtn.style.display = 'inline-block';
    
    // Hide display and edit button
    if (locationDisplay) locationDisplay.style.display = 'none';
    if (editBtn) editBtn.style.display = 'none';
    
    // Load current values into input fields
    loadCurrentLocationToInputs();
    
    console.log('✅ Switched to edit mode');
}

/**
 * Display saved location information
 * 保存された地域情報を表示
 */
function displayLocationInfo(country, city) {
    console.log('📍 Displaying location info:', { country, city });
    
    const locationInputs = document.querySelector('.location-inputs');
    const locationDisplay = document.getElementById('locationDisplay');
    const currentLocation = document.getElementById('currentLocation');
    const saveBtn = document.getElementById('saveLocationBtn');
    const editBtn = document.getElementById('editLocationBtn');
    
    // Build display text
    let displayText = '';
    if (country && city) {
        displayText = `${country} / ${city}`;
    } else if (country) {
        displayText = country;
    } else if (city) {
        displayText = city;
    }
    
    if (displayText) {
        // Show display mode
        if (locationInputs) locationInputs.style.display = 'none';
        if (saveBtn) saveBtn.style.display = 'none';
        if (locationDisplay) locationDisplay.style.display = 'flex';
        if (editBtn) editBtn.style.display = 'inline-block';
        if (currentLocation) currentLocation.textContent = displayText;
        
        console.log('✅ Location displayed:', displayText);
    } else {
        // Show input mode if no location saved
        if (locationInputs) locationInputs.style.display = 'flex';
        if (saveBtn) saveBtn.style.display = 'inline-block';
        if (locationDisplay) locationDisplay.style.display = 'none';
        if (editBtn) editBtn.style.display = 'none';
    }
}

/**
 * Load current location data into input fields
 * 現在の地域データを入力フィールドにロード
 */
function loadCurrentLocationToInputs() {
    try {
        // Try to get from localStorage first
        const savedLocation = localStorage.getItem('userLocation');
        if (savedLocation) {
            const location = JSON.parse(savedLocation);
            const countryInput = document.getElementById('countryInput');
            const cityInput = document.getElementById('cityInput');
            
            if (countryInput) countryInput.value = location.country || '';
            if (cityInput) cityInput.value = location.city || '';
            
            console.log('📋 Loaded location from localStorage:', location);
        }
    } catch (error) {
        console.error('🚨 Error loading location to inputs:', error);
    }
}

/**
 * Load saved location settings from backend/localStorage
 * 保存された地域設定をバックエンド/localStorageからロード
 */
async function loadLocationSettings() {
    console.log('📍 Loading saved location settings...');
    
    try {
        // First try to get from user info if available
        const userInfo = localStorage.getItem('userInfo');
        if (userInfo) {
            const userData = JSON.parse(userInfo);
            const country = userData.country || '';
            const city = userData.city || '';
            
            if (country || city) {
                console.log('✅ Location loaded from user info:', { country, city });
                displayLocationInfo(country, city);
                // Save to localStorage for quick access
                localStorage.setItem('userLocation', JSON.stringify({ country, city }));
                return;
            }
        }
        
        // Fallback to localStorage
        const savedLocation = localStorage.getItem('userLocation');
        if (savedLocation) {
            const location = JSON.parse(savedLocation);
            console.log('✅ Location loaded from localStorage:', location);
            displayLocationInfo(location.country, location.city);
            return;
        }
        
        console.log('ℹ️ No saved location found, showing input mode');
        displayLocationInfo('', ''); // Show input mode
        
    } catch (error) {
        console.error('🚨 Error loading location settings:', error);
        // Show input mode on error
        displayLocationInfo('', '');
    }
}