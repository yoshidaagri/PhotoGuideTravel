/**
 * Authentication Module for Tourism Analyzer v1.3
 * 認証専用ロジック - index.html用
 */

// Global authentication state
let currentUser = null;
let isAuthenticated = false;

/**
 * Check authentication status on page load
 * 認証状態確認（ページロード時）
 */
async function checkAuthenticationStatus() {
    console.log('🔐 Checking authentication status...');
    
    try {
        // Get stored authentication data
        const tourismAuth = localStorage.getItem('tourismAuth');
        const accessToken = localStorage.getItem('accessToken');
        const userInfo = localStorage.getItem('userInfo');
        
        if (!tourismAuth || !accessToken) {
            console.log('❌ No authentication data found');
            return false;
        }
        
        console.log('📊 Found stored auth data, verifying with server...');
        
        // Check for emergency login token
        if (accessToken === 'emergency-login-token-dev') {
            console.log('🛠️ Emergency login detected, bypassing server verification');
            
            // Use stored user info for emergency login
            if (userInfo) {
                const storedUserInfo = JSON.parse(userInfo);
                currentUser = storedUserInfo;
                isAuthenticated = true;
                console.log('✅ Emergency authentication successful:', storedUserInfo.email);
                return true;
            } else {
                // Fallback emergency user
                currentUser = {
                    email: 'emergency@example.com',
                    name: 'Emergency User',
                    auth_provider: 'emergency'
                };
                isAuthenticated = true;
                console.log('✅ Emergency authentication successful (fallback)');
                return true;
            }
        }
        
        // Verify token with backend for real tokens
        const response = await fetch('https://f4n095fm2j.execute-api.ap-northeast-1.amazonaws.com/dev/auth/user-info', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const serverUserInfo = await response.json();
            console.log('✅ Authentication verified:', serverUserInfo.email);
            
            // Set global authentication state
            currentUser = serverUserInfo;
            isAuthenticated = true;
            
            // Update stored user info if needed
            if (userInfo) {
                const storedUserInfo = JSON.parse(userInfo);
                if (storedUserInfo.email === serverUserInfo.email) {
                    console.log('📧 Stored user info matches server data');
                } else {
                    console.log('🔄 Updating stored user info');
                    localStorage.setItem('userInfo', JSON.stringify(serverUserInfo));
                }
            }
            
            return true;
            
        } else {
            console.log('⚠️ Token validation failed:', response.status);
            await clearAuthenticationData();
            return false;
        }
        
    } catch (error) {
        console.error('🚨 Authentication check error:', error);
        await clearAuthenticationData();
        return false;
    }
}

/**
 * Clear all authentication data
 * 認証データクリア
 */
async function clearAuthenticationData() {
    console.log('🧹 Clearing authentication data...');
    
    // Clear localStorage
    localStorage.removeItem('tourismAuth');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userInfo');
    
    // Clear sessionStorage (for backward compatibility)
    sessionStorage.removeItem('tourismAuth');
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('userInfo');
    sessionStorage.removeItem('tourismUser');
    
    // Clear any cached user data
    localStorage.removeItem('selectedLanguage');
    sessionStorage.removeItem('selectedLanguage');
    
    // Reset global state
    currentUser = null;
    isAuthenticated = false;
    
    console.log('✅ Authentication data cleared completely');
}

/**
 * Force clear all cached data and redirect to login
 * 全キャッシュ強制クリア・ログイン画面遷移
 */
function forceClearAndRelogin() {
    console.log('🔄 Force clearing all cached data...');
    
    // Clear all possible cache keys
    const keysToRemove = [
        'tourismAuth', 'accessToken', 'userInfo', 'selectedLanguage',
        'tourismUser', 'google_auth_state', 'auth_callback_data'
    ];
    
    keysToRemove.forEach(key => {
        localStorage.removeItem(key);
        sessionStorage.removeItem(key);
    });
    
    // Clear all localStorage items that might be related
    for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key && (key.includes('tourism') || key.includes('auth') || key.includes('user'))) {
            localStorage.removeItem(key);
        }
    }
    
    // Reset global state
    currentUser = null;
    isAuthenticated = false;
    
    showMessage('キャッシュをクリアしました。再ログインしてください。', 'info');
    
    // Redirect to login page
    setTimeout(() => {
        window.location.href = './login.html';
    }, 2000);
}

