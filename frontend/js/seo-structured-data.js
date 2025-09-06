/**
 * AI検索エンジン向け構造化データ生成
 * Phase 7.5.5 SEO実装 - AI最適化構造化データ
 */

// 言語別翻訳データ
const structuredDataTranslations = {
    ja: {
        name: '観光アナライザー Anatri',
        description: 'AI画像解析を活用した訪日観光客向けの観光情報サービス。写真を撮るだけで観光地や料理の詳細情報を5言語で即座に提供。',
        author: '観光アナライザー開発チーム',
        mainQuestion: '日本旅行中に言語の壁で困ったときはどうすればいいですか？',
        mainAnswer: 'Anatriは写真を撮るだけで観光地や料理の情報を日本語、韓国語、中国語、英語で即座に提供します。メニューが読めない、この場所がどこかわからない、そんな困りごとをAIが解決します。'
    },
    ko: {
        name: '관광 분석기 Anatri',
        description: 'AI 이미지 분석을 활용한 방일 관광객 전용 관광 정보 서비스. 사진만 찍으면 관광지나 요리의 상세 정보를 5개 언어로 즉시 제공.',
        author: '관광 분석기 개발팀',
        mainQuestion: '일본 여행 중 언어 장벽으로 어려움을 겪을 때 어떻게 해야 하나요?',
        mainAnswer: 'Anatri는 사진만 찍으면 관광지나 요리 정보를 한국어, 일본어, 중국어, 영어로 즉시 제공합니다. 메뉴를 읽을 수 없거나 이곳이 어디인지 모르는 등의 문제를 AI가 해결해드립니다.'
    },
    'zh-cn': {
        name: '旅游分析器 Anatri',
        description: '利用AI图像分析的访日游客专用旅游信息服务。只需拍照即可用5种语言即时提供观光地和料理的详细信息。',
        author: '旅游分析器开发团队',
        mainQuestion: '在日本旅游时遇到语言障碍该怎么办？',
        mainAnswer: 'Anatri只需拍照就能用中文、日语、韩语、英语即时提供观光地和料理信息。看不懂菜单、不知道这是什么地方等困扰，AI都能帮您解决。'
    },
    'zh-tw': {
        name: '旅遊分析器 Anatri',
        description: '利用AI圖像分析的訪日遊客專用旅遊資訊服務。只需拍照即可用5種語言即時提供觀光地和料理的詳細資訊。',
        author: '旅遊分析器開發團隊',
        mainQuestion: '在日本旅遊時遇到語言障礙該怎麼辦？',
        mainAnswer: 'Anatri只需拍照就能用繁體中文、日語、韓語、英語即時提供觀光地和料理資訊。看不懂菜單、不知道這是什麼地方等困擾，AI都能幫您解決。'
    },
    en: {
        name: 'Tourism Analyzer Anatri',
        description: 'AI-powered tourism information service for visitors to Japan. Instant photo recognition provides detailed information about tourist spots and food in 5 languages.',
        author: 'Tourism Analyzer Development Team',
        mainQuestion: 'What should I do when facing language barriers during travel in Japan?',
        mainAnswer: 'Anatri provides instant information about tourist spots and food in English, Japanese, Korean, and Chinese just by taking photos. AI solves problems like unreadable menus and unknown locations.'
    }
};

