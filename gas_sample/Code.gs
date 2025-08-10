// ウズベキスタン観光・店舗アナライザー - メインコード

function doGet() {
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

// プロパティに必要な設定をすべて保存
function setupAllProperties() {
  const properties = PropertiesService.getScriptProperties();
  
  // 以下の値を実際の値に置き換えてください
  properties.setProperties({
    'GEMINI_API_KEY': 'YOUR_GEMINI_API_KEY_HERE',
    'GEMINI_API_ENDPOINT': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent',
    'DRIVE_FOLDER_ID': 'YOUR_DRIVE_FOLDER_ID_HERE',
    'SPREADSHEET_ID': 'YOUR_SPREADSHEET_ID_HERE'
  });
  
  console.log('すべてのプロパティが設定されました');
}

// 店舗・観光施設分析機能（統合版）
function analyzeStoreAndTourism(imageData) {
  const prompt = `
  この画像に写っているウズベキスタンの店舗・施設・観光地について、以下の形式で日本語で回答してください：

  【基本情報】
  - 名称・場所：
  - 種類：（レストラン、バザール、モスク、霊廟、博物館など）
  - 歴史・背景：（観光地の場合）
  - 主な商品・サービス：（店舗の場合）
  - 看板の意味：（ウズベク語/ロシア語がある場合）

  【評価・おすすめ情報】
  - おすすめ度：★★★★☆（5段階）
  - 見どころ・特徴：
  - ベストタイム：（時間帯・季節）
  - 写真撮影スポット：
  - 注意点・コツ：

  【料金・アクセス情報】
  - 入場料・価格帯：（ウズベクスム・円換算目安）
  - 追加料金：（ガイド・写真撮影・特別メニューなど）
  - アクセス方法：（交通手段・所要時間）
  - 営業時間：
  - 周辺の見どころ：

  300文字以内で、日本人旅行者向けに親しみやすく回答してください。
  `;
  
  const result = callGeminiAPI(prompt, imageData);
  saveToHistory('店舗・観光分析', result, imageData);
  return result;
}

// 看板分析機能
function analyzeSignboard(imageData) {
  const prompt = `
  この画像に写っている看板・メニュー・文字について、以下の形式で日本語で詳しく回答してください：

  【文字・言語分析と翻訳】
  - ウズベク語（ラテン文字）：読み取った文字 → 日本語翻訳
  - キリル文字（ロシア語/ウズベク語）：読み取った文字 → 日本語翻訳
  - アラビア文字：読み取った文字 → 日本語翻訳
  - 英語：読み取った内容 → 日本語翻訳

  【メニュー・料理の場合】
  - 料理名：現地語 → 日本語翻訳
  - 料理の説明：どんな料理か詳しく
  - 価格：ウズベクスム → 円換算目安
  - おすすめ度：★★★★☆（5段階）

  【看板・店舗情報の場合】
  - 店舗・施設名：現地語 → 日本語翻訳
  - 業種・サービス内容：
  - 営業時間・料金（もしあれば）：

  【旅行者向けアドバイス】
  - 注文方法や利用のコツ：
  - 観光客が知っておくべきポイント：
  - 現地での一般的な価格帯：

  300文字以内で、現地語が分からない日本人旅行者向けに親しみやすく翻訳・説明してください。
  `;
  
  const result = callGeminiAPI(prompt, imageData);
  saveToHistory('看板分析', result, imageData);
  return result;
}

// Gemini API共通呼び出し関数
function callGeminiAPI(prompt, imageData) {
  const apiKey = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  const endpoint = PropertiesService.getScriptProperties().getProperty('GEMINI_API_ENDPOINT') || 
    'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent';
  
  if (!apiKey || apiKey === 'YOUR_GEMINI_API_KEY_HERE') {
    throw new Error('Gemini APIキーが設定されていません。setupAllProperties()を実行してください。');
  }
  
  const url = `${endpoint}?key=${apiKey}`;
  
  const payload = {
    contents: [{
      parts: [
        {text: prompt},
        {
          inline_data: {
            mime_type: "image/jpeg", 
            data: imageData
          }
        }
      ]
    }],
    generationConfig: {
      temperature: 0.3,
      maxOutputTokens: 300,
      topP: 0.2
    }
  };
  
  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify(payload)
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const responseText = response.getContentText();
    const data = JSON.parse(responseText);
    
    if (data.candidates && data.candidates.length > 0) {
      return data.candidates[0].content.parts[0].text;
    } else {
      throw new Error('分析結果を取得できませんでした');
    }
  } catch (error) {
    console.error('Gemini API Error:', error);
    throw new Error('画像の分析中にエラーが発生しました: ' + error.toString());
  }
}

// Google Driveに画像を保存
function saveToGoogleDrive(imageData, filename) {
  try {
    const folderId = PropertiesService.getScriptProperties().getProperty('DRIVE_FOLDER_ID');
    
    if (!folderId || folderId === 'YOUR_DRIVE_FOLDER_ID_HERE') {
      console.log('Google Drive フォルダIDが設定されていないため、画像保存をスキップします');
      return null;
    }
    
    const folder = DriveApp.getFolderById(folderId);
    const blob = Utilities.newBlob(Utilities.base64Decode(imageData), 'image/jpeg', filename);
    const file = folder.createFile(blob);
    
    // ファイルを共有可能にする
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    
    return file.getUrl();
  } catch (error) {
    console.error('Google Drive保存エラー:', error);
    return null;
  }
}