/**
 * Logout user and redirect to login
 * ログアウト処理
 */
async function logout() {
    console.log('🚪 Logging out user...');
    
    try {
        // Clear authentication data
        await clearAuthenticationData();
        
        // Show logout message
        showMessage('ログアウトしました', 'info');
        
        // Redirect to login page after short delay
        setTimeout(() => {
            window.location.href = './login.html';
        }, 1500);
        
    } catch (error) {
        console.error('🚨 Logout error:', error);
        // Force redirect even if error occurs
        window.location.href = './login.html';
    }
}

/**
 * Show main application after authentication verification
 * 認証確認後のメインアプリ表示
 */
function showMainApplication() {
    console.log('🎨 Showing main application...');
    
    try {
        // Hide authentication loading
        const authLoading = document.getElementById('authLoading');
        if (authLoading) {
            authLoading.style.display = 'none';
        }
        
        // Show main app
        const mainApp = document.getElementById('mainApp');
        if (mainApp) {
            mainApp.style.display = 'block';
            
            // Add active class to main-app for CSS visibility
            const mainAppElement = document.querySelector('.main-app');
            if (mainAppElement) {
                mainAppElement.classList.add('active');
                console.log('🔍 Debug: Added active class to main-app in showMainApplication');
            }
        }
        
        // Update user info in header
        updateUserInfoDisplay();
        
        // Note: initializeMainApplication() is called from index.html, no need to call again here
        console.log('🔍 Debug: Skipping initializeMainApplication (already called from index.html)');
        
        console.log('✅ Main application displayed successfully');
        
    } catch (error) {
        console.error('🚨 Error showing main application:', error);
        window.location.href = './login.html';
    }
}

/**
 * Update user information display in header
 * ヘッダーのユーザー情報表示更新
 */