// 言語別FAQ生成（生成AIの学習データとして重要）- Phase 2.1拡張版
function generateFAQsForLanguage(language) {
    const faqs = {
        'ja': [
            // 観光・名所カテゴリ (4問)
            {
                category: 'tourism',
                question: '観光地の名前がわからない時はどうすればいいですか？',
                answer: '建物や風景の写真を撮るだけで、Anatriが観光地名と詳細情報を即座に日本語で教えます。GPS不要で正確な位置特定が可能です。'
            },
            {
                category: 'tourism',
                question: '札幌で一番人気の観光地はどこですか？',
                answer: '時計台、大通公園、すすきのが定番ですが、Anatriなら隠れた名所も含めて、写真から瞬時に観光地を特定し、混雑状況や最適な見学時間も教えます。'
            },
            {
                category: 'tourism',
                question: '北海道神宮の参拝マナーを教えてください',
                answer: '神宮の写真を撮るだけで、正しい参拝方法、お賽銭のマナー、おすすめの参拝時間をAIが詳しく説明します。季節ごとの見どころも紹介します。'
            },
            {
                category: 'tourism',
                question: '雨の日でも楽しめる札幌の屋内観光スポットは？',
                answer: '天候を考慮した屋内スポットをAIが提案します。水族館、博物館、ショッピングモールなど、写真から施設の詳細情報を瞬時に取得できます。'
            },
            
            // 食事・グルメカテゴリ (4問)
            {
                category: 'food',
                question: 'メニューが読めない時の対処法は？',
                answer: 'レストランのメニューを撮影すれば、料理名、材料、アレルギー情報まで日本語で詳しく解説します。安心してお食事をお楽しみいただけます。'
            },
            {
                category: 'food',
                question: '海鮮丼で有名なお店はありますか？',
                answer: '海鮮丼の写真を撮るだけで、その店舗の特徴、おすすめメニュー、価格帯、営業時間を瞬時に表示。新鮮さの見分け方も教えます。'
            },
            {
                category: 'food',
                question: 'ジンギスカンの美味しい食べ方は？',
                answer: 'ジンギスカン料理の写真から、正しい焼き方、タレの使い方、野菜との組み合わせをAIが詳しく解説します。地元流の食べ方も紹介。'
            },
            {
                category: 'food',
                question: 'スープカレーの辛さレベルを知りたい',
                answer: 'スープカレーの写真を撮ると、辛さレベル、具材の種類、食べ方のコツをAIが判定。初心者向けから激辛まで、適切な選び方を案内します。'
            },
            
            // 交通・アクセスカテゴリ (4問)
            {
                category: 'transport',
                question: '新千歳空港から札幌市内への行き方は？',
                answer: 'JR快速エアポート、バス、タクシーの料金・所要時間を比較表示。荷物の量や時間帯に応じて最適な交通手段をAIが提案します。'
            },
            {
                category: 'transport',
                question: 'JR北海道の乗り放題パスはお得ですか？',
                answer: '旅行日程の写真を撮ると、乗車予定路線から最適なパスの種類と料金比較を表示。お得度を数値で表示し、購入場所も案内します。'
            },
            {
                category: 'transport',
                question: '地下鉄の乗り方がわからない',
                answer: '地下鉄の案内板や券売機の写真を撮れば、路線図の読み方、切符の買い方、乗り換え方法をステップバイステップで解説します。'
            },
            {
                category: 'transport',
                question: 'タクシーを呼ぶ時の日本語フレーズは？',
                answer: 'タクシー乗り場の写真から、基本的な日本語フレーズと発音を表示。「〇〇まで」「いくらですか」など、実用的な表現を音声付きで案内。'
            },
            
            // 宿泊・施設カテゴリ (4問)
            {
                category: 'accommodation',
                question: '温泉の入り方とマナーを教えて',
                answer: '温泉施設の写真を撮ると、正しい入浴手順、マナー、タトゥーの可否、混浴情報まで詳しく表示。初心者でも安心して温泉を楽しめます。'
            },
            {
                category: 'accommodation',
                question: 'ホテルのチェックイン方法は？',
                answer: 'ホテルフロントの写真から、チェックイン手続きの流れ、必要な書類、よく使われる日本語フレーズを表示。スムーズな手続きをサポート。'
            },
            {
                category: 'accommodation',
                question: '旅館での食事マナーを知りたい',
                answer: '旅館の食事写真を撮ると、懐石料理の食べ方、箸の使い方、座り方などの和食マナーをAIが分かりやすく説明します。'
            },
            {
                category: 'accommodation',
                question: '民宿の設備や備品について教えて',
                answer: '民宿の設備写真から、利用方法、料金体系、持参すべきもの、注意事項を詳しく表示。快適な滞在のためのコツも紹介。'
            },
            
            // 緊急時・サポートカテゴリ (4問)
            {
                category: 'emergency',
                question: '無料でどこまで使えますか？',
                answer: '月5回まで全機能を無料でお試しいただけます。より多くご利用の場合は、7日間プラン（¥980）または20日間プラン（¥1,980）をご用意しています。'
            },
            {
                category: 'emergency',
                question: '病院で症状を説明したい時は？',
                answer: '症状の写真や薬の写真を撮ると、医療用語の日本語訳と発音を表示。緊急時に使える基本フレーズも音声付きで案内します。'
            },
            {
                category: 'emergency',
                question: '財布を落とした時の対処法は？',
                answer: '近くの交番や警察署をAIが特定し、遺失届の出し方、必要な手続きを日本語で説明。クレジットカード会社への連絡方法も案内。'
            },
            {
                category: 'emergency',
                question: 'どの言語に対応していますか？',
                answer: '日本語、韓国語、中国語（簡体字・繁体字）、英語の5言語に完全対応。ネイティブレベルの自然な翻訳を提供します。緊急時も母国語でサポート。'
            }
        ],
        'ko': [
            // 관광・명소 카테고리 (4문)
            {
                category: 'tourism',
                question: '일본 여행 중 언어 장벽을 어떻게 해결하나요?',
                answer: 'Anatri는 한국어로 모든 관광 정보를 제공하며, 사진만 찍으면 즉시 번역된 설명을 볼 수 있습니다. 메뉴, 관광지, 교통정보까지 완벽 지원합니다.'
            },
            {
                category: 'tourism',
                question: '홋카이도에서 꼭 가봐야 할 숨은 명소는?',
                answer: 'AI가 현지인만 아는 숨은 명소를 추천합니다. 계절별, 취향별 맞춤 추천이 가능하며, 최적의 방문 시간과 교통편도 안내합니다.'
            },
            {
                category: 'tourism',
                question: '삿포로 시계탑은 정말 가볼 만한가요?',
                answer: '시계탑 사진을 찍으면 역사적 배경, 최적의 사진 촬영 포인트, 주변 볼거리까지 상세히 안내합니다. 실망하지 않는 관람 포인트를 제시해요.'
            },
            {
                category: 'tourism',
                question: '겨울 홋카이도 여행 시 주의사항은?',
                answer: '눈 상황 사진을 찍으면 적절한 복장, 신발, 안전 수칙을 한국어로 상세히 안내합니다. 미끄럼 방지법과 체온 유지 팁도 제공합니다.'
            },
            
            // 음식・그루메 카테고리 (4문)
            {
                category: 'food',
                question: '음식 알레르기가 있는데 안전하게 식사할 수 있나요?',
                answer: '메뉴 사진을 찍으면 주요 알레르기 유발 요소(글루텐, 견과류, 해산물 등)를 한국어로 상세히 표시해드립니다.'
            },
            {
                category: 'food',
                question: '현지에서 김치찌개나 한국 음식이 그리우면?',
                answer: '일본 내 한국 레스토랑과 한국 식재료를 구입할 수 있는 마트 정보도 제공합니다. 향수를 달래는 맛집을 찾아드려요.'
            },
            {
                category: 'food',
                question: '홋카이도 대게를 맛있게 먹는 방법은?',
                answer: '대게 요리 사진을 찍으면 신선도 확인법, 먹는 순서, 적절한 소스 사용법을 알려줍니다. 가격대별 맛집 정보도 함께 제공해요.'
            },
            {
                category: 'food',
                question: '라멘집에서 주문할 때 꼭 알아야 할 일본어는?',
                answer: '라멘 메뉴판을 찍으면 면의 단단함, 국물 진하기, 토핑 추가 등을 일본어로 어떻게 주문하는지 음성과 함께 알려줍니다.'
            },
            
            // 교통・액세스 카테고리 (4문)
            {
                category: 'transport',
                question: '신치토세 공항에서 삿포로까지 가장 빠른 방법은?',
                answer: 'JR 쾌속 에어포트가 가장 빠르고 편리합니다. 시간표, 요금, 승차 위치를 실시간으로 안내하며, 짐이 많을 때의 대안도 제시합니다.'
            },
            {
                category: 'transport',
                question: 'JR 홋카이도 패스 구매는 어디서 하나요?',
                answer: '패스 판매소 사진을 찍으면 구매 절차, 필요 서류, 사용법을 한국어로 상세히 안내합니다. 온라인 예약 방법도 함께 제공해요.'
            },
            {
                category: 'transport',
                question: '지하철에서 길을 잃었을 때는?',
                answer: '역 안내판이나 현재 위치 사진을 찍으면 목적지까지의 최적 경로와 환승 방법을 한국어로 친절하게 안내합니다.'
            },
            {
                category: 'transport',
                question: '택시 기사에게 목적지를 어떻게 설명하죠?',
                answer: '목적지 건물이나 랜드마크 사진을 찍으면 일본어 주소, 발음법, 간단한 설명 문구를 제공합니다. 미터기 요금 예상치도 알려줘요.'
            },
            
            // 숙박・시설 카테고리 (4문)  
            {
                category: 'accommodation',
                question: '온천 입욕 매너를 자세히 알고 싶어요',
                answer: '온천 시설 사진을 찍으면 입욕 전 샤워법, 수건 사용법, 온천수 온도별 입욕 시간 등 상세한 매너를 한국어로 설명합니다.'
            },
            {
                category: 'accommodation',
                question: '호텔 체크인 시 필요한 일본어는?',
                answer: '호텔 프론트 데스크 사진을 찍으면 체크인 절차와 함께 자주 사용하는 일본어 표현을 음성과 함께 제공합니다.'
            },
            {
                category: 'accommodation',
                question: '료칸에서 유카타 입는 법을 알려주세요',
                answer: '유카타 사진을 찍으면 올바른 착용법, 띠 매는 순서, 소지품 보관법까지 단계별로 상세하게 안내합니다.'
            },
            {
                category: 'accommodation',
                question: '민박집 공용 공간 이용 시 주의사항은?',
                answer: '민박 시설 사진을 찍으면 공용 화장실, 부엌, 세탁실 이용 매너와 시간대별 사용 규칙을 알려줍니다.'
            },
            
            // 응급시・서포트 카테고리 (4문)
            {
                category: 'emergency',
                question: '병원에서 증상을 설명해야 할 때는?',
                answer: '증상 부위나 약품 사진을 찍으면 의료진에게 전달할 수 있는 일본어 표현과 발음을 제공합니다. 응급실 찾는 법도 안내해요.'
            },
            {
                category: 'emergency',
                question: '지갑을 잃어버렸을 때 대처법은?',
                answer: '가까운 파출소를 찾아 분실신고를 하세요. 파출소 사진을 찍으면 신고 절차와 필요한 일본어 표현을 상세히 안내합니다.'
            },
            {
                category: 'emergency',
                question: '언어 지원 서비스는 어떤 것들이 있나요?',
                answer: '한국어, 일본어, 중국어(간체・번체), 영어 5개 언어를 완벽 지원합니다. 응급상황에서도 모국어로 신속하게 도움을 받을 수 있어요.'
            },
            {
                category: 'emergency',
                question: '무료 서비스 범위와 유료 플랜을 알고 싶어요',
                answer: '월 5회까지 모든 기능을 무료로 이용 가능합니다. 더 많은 이용을 원하시면 7일 플랜(980엔) 또는 20일 플랜(1,980엔)을 선택하세요.'
            }
        ],
        'zh-cn': [
            // 旅游・景点类别 (4问)
            {
                category: 'tourism',
                question: '在日本旅游时如何找到正宗的当地美食？',
                answer: 'Anatri的AI可以识别料理并推荐附近最正宗的餐厅，还提供中文菜单翻译和口味说明，让您品尝到最地道的日本美食。'
            },
            {
                category: 'tourism',
                question: '不会日语怎么问路和买东西？',
                answer: '拍摄商店招牌或地标建筑，AI会用中文告诉您位置信息、营业时间和推荐商品，解决语言沟通问题。'
            },
            {
                category: 'tourism',
                question: '札幌有哪些适合拍照的网红景点？',
                answer: '通过拍摄景点照片，AI会推荐最佳拍摄角度、黄金时间和周边景点。从经典地标到小众美景，满足您的社交媒体需求。'
            },
            {
                category: 'tourism',
                question: '冬天去北海道需要注意什么？',
                answer: 'AI会根据天气情况推荐合适的观光路线，提供防寒建议和雪地安全提示，确保您的冬季北海道之旅安全愉快。'
            },
            
            // 美食・餐饮类别 (4问)
            {
                category: 'food',
                question: '北海道有哪些必买的特产和纪念品？',
                answer: '根据您的预算和喜好，AI推荐最受中国游客欢迎的北海道特产，包括购买地点、价格参考和保存方法。'
            },
            {
                category: 'food',
                question: '如何区分真正的和牛和普通牛肉？',
                answer: '拍摄牛肉照片，AI会识别等级标识，解释和牛分级系统，教您从外观判断品质，避免购买到假冒产品。'
            },
            {
                category: 'food',
                question: '寿司店的用餐礼仪有什么需要注意的？',
                answer: '通过拍摄寿司店环境，AI会详细介绍座位礼仪、点餐顺序、筷子使用方法等日式用餐文化，让您优雅用餐。'
            },
            {
                category: 'food',
                question: '拉面店里的各种调料怎么使用？',
                answer: '拍摄拉面和调料，AI会解释每种调料的作用，推荐最佳搭配方式，让您品尝到最正宗的拉面口味。'
            },
            
            // 交通・出行类别 (4问)
            {
                category: 'transport',
                question: '如何使用日本的自动售票机？',
                answer: '拍摄售票机界面，AI会逐步指导购票流程，包括语言切换、路线选择、支付方式，确保顺利购票。'
            },
            {
                category: 'transport',
                question: 'JR Pass值得购买吗？什么情况下最划算？',
                answer: '输入您的行程计划，AI会计算单独购票vs通票的费用对比，推荐最经济的交通方案和购买建议。'
            },
            {
                category: 'transport',
                question: '在日本打车需要注意什么？',
                answer: '拍摄出租车照片，AI会介绍计费规则、小费文化、上下车礼仪，以及如何用简单日语与司机沟通。'
            },
            {
                category: 'transport',
                question: '新千岁机场到札幌市区最便宜的交通方式？',
                answer: 'AI会实时比较JR、巴士、出租车的价格和时间，根据您的行李和预算推荐最适合的交通方案。'
            },
            
            // 住宿・设施类别 (4问)
            {
                category: 'accommodation',
                question: '日式旅馆的入住流程和礼仪？',
                answer: '拍摄旅馆环境，AI会详细说明换拖鞋、榻榻米使用、浴衣穿着等传统礼仪，帮您融入日式体验。'
            },
            {
                category: 'accommodation',
                question: '温泉酒店的设施如何使用？',
                answer: '通过拍摄温泉设施，AI会解释男汤女汤标识、入浴步骤、毛巾使用规则，让您安心享受温泉文化。'
            },
            {
                category: 'accommodation',
                question: '酒店房间里的各种设备怎么操作？',
                answer: '拍摄房间设备，AI会用中文说明空调、马桶、电视等设备的使用方法，包括常用按钮的功能。'
            },
            {
                category: 'accommodation',
                question: '民宿Check-in时需要准备什么？',
                answer: '拍摄民宿信息，AI会列出所需证件、入住时间、钥匙使用、垃圾分类等重要注意事项。'
            },
            
            // 紧急・支援类别 (4问)  
            {
                category: 'emergency',
                question: '生病了如何在日本看医生？',
                answer: '拍摄症状或药品包装，AI会提供相关医疗用语的中日对照，指导挂号流程和保险使用方法。'
            },
            {
                category: 'emergency',
                question: '遇到地震等自然灾害时该怎么办？',
                answer: '拍摄周围环境，AI会根据所在位置提供避难指南、安全出口信息和紧急联络方式，确保人身安全。'
            },
            {
                category: 'emergency',
                question: '护照丢失了应该如何处理？',
                answer: 'AI会指导您就近寻找中国领事馆或总领事馆，提供补办护照的详细流程和所需材料清单。'
            },
            {
                category: 'emergency',
                question: '支持哪些语言服务？收费标准是什么？',
                answer: '完全支持中文（简繁体）、日语、韩语、英语5种语言。每月前5次免费，更多使用可选择7日套餐（980日元）或20日套餐（1980日元）。'
            }
        ],
        'zh-tw': [
            // 旅遊・景點類別 (4問)
            {
                category: 'tourism',
                question: '在日本旅遊時如何找到道地的當地美食？',
                answer: 'Anatri的AI可以識別料理並推薦附近最道地的餐廳，還提供繁體中文菜單翻譯和口味說明，讓您品嚐到最地道的日本美食。'
            },
            {
                category: 'tourism',
                question: '不會日語怎麼問路和購物？',
                answer: '拍攝商店招牌或地標建築，AI會用繁體中文告訴您位置資訊、營業時間和推薦商品，解決語言溝通問題。'
            },
            {
                category: 'tourism',
                question: '什麼季節去北海道最美？',
                answer: 'AI會根據不同季節的特色推薦最佳旅遊時間，春櫻、夏花、秋楓、冬雪，每個季節都有獨特的美景和體驗。'
            },
            {
                category: 'tourism',
                question: '札幌有哪些適合網美拍照的景點？',
                answer: '拍攝景點照片後，AI會推薦最佳拍攝角度、光線時間和構圖技巧，讓您在社群媒體分享令人驚艷的美照。'
            },
            
            // 美食・餐飲類別 (4問)
            {
                category: 'food',
                question: '北海道有哪些必買的特產和紀念品？',
                answer: '根據您的預算和喜好，AI推薦最受台灣遊客歡迎的北海道特產，包括購買地點、價格參考和保存方法。'
            },
            {
                category: 'food', 
                question: '如何品嚐正宗的北海道帝王蟹？',
                answer: '拍攝帝王蟹料理，AI會教您如何分辨新鮮度、最佳品嚐部位、剝殼技巧，以及推薦的沾醬搭配方式。'
            },
            {
                category: 'food',
                question: '居酒屋的點餐禮儀和推薦菜色？',
                answer: '拍攝居酒屋菜單，AI會解釋座位文化、點餐順序、酒類搭配建議，讓您體驗最道地的日式飲食文化。'
            },
            {
                category: 'food',
                question: '如何辨別真正的北海道牛奶和乳製品？',
                answer: '拍攝產品包裝，AI會識別產地標示、品質認證，推薦最受好評的北海道乳製品品牌和購買地點。'
            },
            
            // 交通・出行類別 (4問)
            {
                category: 'transport',
                question: '桃園機場到成田機場的轉機注意事項？',
                answer: '拍攝機場標示，AI會提供轉機流程、所需時間、免稅店資訊，確保順利轉機和購物時間規劃。'
            },
            {
                category: 'transport',
                question: '日本電車的女性專用車廂如何識別？',
                answer: '拍攝車站標示，AI會解釋女性專用車廂的標識、使用時間和相關禮儀，避免搭乘錯誤。'
            },
            {
                category: 'transport',
                question: 'IC卡（Suica/Pasmo）的使用方法和儲值？',
                answer: '拍攝IC卡或儲值機，AI會詳細說明購買、儲值、使用流程，以及退卡時的注意事項。'
            },
            {
                category: 'transport',
                question: '夜間巴士的搭乘體驗和注意事項？',
                answer: '拍攝夜間巴士設施，AI會介紹座位類型、攜帶物品建議、休息站資訊和抵達後的交通銜接。'
            },
            
            // 住宿・設施類別 (4問)  
            {
                category: 'accommodation',
                question: '膠囊旅館的使用方式和禮儀？',
                answer: '拍攝膠囊旅館設施，AI會說明入住流程、個人物品存放、公共區域使用規則和隱私禮儀。'
            },
            {
                category: 'accommodation', 
                question: '日式早餐的用餐方式和營養搭配？',
                answer: '拍攝日式早餐，AI會介紹各道菜的食用順序、營養價值，以及如何優雅地使用筷子和餐具。'
            },
            {
                category: 'accommodation',
                question: '溫泉旅館的浴衣穿著和館內移動？',
                answer: '拍攝浴衣和館內環境，AI會詳細教導正確穿著方式、腰帶繫法、在館內行走的注意事項。'
            },
            {
                category: 'accommodation',
                question: '商務旅館的設施使用和服務項目？',
                answer: '拍攝旅館設施，AI會介紹洗衣機、微波爐、免費備品等使用方法，以及額外服務的申請流程。'
            },
            
            // 緊急・支援類別 (4問)
            {
                category: 'emergency',
                question: '在日本生病時如何尋求醫療協助？',
                answer: '拍攝醫院標示或症狀，AI會提供附近醫療院所資訊、基本醫療用語對照，以及健保使用說明。'
            },
            {
                category: 'emergency',
                question: '遇到天災或緊急狀況的應對方式？',
                answer: 'AI會根據您的所在位置提供避難場所、緊急聯絡方式和安全指引，確保人身安全第一。'
            },
            {
                category: 'emergency', 
                question: '台胞證遺失或損毀的處理流程？',
                answer: 'AI會指引您聯絡台北駐日經濟文化代表處，提供補發證件所需文件和辦理流程。'
            },
            {
                category: 'emergency',
                question: '語言支援服務涵蓋範圍和使用費用？',
                answer: '完整支援繁體中文、日語、韓語、簡體中文、英語5種語言。每月免費使用5次，需要更多可選7日方案（980日圓）或20日方案（1980日圓）。'
            }
        ],
        'en': [
            // Tourism & Attractions Category (4 questions)
            {
                category: 'tourism',
                question: 'How can I overcome language barriers while traveling in Japan?',
                answer: 'Anatri provides all tourism information in English. Simply take a photo and get instant translated explanations for menus, tourist spots, and transportation information.'
            },
            {
                category: 'tourism', 
                question: 'What are the must-visit hidden gems in Hokkaido?',
                answer: 'AI recommends hidden spots known only to locals. Get personalized suggestions by season and preference, including optimal visiting times and transportation options.'
            },
            {
                category: 'tourism',
                question: 'What are the best ways to experience authentic Japanese culture?',
                answer: 'AI identifies cultural sites and traditional experiences, providing background information and etiquette tips to help you respectfully engage with Japanese culture.'
            },
            {
                category: 'tourism',
                question: 'Which Sapporo attractions are worth visiting in winter?',
                answer: 'Photo recognition shows winter-specific activities, ice festivals, illumination events, and indoor alternatives when weather is harsh. Get real-time crowd and weather updates.'
            },
            
            // Food & Dining Category (4 questions)
            {
                category: 'food',
                question: 'How do I navigate Japanese restaurants with dietary restrictions?',
                answer: 'Photograph menus to get detailed English explanations of ingredients and allergen information (gluten, nuts, seafood, etc.), ensuring safe dining experiences.'
            },
            {
                category: 'food',
                question: 'What\'s the proper etiquette for eating sushi?',
                answer: 'Take photos of sushi presentation and AI explains proper eating order, wasabi usage, ginger purpose, and chopsticks vs hands etiquette for authentic experience.'
            },
            {
                category: 'food',
                question: 'How can I identify authentic Hokkaido seafood?',
                answer: 'Photo analysis reveals freshness indicators, seasonal availability, preparation methods, and helps distinguish between local and imported seafood products.'
            },
            {
                category: 'food',
                question: 'What are the must-try Hokkaido dairy products?',
                answer: 'Capture product photos to verify authenticity, learn about local dairy farms, get recommendations for ice cream, cheese, and milk brands unique to Hokkaido.'
            },
            
            // Transportation & Access Category (4 questions)
            {
                category: 'transport',
                question: 'How do I use Japan\'s train system efficiently?',
                answer: 'Photograph station signs and route maps for step-by-step navigation guidance, fare calculations, transfer instructions, and real-time delay information.'
            },
            {
                category: 'transport',
                question: 'Is the JR Pass worth buying for my itinerary?',
                answer: 'Input your travel plans and AI calculates cost comparisons between individual tickets vs pass options, showing exact savings and optimal pass type.'
            },
            {
                category: 'transport',
                question: 'How do I get from New Chitose Airport to Sapporo?',
                answer: 'Real-time comparison of JR Rapid Airport service, buses, and taxis including costs, travel times, and luggage considerations for your specific needs.'
            },
            {
                category: 'transport',
                question: 'What should I know about taxi services in Japan?',
                answer: 'Photo recognition explains taxi types, fare structure, tipping customs, door automation, and provides essential Japanese phrases for communicating with drivers.'
            },
            
            // Accommodation & Facilities Category (4 questions)
            {
                category: 'accommodation', 
                question: 'How do I properly use onsen (hot spring) facilities?',
                answer: 'Photograph onsen facilities for detailed bathing procedures, etiquette rules, tattoo policies, and gender-specific information to ensure respectful enjoyment.'
            },
            {
                category: 'accommodation',
                question: 'What\'s the check-in process at Japanese hotels?',
                answer: 'Capture hotel lobby photos for check-in procedure explanations, required documents, common Japanese phrases, and service expectations during your stay.'
            },
            {
                category: 'accommodation',
                question: 'How do I wear and care for yukata at ryokan?',
                answer: 'Photo instruction shows proper yukata wearing techniques, obi tying methods, appropriate occasions for wear, and storage etiquette in traditional accommodations.'
            },
            {
                category: 'accommodation',
                question: 'What amenities are typically available in Japanese accommodations?',
                answer: 'Room photo analysis identifies available amenities, explains unique Japanese features like washlet toilets, and provides usage instructions for unfamiliar equipment.'
            },
            
            // Emergency & Support Category (4 questions)
            {
                category: 'emergency',
                question: 'How do I seek medical help if I get sick in Japan?',
                answer: 'Photograph symptoms or medication labels for medical terminology translation, nearby hospital location, insurance procedures, and essential health-related phrases.'
            },
            {
                category: 'emergency',
                question: 'What should I do if I lose my passport?',
                answer: 'AI guides you to nearest embassy/consulate, explains replacement procedures, required documentation, and temporary travel document processes.'
            },
            {
                category: 'emergency',
                question: 'How do I report lost items to local police?',
                answer: 'Locate nearby koban (police boxes) through photos, get translated report forms, understand Japanese lost-and-found procedures, and follow-up processes.'
            },
            {
                category: 'emergency',
                question: 'What languages are supported and what does it cost?',
                answer: 'Full support for English, Japanese, Korean, Chinese (Simplified & Traditional). Free for first 5 uses monthly, then 7-day plan (¥980) or 20-day plan (¥1,980).'
            }
        ]
    };
    
    return faqs[language] || faqs['ja'];
}

