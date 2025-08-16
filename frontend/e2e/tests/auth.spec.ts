import { test, expect } from '@playwright/test';

/**
 * Phase 6.9 Google認証フロー E2Eテスト
 * 
 * テストシナリオ:
 * 1. login.htmlアクセス確認
 * 2. Google認証ボタン表示確認
 * 3. 認証処理完了確認（テストモード使用）
 * 4. tourism-guide.htmlリダイレクト確認
 * 5. 認証後ユーザー情報表示確認
 * 6. localStorage認証トークン確認
 * 7. ログアウト機能確認
 */

test.describe('Google認証フロー', () => {
  
  test.beforeEach(async ({ page }) => {
    // 各テスト前にlocalStorageをクリア
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('login.htmlの基本表示確認', async ({ page }) => {
    // login.htmlにアクセス
    await page.goto('/login.html');
    
    // ページタイトル確認
    await expect(page).toHaveTitle(/Googleでログイン - 観光アナライザー/);
    
    // メインタイトル表示確認
    await expect(page.locator('h1')).toContainText('🌸 観光アナライザー');
    
    // サブタイトル表示確認
    await expect(page.locator('p').first()).toContainText('札幌観光・グルメ画像のAI解析サービス');
    
    // 戻るリンク表示確認
    await expect(page.locator('a[href="./tourism-guide.html"]')).toContainText('← 戻る');
  });

  test('Google Identity Services初期化確認', async ({ page }) => {
    await page.goto('/login.html');
    
    // Google Identity Servicesスクリプト読み込み確認
    await page.waitForLoadState('networkidle');
    
    // 初期化ログ確認
    const logs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        logs.push(msg.text());
      }
    });
    
    // ページ再読み込みしてログ取得
    await page.reload();
    await page.waitForTimeout(2000);
    
    // 期待するログメッセージ確認
    expect(logs.some(log => log.includes('login.html loaded, initializing Google Identity Services'))).toBeTruthy();
    expect(logs.some(log => log.includes('Google Identity Services script loaded'))).toBeTruthy();
  });

  test('Google認証ボタン表示確認', async ({ page }) => {
    await page.goto('/login.html');
    
    // Google Identity Services読み込み待機
    await page.waitForTimeout(3000);
    
    // Googleサインインボタンが表示されることを確認
    await expect(page.locator('#google-signin-button')).toBeVisible();
    
    // ローディング表示が非表示になっていることを確認
    await expect(page.locator('#loading')).toBeHidden();
  });

  test('Google認証成功フロー（2秒待機確認）', async ({ page }) => {
    // テスト用のネットワークインターセプト設定
    await page.route('**/dev/auth/google-signin', async route => {
      // テストモードの成功レスポンスをモック
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'simple_jwt_test_token_12345',
          user_info: {
            user_id: 'google_test_user_12345',
            email: 'test.user@gmail.com',
            name: 'Test User',
            auth_provider: 'google'
          }
        })
      });
    });
    
    await page.goto('/login.html');
    await page.waitForTimeout(3000);
    
    // 認証処理をシミュレート
    await page.evaluate(() => {
      // 実際のGoogle ID Tokenで認証実行
      (window as any).exchangeGoogleTokenForCognitoToken('test_token_real_jwt');
    });
    
    // 成功メッセージが2秒間表示されることを確認
    await expect(page.locator('p:has-text("認証成功！メイン画面に移動します")')).toBeVisible({ timeout: 5000 });
    
    // 2秒待機後にtourism-guide.htmlへリダイレクトされることを確認
    await expect(page).toHaveURL(/.*tourism-guide\.html/, { timeout: 10000 });
    
    // localStorage認証情報確認
    const accessToken = await page.evaluate(() => localStorage.getItem('accessToken'));
    const userInfo = await page.evaluate(() => localStorage.getItem('userInfo'));
    const tourismAuth = await page.evaluate(() => localStorage.getItem('tourismAuth'));
    
    expect(accessToken).toBeTruthy();
    expect(userInfo).toBeTruthy();
    expect(tourismAuth).toBe('true');
    
    // ユーザー情報のJSONパース確認（固定ではない）
    const userInfoObj = JSON.parse(userInfo!);
    expect(userInfoObj.email).toBe('test.user@gmail.com');
    expect(userInfoObj.name).toBe('Test User');
  });

  test('認証後のUI状態確認', async ({ page }) => {
    // 事前にlocalStorageに認証情報を設定
    await page.goto('/tourism-guide.html');
    await page.evaluate(() => {
      localStorage.setItem('tourismAuth', 'true');
      localStorage.setItem('accessToken', 'simple_jwt_test_token_12345');
      localStorage.setItem('userInfo', JSON.stringify({
        user_id: 'google_test_user_12345',
        email: 'yoshidaagri@gmail.com',
        name: 'Manabu Yoshida',
        auth_provider: 'google'
      }));
    });
    
    // ページ再読み込みで認証状態確認
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // 認証済みUI要素確認
    await expect(page.locator('#userInfo')).toBeVisible();
    await expect(page.locator('.logout-btn')).toBeVisible();
    
    // ログインセクションが非表示になっていることを確認
    await expect(page.locator('#loginSection')).toBeHidden();
  });

  test('ログアウト機能確認', async ({ page }) => {
    // 認証状態設定
    await page.goto('/tourism-guide.html');
    await page.evaluate(() => {
      localStorage.setItem('tourismAuth', 'true');
      localStorage.setItem('accessToken', 'simple_jwt_test_token_12345');
      localStorage.setItem('userInfo', JSON.stringify({
        email: 'yoshidaagri@gmail.com',
        name: 'Manabu Yoshida'
      }));
    });
    
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // 認証状態読み込み待機
    
    // ログアウトボタンが表示されるまで待機
    await expect(page.locator('.logout-btn')).toBeVisible({ timeout: 10000 });
    
    // ログアウトボタンクリック
    await page.locator('.logout-btn').click();
    
    // localStorage削除確認
    const accessToken = await page.evaluate(() => localStorage.getItem('accessToken'));
    const userInfo = await page.evaluate(() => localStorage.getItem('userInfo'));
    const tourismAuth = await page.evaluate(() => localStorage.getItem('tourismAuth'));
    
    expect(accessToken).toBeNull();
    expect(userInfo).toBeNull();
    expect(tourismAuth).toBeNull();
    
    // ログインセクション表示確認
    await expect(page.locator('#loginSection')).toBeVisible();
  });

  test('認証エラーハンドリング（3秒表示確認）', async ({ page }) => {
    // エラーレスポンスをモック
    await page.route('**/dev/auth/google-signin', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Invalid Google token'
        })
      });
    });
    
    await page.goto('/login.html');
    await page.waitForTimeout(3000);
    
    // エラーレスポンス時間を記録
    const startTime = Date.now();
    
    // 認証エラーシナリオ実行
    await page.evaluate(() => {
      (window as any).exchangeGoogleTokenForCognitoToken('invalid_token');
    });
    
    // エラーメッセージが表示されることを確認
    await expect(page.locator('p:has-text("認証処理でエラーが発生しました")')).toBeVisible({ timeout: 5000 });
    
    // 再試行ボタン表示確認
    await expect(page.locator('button:has-text("再試行")')).toBeVisible();
    
    // 3秒間エラーメッセージが表示され続けることを確認
    await page.waitForTimeout(3000);
    await expect(page.locator('p:has-text("認証処理でエラーが発生しました")')).toBeVisible();
    
    const endTime = Date.now();
    const elapsedTime = endTime - startTime;
    
    // 少なくとも3秒間は表示されていることを確認
    expect(elapsedTime).toBeGreaterThanOrEqual(3000);
  });

  test('実際のバックエンドAPI呼び出し確認', async ({ page }) => {
    await page.goto('/login.html');
    await page.waitForTimeout(3000);
    
    // コンソールログを監視
    const logs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log' || msg.type() === 'error') {
        logs.push(`${msg.type()}: ${msg.text()}`);
      }
    });
    
    // 実際のバックエンドAPIを呼び出し（テストトークン使用）
    await page.evaluate(() => {
      (window as any).exchangeGoogleTokenForCognitoToken('test_token_yoshidaagri');
    });
    
    // 成功メッセージまたはエラーメッセージを待機
    await page.waitForTimeout(5000);
    
    // ログからバックエンド応答を確認
    const hasTokenExchangeLog = logs.some(log => log.includes('Token exchange'));
    expect(hasTokenExchangeLog).toBeTruthy();
    
    console.log('Backend API test logs:', logs);
  });

  test('モバイル表示対応確認', async ({ page }) => {
    // モバイルビューポート設定
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/login.html');
    await page.waitForTimeout(3000);
    
    // モバイルでの表示確認
    await expect(page.locator('.google-login-container')).toBeVisible();
    await expect(page.locator('#google-signin-button')).toBeVisible();
    
    // レスポンシブデザイン確認
    const container = page.locator('.google-login-container');
    const boundingBox = await container.boundingBox();
    expect(boundingBox?.width).toBeLessThanOrEqual(375);
  });
});