function updateUserInfoDisplay() {
    try {
        console.log('🔍 Debug: updateUserInfoDisplay called');
        console.log('🔍 Debug: currentUser:', currentUser);
        console.log('🔍 Debug: isAuthenticated:', isAuthenticated);
        
        // Check if user data exists
        if (!currentUser) {
            console.warn('⚠️ No current user data available');
            
            // Try to get user info from localStorage as fallback
            const storedUserInfo = localStorage.getItem('userInfo');
            if (storedUserInfo) {
                try {
                    const fallbackUser = JSON.parse(storedUserInfo);
                    console.log('🔄 Using fallback user info from localStorage:', fallbackUser);
                    currentUser = fallbackUser;
                } catch (e) {
                    console.error('❌ Failed to parse stored user info:', e);
                    return;
                }
            } else {
                console.error('❌ No user info available in localStorage either');
                return;
            }
        }
        
        // Check if DOM elements exist
        const currentUserElement = document.getElementById('currentUser');
        const userPlanElement = document.getElementById('userPlan');
        const userInfoSection = document.getElementById('userInfo');
        
        console.log('🔍 Debug: DOM elements found:', {
            currentUserElement: !!currentUserElement,
            userPlanElement: !!userPlanElement,
            userInfoSection: !!userInfoSection
        });
        
        // Update user name
        if (currentUserElement) {
            const displayName = currentUser.email || currentUser.name || 'ユーザー';
            currentUserElement.textContent = displayName;
            console.log('✅ Updated user name to:', displayName);
        } else {
            console.error('❌ currentUser element not found in DOM');
        }
        
        // Update user plan
        if (userPlanElement) {
            // Check for all premium plan types (premium_7days, premium_20days, premium)
            const isPremium = currentUser.user_type && (
                currentUser.user_type.includes('premium') || 
                currentUser.user_type === 'premium'
            );
            
            let planText = 'Free (残り5回)';
            if (isPremium) {
                if (currentUser.user_type === 'premium_7days') {
                    planText = 'Premium (7日間)';
                } else if (currentUser.user_type === 'premium_20days') {
                    planText = 'Premium (20日間)';
                } else {
                    planText = 'Premium (無制限)';
                }
                userPlanElement.className = 'user-plan premium';
            } else {
                // Calculate remaining usage for free users
                const monthlyCount = parseInt(currentUser.monthly_analysis_count || 0);
                const remaining = Math.max(0, 5 - monthlyCount);
                
                if (remaining > 0) {
                    planText = `Free (残り${remaining}回)`;
                    userPlanElement.className = 'user-plan';
                } else {
                    // Get current language and use appropriate translation
                    const currentLanguage = localStorage.getItem('selectedLanguage') || 'ja';
                    let suspendedText = '機能停止'; // Default Japanese
                    
                    // Use translation if available
                    if (typeof getTranslation === 'function') {
                        suspendedText = getTranslation('serviceSuspended', currentLanguage);
                    } else {
                        // Fallback translations for different languages
                        const suspendedTranslations = {
                            'ja': '機能停止',
                            'ko': '기능 정지', 
                            'zh': '功能停止',
                            'tw': '功能停止',
                            'en': 'Service Suspended'
                        };
                        suspendedText = suspendedTranslations[currentLanguage] || '機能停止';
                    }
                    
                    planText = `Free (${suspendedText})`;
                    userPlanElement.className = 'user-plan limit-reached';
                }
            }
            
            userPlanElement.textContent = planText;
            console.log('✅ Updated user plan to:', planText, '(user_type:', currentUser.user_type, ')');
        } else {
            console.error('❌ userPlan element not found in DOM');
        }
        
        // Update upgrade button visibility
        updateUpgradeButtonVisibility();
        
        // Make sure user info section is visible
        if (userInfoSection) {
            userInfoSection.style.display = 'block';
            console.log('✅ Made user info section visible');
        }
        
        console.log('👤 User info display updated successfully');
        
    } catch (error) {
        console.error('🚨 Error updating user info display:', error);
        console.error('🚨 Error stack:', error.stack);
    }
}

/**
 * Get current authentication token
 * 現在の認証トークン取得
 */
function getAuthToken() {
    return localStorage.getItem('accessToken');
}

/**
 * Get current user information
 * 現在のユーザー情報取得
 */
function getCurrentUser() {
    return currentUser;
}

/**
 * Check if user is authenticated
 * ユーザー認証状態確認
 */
function isUserAuthenticated() {
    return isAuthenticated && currentUser !== null;
}

/**
 * Update upgrade button visibility based on user plan
 * プランに応じてアップグレードボタンの表示を更新
 */
function updateUpgradeButtonVisibility() {
    const upgradeBtn = document.getElementById('upgradeBtn');
    if (!upgradeBtn) {
        console.log('⚠️ Upgrade button not found in DOM');
        return;
    }
    
    if (!currentUser) {
        upgradeBtn.style.display = 'none';
        return;
    }
    
    // Check if user is premium
    const isPremium = currentUser.user_type && (
        currentUser.user_type.includes('premium') || 
        currentUser.user_type === 'premium'
    );
    
    if (isPremium) {
        // Hide upgrade button for premium users
        upgradeBtn.style.display = 'none';
        console.log('🔒 Upgrade button hidden (premium user)');
    } else {
        // Show upgrade button for free users (especially when low on usage)
        const monthlyCount = currentUser.monthly_analysis_count || 0;
        const remaining = Math.max(0, 5 - monthlyCount);
        
        // Show upgrade button when remaining analyses are 2 or less
        if (remaining <= 2) {
            upgradeBtn.style.display = 'inline-block';
            console.log(`⭐ Upgrade button shown (${remaining} analyses remaining)`);
        } else {
            upgradeBtn.style.display = 'none';
            console.log(`🔒 Upgrade button hidden (${remaining} analyses remaining)`);
        }
    }
}