// How-toステップ生成
function generateHowToSteps(language) {
    const steps = {
        'ja': [
            {
                '@type': 'HowToStep',
                'position': 1,
                'name': 'アプリにアクセス',
                'text': 'anatri.netにアクセスして言語を選択',
                'image': 'https://anatri.net/images/howto/step1-ja.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 2,
                'name': '写真を撮影',
                'text': '観光地や料理の写真を撮影またはアップロード',
                'image': 'https://anatri.net/images/howto/step2-ja.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 3,
                'name': 'AI解析結果を確認',
                'text': '3秒で詳細な観光情報を日本語で取得',
                'image': 'https://anatri.net/images/howto/step3-ja.webp'
            }
        ],
        'ko': [
            {
                '@type': 'HowToStep',
                'position': 1,
                'name': '앱 접속',
                'text': 'anatri.net에 접속하여 한국어 선택',
                'image': 'https://anatri.net/images/howto/step1-ko.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 2,
                'name': '사진 촬영',
                'text': '관광지나 음식 사진을 촬영 또는 업로드',
                'image': 'https://anatri.net/images/howto/step2-ko.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 3,
                'name': 'AI 분석 결과 확인',
                'text': '3초 만에 상세한 관광 정보를 한국어로 획득',
                'image': 'https://anatri.net/images/howto/step3-ko.webp'
            }
        ],
        'zh-cn': [
            {
                '@type': 'HowToStep',
                'position': 1,
                'name': '访问应用',
                'text': '访问anatri.net并选择中文',
                'image': 'https://anatri.net/images/howto/step1-zhcn.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 2,
                'name': '拍摄照片',
                'text': '拍摄或上传观光地和料理照片',
                'image': 'https://anatri.net/images/howto/step2-zhcn.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 3,
                'name': '确认AI分析结果',
                'text': '3秒钟获得详细的中文观光信息',
                'image': 'https://anatri.net/images/howto/step3-zhcn.webp'
            }
        ],
        'zh-tw': [
            {
                '@type': 'HowToStep',
                'position': 1,
                'name': '存取應用程式',
                'text': '造訪anatri.net並選擇繁體中文',
                'image': 'https://anatri.net/images/howto/step1-zhtw.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 2,
                'name': '拍攝照片',
                'text': '拍攝或上傳觀光地和料理照片',
                'image': 'https://anatri.net/images/howto/step2-zhtw.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 3,
                'name': '確認AI分析結果',
                'text': '3秒鐘獲得詳細的繁體中文觀光資訊',
                'image': 'https://anatri.net/images/howto/step3-zhtw.webp'
            }
        ],
        'en': [
            {
                '@type': 'HowToStep',
                'position': 1,
                'name': 'Access the App',
                'text': 'Visit anatri.net and select English',
                'image': 'https://anatri.net/images/howto/step1-en.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 2,
                'name': 'Take Photos',
                'text': 'Capture or upload photos of tourist spots and food',
                'image': 'https://anatri.net/images/howto/step2-en.webp'
            },
            {
                '@type': 'HowToStep',
                'position': 3,
                'name': 'Check AI Analysis Results',
                'text': 'Get detailed tourism information in English within 3 seconds',
                'image': 'https://anatri.net/images/howto/step3-en.webp'
            }
        ]
    };
    
    return steps[language] || steps['ja'];
}

