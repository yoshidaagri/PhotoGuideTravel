/**
 * Translation Dictionary for Tourism Analyzer v1.3
 * 多言語対応辞書 - 全言語サポート
 */

// Translation dictionary for UI internationalization
const translations = {
    ja: {
        title: "観光アナライザー Anatri",
        description: "観光・グルメ画像をAI解析し、地元情報をご紹介",
        languageSelect: "解析言語を選択",
        analysisTypeSelect: "解析タイプを選択",
        storeAnalysis: "店舗・観光地分析",
        menuTranslation: "看板・メニュー翻訳",
        uploadText: "画像をアップロード",
        uploadSubtext: "店舗・観光地・料理の写真をクリックまたはドラッグ＆ドロップ",
        fileFormat: "対応形式: JPG, PNG, GIF (最大 10MB)",
        storeRecommended: "推奨: 名物料理、観光名所、イベント等",
        menuRecommended: "特に有効: 手書きメニュー、価格表、注文表等",
        previewTitle: "アップロード画像プレビュー",
        analyzeButton: "観光AI解析を開始",
        loading: "観光AIが解析中...",
        loadingSubtext: "名物料理・観光名所・地元情報",
        loadingDetail: "詳細な地元情報を分析しています",
        loginTitle: "観光アナライザー Anatri",
        googleLogin: "Googleでログイン",
        googleRedirecting: "Googleへリダイレクト中...",
        emailLogin: "メールでログイン",
        orDivider: "または",
        loginProcessing: "認証中...",
        signupPrompt: "アカウントをお持ちでない方は",
        signupLink: "新規登録",
        forgotPassword: "パスワードを忘れた方",
        confirmPassword: "パスワード確認",
        signup: "新規登録",
        backToLogin: "ログインに戻る",
        googleLoginNotReady: "Googleログインは現在設定中です。メールログインをご利用ください。",
        currentUser: "ユーザー",
        logout: "ログアウト",
        newAnalysis: "新しい解析",
        startText: "開始",
        serviceSuspended: "機能停止",
        // Premium Modal
        upgradeTitle: "⭐ プレミアムプランにアップグレード",
        upgradeDescription: "無制限でAI解析をお楽しみください",
        plan7days: "3日間プラン",
        plan20days: "7日間プラン",
        price980: "¥980",
        price1980: "¥1,980",
        duration7days: "1週間無制限",
        duration20days: "7日間無制限",
        featureUnlimited: "AI解析無制限",
        featurePriority: "高優先度処理",
        featureReport: "詳細分析レポート",
        proceedPayment: "決済に進む",
        cancelPayment: "キャンセル",
        popularPlan: "人気プラン",
        paymentPreparation: "💳 決済ページに移動中...",
        stripeRedirect: "安全なStripe決済ページへリダイレクトしています...",
        paymentSecurity: "🔒 SSL暗号化通信・Stripe社による安全決済",
        // Location Settings
        locationSettings: "📍 地域設定（解析精度向上）",
        countryLabel: "国名",
        cityLabel: "都市名",
        countryPlaceholder: "例: 日本",
        cityPlaceholder: "例: 札幌",
        saveLocation: "💾 保存",
        editLocation: "✏️ 編集",
        locationHelp: "💡 地域を指定するとAI解析がより正確になります"
    },
    ko: {
        title: "관광 애널라이저 Anatri",
        description: "관광・미식 이미지를 AI 분석하여 현지 정보를 소개",
        languageSelect: "분석 언어 선택",
        analysisTypeSelect: "분석 유형 선택",
        storeAnalysis: "점포・관광지 분석",
        menuTranslation: "간판・메뉴 번역",
        uploadText: "이미지 업로드",
        uploadSubtext: "점포・관광지・요리 사진을 클릭하거나 드래그&드롭",
        fileFormat: "지원 형식: JPG, PNG, GIF (최대 10MB)",
        storeRecommended: "추천: 명물 요리, 관광명소, 이벤트 등",
        menuRecommended: "특히 유효: 손글씨 메뉴, 가격표, 주문표 등",
        previewTitle: "업로드 이미지 미리보기",
        analyzeButton: "관광 AI 분석 시작",
        loading: "관광 AI 분석 중...",
        loadingSubtext: "명물 요리・관광명소・현지 정보",
        loadingDetail: "상세한 현지 정보를 분석하고 있습니다",
        loginTitle: "관광 애널라이저 Anatri",
        googleLogin: "Google로 로그인",
        googleRedirecting: "Google로 리다이렉트 중...",
        emailLogin: "이메일로 로그인",
        orDivider: "또는",
        loginProcessing: "인증 중...",
        signupPrompt: "계정이 없으신 분은",
        signupLink: "신규 가입",
        forgotPassword: "비밀번호를 잊으신 분",
        confirmPassword: "비밀번호 확인",
        signup: "신규 가입",
        backToLogin: "로그인으로 돌아가기",
        googleLoginNotReady: "Google 로그인은 현재 설정 중입니다. 이메일 로그인을 이용해주세요.",
        currentUser: "사용자",
        logout: "로그아웃",
        newAnalysis: "새로운 분석",
        startText: "시작",
        serviceSuspended: "기능 정지",
        // Premium Modal
        upgradeTitle: "⭐ 프리미엄 플랜으로 업그레이드",
        upgradeDescription: "무제한으로 AI 분석을 즐겨보세요",
        plan7days: "3일 플랜",
        plan20days: "7일 플랜",
        price980: "¥980",
        price1980: "¥1,980",
        duration7days: "1주간 무제한",
        duration20days: "7일간 무제한",
        featureUnlimited: "AI 분석 무제한",
        featurePriority: "높은 우선순위 처리",
        featureReport: "상세 분석 보고서",
        proceedPayment: "결제 진행",
        cancelPayment: "취소",
        popularPlan: "인기 플랜",
        paymentPreparation: "💳 결제 페이지로 이동 중...",
        stripeRedirect: "안전한 Stripe 결제 페이지로 리다이렉트하고 있습니다...",
        paymentSecurity: "🔒 SSL 암호화 통신・Stripe사의 안전 결제",
        // Location Settings
        locationSettings: "📍 지역 설정（분석 정확도 향상）",
        countryLabel: "국가명",
        cityLabel: "도시명",
        countryPlaceholder: "예: 일본",
        cityPlaceholder: "예: 삿포로",
        saveLocation: "💾 저장",
        editLocation: "✏️ 편집",
        locationHelp: "💡 지역을 지정하면 AI 분석이 더 정확해집니다"
    },
    zh: {
        title: "旅游分析器 Anatri",
        description: "AI分析旅游・美食图像，介绍当地信息",
        languageSelect: "选择分析语言",
        analysisTypeSelect: "选择分析类型",
        storeAnalysis: "店铺・景点分析",
        menuTranslation: "招牌・菜单翻译",
        uploadText: "上传图像",
        uploadSubtext: "点击或拖拽店铺・景点・料理照片",
        fileFormat: "支持格式: JPG, PNG, GIF (最大 10MB)",
        storeRecommended: "推荐: 特色料理、观光名胜、活动等",
        menuRecommended: "特别有效: 手写菜单、价格表、订单表等",
        previewTitle: "上传图像预览",
        analyzeButton: "开始旅游AI分析",
        loading: "旅游AI分析中...",
        loadingSubtext: "特色料理・观光名胜・当地信息",
        loadingDetail: "正在分析详细的当地信息",
        loginTitle: "旅游分析器 Anatri",
        googleLogin: "使用Google登录",
        googleRedirecting: "正在跳转到Google...",
        emailLogin: "使用邮箱登录",
        orDivider: "或者",
        loginProcessing: "认证中...",
        signupPrompt: "没有账户的用户",
        signupLink: "新用户注册",
        forgotPassword: "忘记密码的用户",
        confirmPassword: "确认密码",
        signup: "新用户注册",
        backToLogin: "返回登录",
        googleLoginNotReady: "Google登录目前正在设置中。请使用邮箱登录。",
        currentUser: "用户",
        logout: "登出",
        newAnalysis: "新分析",
        startText: "开始",
        serviceSuspended: "功能停止",
        // Premium Modal
        upgradeTitle: "⭐ 升级到高级计划",
        upgradeDescription: "享受无限AI分析",
        plan7days: "3天计划",
        plan20days: "7天计划",
        price980: "¥980",
        price1980: "¥1,980",
        duration7days: "1周无限制",
        duration20days: "7天无限制",
        featureUnlimited: "AI分析无限制",
        featurePriority: "高优先级处理",
        featureReport: "详细分析报告",
        proceedPayment: "进行支付",
        cancelPayment: "取消",
        popularPlan: "热门计划",
        paymentPreparation: "💳 正在转到支付页面...",
        stripeRedirect: "正在跳转到安全的Stripe支付页面...",
        paymentSecurity: "🔒 SSL加密通信・Stripe公司安全支付",
        // Location Settings
        locationSettings: "📍 地区设置（提高分析精度）",
        countryLabel: "国家",
        cityLabel: "城市",
        countryPlaceholder: "例: 日本",
        cityPlaceholder: "例: 札幌",
        saveLocation: "💾 保存",
        editLocation: "✏️ 编辑",
        locationHelp: "💡 指定地区可以使AI分析更加准确"
    },
    tw: {
        title: "旅遊分析器 Anatri",
        description: "AI分析旅遊・美食圖像，介紹當地資訊",
        languageSelect: "選擇分析語言",
        analysisTypeSelect: "選擇分析類型",
        storeAnalysis: "店鋪・景點分析",
        menuTranslation: "招牌・菜單翻譯",
        uploadText: "上傳圖像",
        uploadSubtext: "點擊或拖拽店鋪・景點・料理照片",
        fileFormat: "支持格式: JPG, PNG, GIF (最大 10MB)",
        storeRecommended: "推薦: 特色料理、觀光名勝、活動等",
        menuRecommended: "特別有效: 手寫菜單、價格表、訂單表等",
        previewTitle: "上傳圖像預覽",
        analyzeButton: "開始旅遊AI分析",
        loading: "旅遊AI分析中...",
        loadingSubtext: "特色料理・觀光名勝・當地資訊",
        loadingDetail: "正在分析詳細的當地資訊",
        loginTitle: "旅遊分析器 Anatri",
        googleLogin: "使用Google登入",
        googleRedirecting: "正在跳轉到Google...",
        emailLogin: "使用郵箱登入",
        orDivider: "或者",
        loginProcessing: "認證中...",
        signupPrompt: "沒有帳戶的用戶",
        signupLink: "新用戶註冊",
        forgotPassword: "忘記密碼的用戶",
        confirmPassword: "確認密碼",
        signup: "新用戶註冊",
        backToLogin: "返回登入",
        googleLoginNotReady: "Google登入目前正在設置中。請使用郵箱登入。",
        currentUser: "用戶",
        logout: "登出",
        newAnalysis: "新分析",
        startText: "開始",
        serviceSuspended: "功能停止",
        // Premium Modal
        upgradeTitle: "⭐ 升級到高級計劃",
        upgradeDescription: "享受無限AI分析",
        plan7days: "3天計劃",
        plan20days: "7天計劃",
        price980: "¥980",
        price1980: "¥1,980",
        duration7days: "1週無限制",
        duration20days: "7天無限制",
        featureUnlimited: "AI分析無限制",
        featurePriority: "高優先級處理",
        featureReport: "詳細分析報告",
        proceedPayment: "進行支付",
        cancelPayment: "取消",
        popularPlan: "熱門計劃",
        paymentPreparation: "💳 正在轉到支付頁面...",
        stripeRedirect: "正在跳轉到安全的Stripe支付頁面...",
        paymentSecurity: "🔒 SSL加密通信・Stripe公司安全支付",
        // Location Settings
        locationSettings: "📍 地區設置（提高分析精度）",
        countryLabel: "國家",
        cityLabel: "城市",
        countryPlaceholder: "例: 日本",
        cityPlaceholder: "例: 札幌",
        saveLocation: "💾 保存",
        editLocation: "✏️ 編輯",
        locationHelp: "💡 指定地區可以使AI分析更加準確"
    },
    en: {
        title: "Tourism Analyzer Anatri",
        description: "AI analysis of tourism and gourmet images with local information",
        languageSelect: "Select Analysis Language",
        analysisTypeSelect: "Select Analysis Type",
        storeAnalysis: "Store・Tourist Spot Analysis",
        menuTranslation: "Sign・Menu Translation",
        uploadText: "Upload Image",
        uploadSubtext: "Click or drag & drop photos of stores, tourist spots, dishes",
        fileFormat: "Supported formats: JPG, PNG, GIF (max 10MB)",
        storeRecommended: "Recommended: Local dishes, tourist attractions, events, etc.",
        menuRecommended: "Especially effective: Handwritten menus, price lists, order forms, etc.",
        previewTitle: "Uploaded Image Preview",
        analyzeButton: "Start Tourism AI Analysis",
        loading: "Tourism AI analyzing...",
        loadingSubtext: "Local dishes・Tourist attractions・Local information",
        loadingDetail: "Analyzing detailed local information",
        loginTitle: "Tourism Analyzer Anatri",
        googleLogin: "Sign in with Google",
        googleRedirecting: "Redirecting to Google...",
        emailLogin: "Sign in with Email",
        orDivider: "or",
        loginProcessing: "Authenticating...",
        signupPrompt: "Don't have an account?",
        signupLink: "Sign Up",
        forgotPassword: "Forgot Password?",
        confirmPassword: "Confirm Password",
        signup: "Sign Up",
        backToLogin: "Back to Login",
        googleLoginNotReady: "Google login is currently being set up. Please use email login.",
        currentUser: "User",
        logout: "Logout",
        newAnalysis: "New Analysis",
        startText: "Start",
        serviceSuspended: "Service Suspended",
        // Premium Modal
        upgradeTitle: "⭐ Upgrade to Premium Plan",
        upgradeDescription: "Enjoy unlimited AI analysis",
        plan7days: "3-day Plan",
        plan20days: "7-day Plan",
        price980: "¥980",
        price1980: "¥1,980",
        duration7days: "1 week unlimited",
        duration20days: "7 days unlimited",
        featureUnlimited: "Unlimited AI analysis",
        featurePriority: "High priority processing",
        featureReport: "Detailed analysis report",
        proceedPayment: "Proceed to Payment",
        cancelPayment: "Cancel",
        popularPlan: "Popular Plan",
        paymentPreparation: "💳 Moving to payment page...",
        stripeRedirect: "Redirecting to secure Stripe payment page...",
        paymentSecurity: "🔒 SSL encrypted communication・Secure payment by Stripe",
        // Location Settings
        locationSettings: "📍 Location Settings (Improve Analysis Accuracy)",
        countryLabel: "Country",
        cityLabel: "City",
        countryPlaceholder: "e.g.: Japan",
        cityPlaceholder: "e.g.: Sapporo",
        saveLocation: "💾 Save",
        editLocation: "✏️ Edit",
        locationHelp: "💡 Specifying your location will make AI analysis more accurate"
    }
};

/**
 * Update UI elements with selected language
 * 選択言語でUI要素を更新
 */
function updateLanguageUI(language = 'ja') {
    console.log(`🌐 Updating UI to language: ${language}`);
    
    try {
        const t = translations[language] || translations.ja;
        
        // Update all elements with data-i18n attribute
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            if (t[key]) {
                element.textContent = t[key];
            }
        });
        
        // Store selected language
        localStorage.setItem('selectedLanguage', language);
        console.log(`✅ UI updated to ${language}`);
        
    } catch (error) {
        console.error('🚨 Error updating language UI:', error);
    }
}

/**
 * Get current selected language
 * 現在選択されている言語を取得
 */
function getCurrentLanguage() {
    return localStorage.getItem('selectedLanguage') || 'ja';
}

/**
 * Get translation for a specific key
 * 特定キーの翻訳を取得
 */
function getTranslation(key, language = null) {
    const lang = language || getCurrentLanguage();
    const t = translations[lang] || translations.ja;
    return t[key] || key;
}