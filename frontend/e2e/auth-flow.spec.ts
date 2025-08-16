import { test, expect } from '@playwright/test';

test.describe('Authentication Flow Tests - Phase 6.9', () => {
  
  test('Google login redirects from tourism-guide.html to login.html', async ({ page }) => {
    // メインページに移動
    await page.goto('/tourism-guide.html');
    
    // ページが正常に読み込まれることを確認（メインアプリのh1を指定）
    await expect(page.locator('h1[data-i18n="title"]')).toContainText('観光アナライザー');
    
    // 認証モーダルを開く（メインのログインボタンをクリック）
    await page.locator('#headerLoginBtn, .header-login-btn, button:has-text("ログイン")').first().click();
    await page.waitForTimeout(1500); // モーダル表示を十分に待機
    
    // Googleログインボタンをクリック（モーダル内の具体的なボタンを選択）
    await page.locator('#googleLoginBtn, .google-login-btn, button:has-text("Googleでログイン")').first().click();
    
    // login.htmlに遷移することを確認
    await expect(page).toHaveURL(/.*login\.html/);
    
    // login.htmlページの内容を確認
    await expect(page.locator('h1').first()).toContainText('観光アナライザー');
    await expect(page.locator('p:has-text("Googleアカウントでログイン処理中")')).toBeVisible();
    
    // 戻るリンクが存在することを確認
    await expect(page.locator('a:has-text("← 戻る")')).toBeVisible();
  });

  test('login.html auto-redirects to Cognito OAuth after 1 second', async ({ page }) => {
    // Consoleログを監視
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    
    // login.htmlに直接アクセス
    await page.goto('/login.html');
    
    // ページ内容の初期確認
    await expect(page.locator('h1').first()).toContainText('観光アナライザー');
    await expect(page.locator('p:has-text("Googleアカウントでログイン処理中")')).toBeVisible();
    
    // JavaScriptが実行される前にページのoriginを確認
    const currentOrigin = await page.evaluate(() => window.location.origin);
    console.log('Current origin:', currentOrigin);
    
    // 2秒待機後にCognito OAuth URLへのリダイレクトを確認（時間を延長）
    await page.waitForTimeout(2500);
    
    const currentUrl = page.url();
    console.log('Current URL after wait:', currentUrl);
    
    // Cognito OAuth URLへのリダイレクトを確認
    await expect(page.url()).toContain('ai-tourism-auth.auth.ap-northeast-1.amazoncognito.com');
    await expect(page.url()).toContain('identity_provider=Google');
    await expect(page.url()).toContain('client_id=2tctru78c2epl4mbhrt8asd55e');
    await expect(page.url()).toContain('response_type=code');
  });

  test('Email login modal appears and works unchanged', async ({ page }) => {
    // メインページに移動
    await page.goto('/tourism-guide.html');
    
    // ページ読み込み完了を待機
    await expect(page.locator('h1[data-i18n="title"]')).toContainText('観光アナライザー');
    
    // 認証モーダルを開く
    await page.locator('button:has-text("ログイン")').first().click();
    await page.waitForTimeout(1000);
    
    // モーダルが表示されたことを確認
    await expect(page.locator('button:has-text("メールでログイン")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Googleでログイン")').first()).toBeVisible();
    
    // メールでログインボタンをクリック
    await page.locator('button:has-text("メールでログイン")').first().click();
    await page.waitForTimeout(500);
    
    // メール入力フォームが表示されることを確認（リダイレクトを防ぐため早めにチェック）
    const emailInput = page.locator('input[type="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    
    await expect(emailInput).toBeVisible({ timeout: 3000 });
    await expect(passwordInput).toBeVisible({ timeout: 3000 });
  });

  test('Email authentication with yoshidaagri@gmail.com (basic form interaction)', async ({ page }) => {
    // メインページに移動
    await page.goto('/tourism-guide.html');
    
    // ページ読み込み完了を待機
    await expect(page.locator('h1[data-i18n="title"]')).toContainText('観光アナライザー');
    
    // 認証モーダルを開く
    await page.locator('button:has-text("ログイン")').first().click();
    await page.waitForTimeout(1000);
    
    // メールでログインボタンをクリック
    await page.locator('button:has-text("メールでログイン")').first().click();
    await page.waitForTimeout(500);
    
    // テスト用メールアドレスを入力（タイムアウトを短く設定）
    const emailInput = page.locator('input[type="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    
    await expect(emailInput).toBeVisible({ timeout: 3000 });
    await expect(passwordInput).toBeVisible({ timeout: 3000 });
    
    await emailInput.fill('yoshidaagri@gmail.com');
    await passwordInput.fill('test-password-for-ui-test');
    
    // フォームの値が正しく入力されていることを確認
    await expect(emailInput).toHaveValue('yoshidaagri@gmail.com');
    await expect(passwordInput).toHaveValue('test-password-for-ui-test');
    
    // ログインボタンが有効化されていることを確認（実際のログインは行わない）
    const loginButton = page.locator('button:has-text("ログイン")').first();
    await expect(loginButton).toBeVisible();
    await expect(loginButton).toBeEnabled();
  });

  test('Back button from login.html returns to tourism-guide.html', async ({ page }) => {
    // login.htmlに直接アクセス
    await page.goto('/login.html');
    
    // 戻るリンクをクリック
    await page.locator('a:has-text("← 戻る")').click();
    
    // tourism-guide.htmlに戻ることを確認
    await expect(page).toHaveURL(/.*tourism-guide\.html/);
    await expect(page.locator('h1[data-i18n="title"]')).toContainText('観光アナライザー');
  });

  test('Page loads and basic functionality works on mobile viewport', async ({ page }) => {
    // モバイルビューポートでテスト
    await page.setViewportSize({ width: 375, height: 667 });
    
    // メインページに移動
    await page.goto('/tourism-guide.html');
    
    // ページが正常に読み込まれることを確認
    await expect(page.locator('h1[data-i18n="title"]')).toContainText('観光アナライザー');
    
    // 認証ボタンがモバイルでも表示されることを確認
    const loginButton = page.locator('button:has-text("ログイン")').first();
    await expect(loginButton).toBeVisible();
    
    // モーダルを開く
    await loginButton.click();
    await page.waitForTimeout(1000);
    
    // Googleログインボタンが表示されることを確認
    await expect(page.locator('button:has-text("Googleでログイン")').first()).toBeVisible();
    
    // メールログインボタンが表示されることを確認
    await expect(page.locator('button:has-text("メールでログイン")').first()).toBeVisible();
  });
});