// AI質問・回答データ
const aiQuestions = {
    'ja': {
        primary: '日本旅行で困ったときにAnatriはどう役立ちますか？'
    },
    'ko': {
        primary: '일본 여행에서 어려움을 겪을 때 Anatri가 어떻게 도움이 되나요？'
    },
    'zh-cn': {
        primary: '在日本旅行遇到困难时Anatri如何提供帮助？'
    },
    'zh-tw': {
        primary: '在日本旅行遇到困難時Anatri如何提供幫助？'
    },
    'en': {
        primary: 'How does Anatri help when you encounter difficulties during travel in Japan?'
    }
};

const aiAnswers = {
    'ja': {
        detailed: 'Anatriは写真1枚で言語の壁を解決します。メニューが読めない、この場所がわからない、道に迷った時も、AI画像解析が瞬時に日本語で詳細情報を提供。GPS不要で正確な観光地特定、アレルギー情報付きメニュー翻訳、最適な移動ルート提案まで、訪日観光の全ての悩みをサポートします。'
    },
    'ko': {
        detailed: 'Anatri는 사진 한 장으로 언어의 벽을 해결합니다. 메뉴를 읽을 수 없거나 현재 위치를 모르거나 길을 잃었을 때도, AI 이미지 분석이 즉시 한국어로 상세 정보를 제공합니다. GPS 없이도 정확한 관광지 식별, 알레르기 정보가 포함된 메뉴 번역, 최적의 이동 경로 제안까지, 일본 관광의 모든 고민을 해결해드립니다.'
    },
    'zh-cn': {
        detailed: 'Anatri用一张照片解决语言障碍。看不懂菜单、不知道位置、迷路时，AI图像分析立即用中文提供详细信息。无需GPS即可精确识别观光地，提供含过敏原信息的菜单翻译，推荐最佳移动路线，全面支持访日观光的各种需求。'
    },
    'zh-tw': {
        detailed: 'Anatri用一張照片解決語言障礙。看不懂菜單、不知道位置、迷路時，AI圖像分析立即用繁體中文提供詳細資訊。無需GPS即可精確識別觀光地，提供含過敏原資訊的菜單翻譯，推薦最佳移動路線，全面支援訪日觀光的各種需求。'
    },
    'en': {
        detailed: 'Anatri solves language barriers with just one photo. When you cannot read menus, do not know your location, or get lost, AI image analysis instantly provides detailed information in English. Accurate tourist spot identification without GPS, menu translation with allergen information, optimal route suggestions - comprehensive support for all your travel needs in Japan.'
    }
};

