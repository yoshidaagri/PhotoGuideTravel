const { test, expect } = require('@playwright/test');

test.describe('Phase 6.9.5 メール認証多言語化テスト', () => {
  const URL = 'https://d22ztxm5q1c726.cloudfront.net/tourism-guide.html';

  test('1. 基本画面表示テスト', async ({ page }) => {
    await page.goto(URL);
    
    // ページタイトル確認（ログイン画面のh1を特定）
    await expect(page.locator('.login-title')).toContainText('🏔️');
    
    // 基本ボタンの表示確認
    await expect(page.locator('#googleLoginBtn')).toBeVisible();
    await expect(page.locator('#emailLoginBtn')).toBeVisible();
    
    // メールログインボタンのテキスト確認
    await expect(page.locator('#emailLoginBtn')).toContainText('メールでログイン');
    
    console.log('✅ 基本画面表示テスト - 成功');
  });

  test('2. メール認証画面遷移テスト', async ({ page }) => {
    await page.goto(URL);
    
    // メールログインボタンをクリック
    await page.click('#emailLoginBtn');
    
    // メール認証画面の要素確認
    await expect(page.locator('.login-title')).toContainText('🏔️');
    await expect(page.locator('.login-subtitle')).toContainText('観光アナライザーにログイン');
    
    // 言語選択ラジオボタンの確認
    await expect(page.locator('input[name="authLang"][value="ja"]')).toBeVisible();
    await expect(page.locator('input[name="authLang"][value="ko"]')).toBeVisible();
    await expect(page.locator('input[name="authLang"][value="zh"]')).toBeVisible();
    await expect(page.locator('input[name="authLang"][value="tw"]')).toBeVisible();
    await expect(page.locator('input[name="authLang"][value="en"]')).toBeVisible();
    
    // フォーム要素の確認
    await expect(page.locator('#loginEmail')).toBeVisible();
    await expect(page.locator('#loginPassword')).toBeVisible();
    
    console.log('✅ メール認証画面遷移テスト - 成功');
  });

  test('3. 日本語表示テスト', async ({ page }) => {
    await page.goto(URL);
    await page.click('#emailLoginBtn');
    
    // 日本語が選択されていることを確認
    await expect(page.locator('input[name="authLang"][value="ja"]')).toBeChecked();
    
    // プレースホルダーテキストの確認
    await expect(page.locator('#loginEmail')).toHaveAttribute('placeholder', 'メールアドレス');
    await expect(page.locator('#loginPassword')).toHaveAttribute('placeholder', 'パスワード');
    
    // ボタンテキストの確認
    await expect(page.locator('#loginModeBtn')).toContainText('ログイン');
    await expect(page.locator('#signupModeBtn')).toContainText('新規登録');
    
    console.log('✅ 日本語表示テスト - 成功');
  });

  test('4. 韓国語切り替えテスト', async ({ page }) => {
    await page.goto(URL);
    await page.click('#emailLoginBtn');
    
    // 韓国語を選択
    await page.click('input[name="authLang"][value="ko"]');
    
    // プレースホルダーの変更を確認
    await expect(page.locator('#loginEmail')).toHaveAttribute('placeholder', '이메일 주소');
    await expect(page.locator('#loginPassword')).toHaveAttribute('placeholder', '비밀번호');
    
    // タイトルの変更を確認
    await expect(page.locator('.login-subtitle')).toContainText('관광 분석기에 로그인');
    
    // ボタンテキストの確認
    await expect(page.locator('#loginModeBtn')).toContainText('로그인');
    await expect(page.locator('#signupModeBtn')).toContainText('회원가입');
    
    console.log('✅ 韓国語切り替えテスト - 成功');
  });

  test('5. 中国語（簡体字）切り替えテスト', async ({ page }) => {
    await page.goto(URL);
    await page.click('#emailLoginBtn');
    
    // 中国語（簡体字）を選択
    await page.click('input[name="authLang"][value="zh"]');
    
    // プレースホルダーの変更を確認
    await expect(page.locator('#loginEmail')).toHaveAttribute('placeholder', '邮箱地址');
    await expect(page.locator('#loginPassword')).toHaveAttribute('placeholder', '密码');
    
    // タイトルの変更を確認
    await expect(page.locator('.login-subtitle')).toContainText('登录旅游分析器');
    
    // ボタンテキストの確認
    await expect(page.locator('#loginModeBtn')).toContainText('登录');
    await expect(page.locator('#signupModeBtn')).toContainText('注册账户');
    
    console.log('✅ 中国語（簡体字）切り替えテスト - 成功');
  });

  test('6. 中国語（繁体字）切り替えテスト', async ({ page }) => {
    await page.goto(URL);
    await page.click('#emailLoginBtn');
    
    // 中国語（繁体字）を選択
    await page.click('input[name="authLang"][value="tw"]');
    
    // プレースホルダーの変更を確認
    await expect(page.locator('#loginEmail')).toHaveAttribute('placeholder', '電子郵件地址');
    await expect(page.locator('#loginPassword')).toHaveAttribute('placeholder', '密碼');
    
    // タイトルの変更を確認
    await expect(page.locator('.login-subtitle')).toContainText('登入觀光分析器');
    
    // ボタンテキストの確認
    await expect(page.locator('#loginModeBtn')).toContainText('登入');
    await expect(page.locator('#signupModeBtn')).toContainText('註冊帳號');
    
    console.log('✅ 中国語（繁体字）切り替えテスト - 成功');
  });

  test('7. 英語切り替えテスト', async ({ page }) => {
    await page.goto(URL);
    await page.click('#emailLoginBtn');
    
    // 英語を選択
    await page.click('input[name="authLang"][value="en"]');
    
    // プレースホルダーの変更を確認
    await expect(page.locator('#loginEmail')).toHaveAttribute('placeholder', 'Email address');
    await expect(page.locator('#loginPassword')).toHaveAttribute('placeholder', 'Password');
    
    // タイトルの変更を確認
    await expect(page.locator('.login-subtitle')).toContainText('Sign in to Tourism Analyzer');
    
    // ボタンテキストの確認
    await expect(page.locator('#loginModeBtn')).toContainText('Sign in');
    await expect(page.locator('#signupModeBtn')).toContainText('Sign up');
    
    console.log('✅ 英語切り替えテスト - 成功');
  });

  test('8. ログイン/サインアップ切り替えテスト', async ({ page }) => {
    await page.goto(URL);
    await page.click('#emailLoginBtn');
    
    // 初期状態でログインフォームが表示されていることを確認
    await expect(page.locator('#loginForm')).toBeVisible();
    await expect(page.locator('#signupForm')).toBeHidden();
    
    // サインアップモードに切り替え
    await page.click('#signupModeBtn');
    
    // サインアップフォームが表示されることを確認
    await expect(page.locator('#loginForm')).toBeHidden();
    await expect(page.locator('#signupForm')).toBeVisible();
    
    // 確認パスワードフィールドの存在確認
    await expect(page.locator('#confirmPassword')).toBeVisible();
    
    // ログインモードに戻す
    await page.click('#loginModeBtn');
    
    // ログインフォームが再表示されることを確認
    await expect(page.locator('#loginForm')).toBeVisible();
    await expect(page.locator('#signupForm')).toBeHidden();
    
    console.log('✅ ログイン/サインアップ切り替えテスト - 成功');
  });

  test('9. 戻るボタンテスト（既存機能影響確認）', async ({ page }) => {
    await page.goto(URL);
    
    // メール認証画面に遷移
    await page.click('#emailLoginBtn');
    
    // 戻るボタンをクリック
    await page.click('button:has-text("ログインに戻る")');
    
    // 元の画面に戻ったことを確認
    await expect(page.locator('#googleLoginBtn')).toBeVisible();
    await expect(page.locator('#emailLoginBtn')).toBeVisible();
    
    console.log('✅ 戻るボタンテスト - 成功');
  });

  test('10. 言語選択の永続化テスト', async ({ page }) => {
    await page.goto(URL);
    await page.click('#emailLoginBtn');
    
    // 英語を選択
    await page.click('input[name="authLang"][value="en"]');
    
    // sessionStorageに保存されているか確認
    const selectedLanguage = await page.evaluate(() => sessionStorage.getItem('selectedLanguage'));
    expect(selectedLanguage).toBe('en');
    
    // 戻って再度メール認証画面に遷移
    await page.click('button:has-text("Back to Login")');
    await page.click('#emailLoginBtn');
    
    // 英語が選択されたままか確認
    await expect(page.locator('input[name="authLang"][value="en"]')).toBeChecked();
    await expect(page.locator('#loginEmail')).toHaveAttribute('placeholder', 'Email address');
    
    console.log('✅ 言語選択の永続化テスト - 成功');
  });
});