// スプレッドシートに履歴を保存
function saveToHistory(analysisType, result, imageData) {
  try {
    console.log('履歴保存開始:', analysisType);
    const spreadsheetId = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
    
    if (!spreadsheetId || spreadsheetId === 'YOUR_SPREADSHEET_ID_HERE') {
      console.log('スプレッドシートIDが設定されていないため、履歴保存をスキップします');
      return { success: false, message: 'スプレッドシートIDが未設定' };
    }
    
    console.log('スプレッドシートにアクセス中...', spreadsheetId);
    const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    let sheet = spreadsheet.getSheetByName('分析履歴');
    
    // シートが存在しない場合は作成
    if (!sheet) {
      console.log('分析履歴シートを作成中...');
      sheet = spreadsheet.insertSheet('分析履歴');
      // ヘッダー行を追加
      sheet.getRange(1, 1, 1, 6).setValues([['日時', '分析種類', '結果', '画像URL', 'ユーザー', 'ステータス']]);
      sheet.getRange(1, 1, 1, 6).setFontWeight('bold');
      sheet.getRange(1, 1, 1, 6).setBackground('#e1f5fe');
    }
    
    // 画像をGoogle Driveに保存（非同期風に）
    const timestamp = new Date();
    const filename = `analysis_${analysisType}_${timestamp.getTime()}.jpg`;
    let imageUrl = '処理中';
    let driveStatus = 'OK';
    
    try {
      imageUrl = saveToGoogleDrive(imageData, filename);
      if (!imageUrl) {
        imageUrl = 'Drive保存失敗';
        driveStatus = 'Drive未設定';
      }
    } catch (driveError) {
      console.error('Drive保存エラー:', driveError);
      imageUrl = 'Drive保存エラー';
      driveStatus = 'Drive接続失敗';
    }
    
    // ユーザー情報を安全に取得
    let userEmail = '匿名ユーザー';
    try {
      userEmail = Session.getActiveUser().getEmail() || '匿名ユーザー';
    } catch (userError) {
      console.log('ユーザー情報取得失敗:', userError);
    }
    
    // 履歴データを追加
    const newRow = [
      timestamp,
      analysisType,
      result.substring(0, 500), // 長すぎる結果を制限
      imageUrl,
      userEmail,
      driveStatus
    ];
    
    console.log('データを行に追加中...', newRow);
    sheet.appendRow(newRow);
    
    // 列幅を自動調整（エラーが起きやすいので try-catch）
    try {
      sheet.autoResizeColumns(1, 6);
    } catch (resizeError) {
      console.log('列幅調整に失敗しましたが、データは保存されました:', resizeError);
    }
    
    console.log('履歴保存完了');
    return { success: true, message: '履歴保存完了' };
    
  } catch (error) {
    console.error('履歴保存エラー:', error);
    console.error('エラー詳細:', error.toString());
    return { success: false, message: `保存エラー: ${error.toString()}` };
  }
}

// 履歴を取得する関数（フロントエンドから呼び出し可能）
function getAnalysisHistory(limit = 50) {
  try {
    console.log('履歴取得開始, limit:', limit);
    const spreadsheetId = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
    
    if (!spreadsheetId || spreadsheetId === 'YOUR_SPREADSHEET_ID_HERE') {
      console.log('スプレッドシートIDが未設定');
      return [];
    }
    
    console.log('スプレッドシートにアクセス中:', spreadsheetId);
    const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    const sheet = spreadsheet.getSheetByName('分析履歴');
    
    if (!sheet) {
      console.log('分析履歴シートが存在しません');
      return [];
    }
    
    const lastRow = sheet.getLastRow();
    console.log('シートの最終行:', lastRow);
    
    if (lastRow <= 1) {
      console.log('データがありません');
      return [];
    }
    
    const startRow = Math.max(2, lastRow - limit + 1);
    const numRows = lastRow - startRow + 1;
    console.log('データ取得範囲:', startRow, 'から', numRows, '行');
    
    const data = sheet.getRange(startRow, 1, numRows, 6).getValues(); // 6列に拡張
    console.log('取得したデータ行数:', data.length);
    
    // 新しい順に並び替え（全て文字列に変換してGASの制限を回避）
    const result = data.reverse().map(row => ({
      date: row[0] ? row[0].toString() : '',
      type: row[1] ? row[1].toString() : '',
      result: row[2] ? row[2].toString() : '',
      imageUrl: row[3] ? row[3].toString() : '',
      user: row[4] ? row[4].toString() : '',
      status: row[5] ? row[5].toString() : 'OK'
    }));
    
    console.log('履歴取得完了, 件数:', result.length);
    console.log('サンプルデータ:', JSON.stringify(result[0] || {}));
    
    return result;
    
  } catch (error) {
    console.error('履歴取得エラー:', error);
    return [];
  }
}

// 設定状況を確認する関数
function checkSetup() {
  const properties = PropertiesService.getScriptProperties();
  const geminiKey = properties.getProperty('GEMINI_API_KEY');
  const geminiEndpoint = properties.getProperty('GEMINI_API_ENDPOINT');
  const driveFolder = properties.getProperty('DRIVE_FOLDER_ID');
  const spreadsheet = properties.getProperty('SPREADSHEET_ID');
  
  return {
    gemini: geminiKey && geminiKey !== 'YOUR_GEMINI_API_KEY_HERE',
    endpoint: geminiEndpoint || 'デフォルト値使用',
    drive: driveFolder && driveFolder !== 'YOUR_DRIVE_FOLDER_ID_HERE',
    spreadsheet: spreadsheet && spreadsheet !== 'YOUR_SPREADSHEET_ID_HERE'
  };
}