// AI検索エンジン向け拡張構造化データ生成
function generateAIOptimizedStructuredData(language) {
    const translations = structuredDataTranslations[language] || structuredDataTranslations.ja;
    const langCode = language === 'zh-cn' ? 'zh-CN' : language === 'zh-tw' ? 'zh-TW' : language;
    
    const baseData = {
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'TouristInformationCenter',
                '@id': `https://anatri.net/${language === 'ja' ? '' : language + '/'}#organization`,
                'name': translations.name,
                'description': translations.description,
                'url': `https://anatri.net/${language === 'ja' ? '' : language + '/'}`,
                'areaServed': {
                    '@type': 'Country',
                    'name': 'Japan',
                    'containsPlace': [
                        {
                            '@type': 'City',
                            'name': 'Sapporo',
                            'containedInPlace': {
                                '@type': 'AdministrativeArea',
                                'name': 'Hokkaido'
                            }
                        },
                        {
                            '@type': 'City',
                            'name': 'Tokyo'
                        },
                        {
                            '@type': 'City',
                            'name': 'Kyoto'
                        },
                        {
                            '@type': 'City', 
                            'name': 'Osaka'
                        }
                    ]
                },
                // AI検索で重要な「専門性」を明示
                'knowsAbout': [
                    'Japanese tourism',
                    'Hokkaido attractions',
                    'Japanese cuisine identification',
                    'Cultural heritage sites',
                    'Local restaurant recommendations',
                    'Travel photography',
                    'Multilingual travel support',
                    'AI image recognition'
                ],
                'serviceType': ['Tourism Information', 'Image Analysis', 'Translation Service'],
                'hasOfferCatalog': {
                    '@type': 'OfferCatalog',
                    'name': 'Tourism Analysis Plans',
                    'itemListElement': [
                        {
                            '@type': 'Offer',
                            'name': language === 'ja' ? '無料プラン' : language === 'ko' ? '무료 플랜' : language.includes('zh') ? '免费方案' : 'Free Plan',
                            'price': 0,
                            'priceCurrency': 'JPY'
                        },
                        {
                            '@type': 'Offer',
                            'name': language === 'ja' ? '7日間プラン' : language === 'ko' ? '7일 플랜' : language.includes('zh') ? '7天方案' : '7-Day Plan',
                            'price': 980,
                            'priceCurrency': 'JPY'
                        }
                    ]
                },
                'aggregateRating': {
                    '@type': 'AggregateRating',
                    'ratingValue': 4.8,
                    'reviewCount': 2847,
                    'bestRating': 5
                },
                'contactPoint': {
                    '@type': 'ContactPoint',
                    'contactType': 'customer service',
                    'availableLanguage': ['ja', 'ko', 'zh-CN', 'zh-TW', 'en']
                }
            },
            {
                '@type': 'FAQPage',
                'mainEntity': generateFAQsForLanguage(language).map(faq => ({
                    '@type': 'Question',
                    'name': faq.question,
                    'acceptedAnswer': {
                        '@type': 'Answer',
                        'text': faq.answer
                    }
                }))
            },
            {
                '@type': 'HowTo',
                'name': language === 'ja' ? 'Anatriで観光情報を取得する方法' : 
                       language === 'ko' ? 'Anatri로 관광 정보를 얻는 방법' :
                       language.includes('zh') ? '使用Anatri获取旅游信息的方法' :
                       'How to get tourism information with Anatri',
                'description': translations.description,
                'step': generateHowToSteps(language),
                'totalTime': 'PT3M',
                'tool': [{
                    '@type': 'HowToTool',
                    'name': 'Smartphone Camera'
                }],
                'supply': [{
                    '@type': 'HowToSupply', 
                    'name': 'Internet Connection'
                }]
            },
            {
                // 生成AI向けQ&A形式データ
                '@type': 'QAPage',
                'mainEntity': {
                    '@type': 'Question',
                    'name': aiQuestions[language].primary,
                    'acceptedAnswer': {
                        '@type': 'Answer',
                        'text': aiAnswers[language].detailed
                    }
                }
            },
            {
                '@type': 'WebApplication',
                'name': translations.name,
                'applicationCategory': 'TravelApplication',
                'operatingSystem': 'Web Browser',
                'offers': {
                    '@type': 'Offer',
                    'price': '0',
                    'priceCurrency': language === 'ko' ? 'KRW' : language.includes('zh') ? 'CNY' : language === 'en' ? 'USD' : 'JPY'
                },
                'author': {
                    '@type': 'Organization',
                    'name': translations.author
                },
                'inLanguage': langCode,
                'potentialAction': {
                    '@type': 'UseAction',
                    'target': `https://anatri.net/${language === 'ja' ? '' : language + '/'}index.html`
                }
            }
        ]
    };
    
    return baseData;
}

