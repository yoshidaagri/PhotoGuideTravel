import { defineConfig, devices } from '@playwright/test';

/**
 * Tourism Analyzer Playwright E2E Test Configuration
 * CloudFront本番環境での自動テスト設定
 */
export default defineConfig({
  // テストファイルの場所
  testDir: './tests',
  
  // 全体のタイムアウト設定
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  
  // テスト並列実行設定
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  // レポート設定
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['line']
  ],
  
  // 全テストで使用する設定
  use: {
    // 本番CloudFront URL
    baseURL: 'https://d22ztxm5q1c726.cloudfront.net',
    
    // ブラウザ設定
    headless: true,
    viewport: { width: 1280, height: 720 },
    
    // アクション設定
    actionTimeout: 10000,
    navigationTimeout: 30000,
    
    // スクリーンショット・動画設定
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // ネットワーク設定
    ignoreHTTPSErrors: false,
  },

  // テスト対象ブラウザ設定
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    
    // モバイル対応テスト
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // ローカル開発サーバー設定（必要時）
  webServer: undefined,
});