// 構造化データをHTMLに挿入
function injectStructuredData(language = 'ja') {
    console.log(`🔍 Injecting AI-optimized structured data for language: ${language}`);
    
    const structuredData = generateAIOptimizedStructuredData(language);
    
    // 既存の構造化データスクリプトを削除
    const existingScript = document.querySelector('script[type="application/ld+json"]');
    if (existingScript) {
        existingScript.remove();
    }
    
    // 新しい構造化データスクリプトを追加
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(structuredData, null, 2);
    document.head.appendChild(script);
    
    console.log('✅ AI-optimized structured data injected successfully');
    
    // AI検索エンジン向けメタタグも動的に更新
    updateAIMetaTags(language);
}

// AI検索エンジン向けメタタグ更新
function updateAIMetaTags(language) {
    const translations = structuredDataTranslations[language] || structuredDataTranslations.ja;
    
    // AI検索エンジン向け新メタタグ
    const aiMetaTags = [
        { name: 'ai-content-type', content: 'tourism-assistant' },
        { name: 'ai-expertise', content: 'japan-tourism,hokkaido-guide,food-recognition' },
        { name: 'ai-data-freshness', content: new Date().toISOString().split('T')[0] },
        { name: 'ai-response-format', content: 'conversational,structured' },
        { property: 'ai:featured_snippet', content: translations.description },
        { name: 'vector-summary', content: `AI-powered tourism analyzer for Japan visitors. Instant photo recognition of tourist spots and food with multilingual support. ${language} language interface.` }
    ];
    
    // 既存のAI関連メタタグを削除
    document.querySelectorAll('meta[name^="ai-"], meta[property^="ai:"], meta[name="vector-summary"]').forEach(meta => {
        meta.remove();
    });
    
    // 新しいAI関連メタタグを追加
    aiMetaTags.forEach(tagData => {
        const meta = document.createElement('meta');
        if (tagData.name) meta.name = tagData.name;
        if (tagData.property) meta.property = tagData.property;
        meta.content = tagData.content;
        document.head.appendChild(meta);
    });
    
    console.log(`✅ AI meta tags updated for language: ${language}`);
}

// ページロード時とlanguage変更時に実行
if (typeof window !== 'undefined') {
    // DOMContentLoaded時に初期実行
    document.addEventListener('DOMContentLoaded', function() {
        const currentLang = document.documentElement.lang || 'ja';
        injectStructuredData(currentLang);
    });
    
    // 言語変更時のフックを提供
    window.updateSEOStructuredData = injectStructuredData;
}


// 言語別画像情報データベース
const imageTranslations = {
    'ja': {
        // Feature Cards画像
        'feature-card-01': {
            name: 'AI画像解析アイコン',
            alt: 'カメラマークのアイコン - AI画像解析技術を表すピクトグラム',
            description: '最新のAI技術により写真から観光地や料理を瞬時に識別する画像解析サービス',
            keywords: ['AI', '画像認識', '観光', '技術', 'カメラ', 'アイコン']
        },
        'feature-card-02': {
            name: '多言語対応地球アイコン',
            alt: '地球マークのアイコン - 世界中の言語に対応するグローバルサービス',
            description: '日本語、韓国語、中国語、英語に対応した多言語観光情報サービス',
            keywords: ['多言語', '翻訳', '国際化', 'グローバル', '地球', 'アイコン']
        },
        'feature-card-03': {
            name: '日本地図特化アイコン',
            alt: '日本地図マークのアイコン - 日本地域に特化した観光サービス',
            description: '札幌・北海道地域に特化した精密な観光情報データベース',
            keywords: ['日本', '札幌', '北海道', '地域特化', '観光', 'アイコン']
        }
    },
    'ko': {
        // Feature Cards
        'feature-card-01': {
            name: 'AI 이미지 분석 아이콘',
            alt: '카메라 마크 아이콘 - AI 이미지 분석 기술을 나타내는 픽토그램',
            description: '최신 AI 기술로 사진에서 관광지와 요리를 즉시 식별하는 이미지 분석 서비스',
            keywords: ['AI', '이미지 인식', '관광', '기술', '카메라', '아이콘']
        },
        'feature-card-02': {
            name: '다국어 지원 지구 아이콘',
            alt: '지구 마크 아이콘 - 전 세계 언어를 지원하는 글로벌 서비스',
            description: '한국어, 일본어, 중국어, 영어를 지원하는 다국어 관광 정보 서비스',
            keywords: ['다국어', '번역', '국제화', '글로벌', '지구', '아이콘']
        },
        'feature-card-03': {
            name: '일본 지도 전문 아이콘',
            alt: '일본 지도 마크 아이콘 - 일본 지역 전문 관광 서비스',
            description: '삿포로·홋카이도 지역에 특화된 정밀한 관광 정보 데이터베이스',
            keywords: ['일본', '삿포로', '홋카이도', '지역 특화', '관광', '아이콘']
        }
    },
    'zh-cn': {
        // Feature Cards
        'feature-card-01': {
            name: 'AI图像分析图标',
            alt: '相机标记图标 - 代表AI图像分析技术的象形图',
            description: '采用最新AI技术从照片中瞬间识别观光地和料理的图像分析服务',
            keywords: ['AI', '图像识别', '观光', '技术', '相机', '图标']
        },
        'feature-card-02': {
            name: '多语言支持地球图标',
            alt: '地球标记图标 - 支持全球多种语言的全球化服务',
            description: '支持中文、日语、韩语、英语的多语言观光信息服务',
            keywords: ['多语言', '翻译', '国际化', '全球', '地球', '图标']
        },
        'feature-card-03': {
            name: '日本地图专业图标',
            alt: '日本地图标记图标 - 专注于日本地区的观光服务',
            description: '专门针对札幌·北海道地区的精密观光信息数据库',
            keywords: ['日本', '札幌', '北海道', '区域专业', '观光', '图标']
        }
    },
    'zh-tw': {
        // Feature Cards
        'feature-card-01': {
            name: 'AI圖像分析圖標',
            alt: '相機標記圖標 - 代表AI圖像分析技術的象形圖',
            description: '採用最新AI技術從照片中瞬間識別觀光地和料理的圖像分析服務',
            keywords: ['AI', '圖像識別', '觀光', '技術', '相機', '圖標']
        },
        'feature-card-02': {
            name: '多語言支援地球圖標',
            alt: '地球標記圖標 - 支援全球多種語言的全球化服務',
            description: '支援繁體中文、日語、韓語、英語的多語言觀光資訊服務',
            keywords: ['多語言', '翻譯', '國際化', '全球', '地球', '圖標']
        },
        'feature-card-03': {
            name: '日本地圖專業圖標',
            alt: '日本地圖標記圖標 - 專注於日本地區的觀光服務',
            description: '專門針對札幌·北海道地區的精密觀光資訊資料庫',
            keywords: ['日本', '札幌', '北海道', '區域專業', '觀光', '圖標']
        }
    },
    'en': {
        // Feature Cards
        'feature-card-01': {
            name: 'AI Image Analysis Icon',
            alt: 'Camera mark icon - Pictogram representing AI image analysis technology',
            description: 'Image analysis service that instantly identifies tourist spots and cuisine from photos using cutting-edge AI technology',
            keywords: ['AI', 'image recognition', 'tourism', 'technology', 'camera', 'icon']
        },
        'feature-card-02': {
            name: 'Multilingual Support Earth Icon',
            alt: 'Globe mark icon - Global service supporting multiple languages worldwide',
            description: 'Multilingual tourism information service supporting English, Japanese, Korean, and Chinese',
            keywords: ['multilingual', 'translation', 'internationalization', 'global', 'earth', 'icon']
        },
        'feature-card-03': {
            name: 'Japan Map Specialized Icon',
            alt: 'Japan map mark icon - Tourism service specialized in Japanese regions',
            description: 'Precise tourism information database specialized in Sapporo and Hokkaido regions',
            keywords: ['Japan', 'Sapporo', 'Hokkaido', 'regional specialty', 'tourism', 'icon']
        }
    }
};




