// App-specific JavaScript functionality

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check if user is authenticated
    const savedUser = localStorage.getItem('golfUser');
    if (!savedUser) {
        // Redirect to main website if not authenticated
        window.location.href = '/';
        return;
    }
    
    // Initialize app-specific features
    setupAppNavigation();
    loadDashboardData();
    
    // Gmail integration is handled by setupGmailIntegrationListeners in loadDashboardData
    console.log('Gmail integration initialized');
}

function setupAppNavigation() {
    // Handle sidebar navigation clicks
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Handle navigation
            const href = this.getAttribute('href');
            const navText = this.querySelector('.nav-text').textContent;
            
            if (href === '/app') {
                showPage('dashboard');
            } else if (href === '/app/rounds') {
                showPage('rounds');
            } else if (href === '/app/settings') {
                showPage('settings');
                loadSettingsData(); // Load settings page data
            }
            
            showNotification(`Navigating to ${navText}...`);
        });
    });
}

function showPage(pageName) {
    // Hide all page contents
    const allPages = document.querySelectorAll('.page-content');
    allPages.forEach(page => {
        page.style.display = 'none';
    });
    
    // Show the selected page
    const targetPage = document.getElementById(`${pageName}-content`);
    if (targetPage) {
        targetPage.style.display = 'block';
    }
}

function loadDashboardData() {
    // Simulate loading user data
    const user = JSON.parse(localStorage.getItem('golfUser'));

    // Update user profile in navbar
    if (user) {
        document.getElementById('userAvatar').src = user.picture;
        document.getElementById('userName').textContent = user.name;
        document.getElementById('userProfile').style.display = 'flex';

        // Check Gmail access status
        checkGmailAccessStatus(user.id);
    }

    // Setup Gmail integration event listeners
    setupGmailIntegrationListeners();

    // Setup signout button
    setupSignoutButton();

    // Backup: Try again after a delay in case of timing issues
    setTimeout(setupSignoutButton, 100);

    // Simulate loading dashboard data
    setTimeout(() => {
        showNotification('Dashboard data loaded successfully!');
    }, 1000);
}

function setupGmailIntegrationListeners() {
    // Grant Gmail access button
    const grantAccessBtn = document.getElementById('grant-gmail-access-btn');
    if (grantAccessBtn) {
        grantAccessBtn.addEventListener('click', handleGrantGmailAccess);
    }

    // Sync golf rounds button (legacy - still in settings page)
    const syncRoundsBtn = document.getElementById('sync-golf-rounds-btn');
    if (syncRoundsBtn) {
        syncRoundsBtn.addEventListener('click', handleSyncGolfRounds);
    }

    // Navbar sync golf rounds button
    const navSyncBtn = document.getElementById('sync-golf-rounds-nav-btn');
    if (navSyncBtn) {
        navSyncBtn.addEventListener('click', handleSyncGolfRounds);
    }

    // Revoke Gmail access button
    const revokeAccessBtn = document.getElementById('revoke-gmail-access-btn');
    if (revokeAccessBtn) {
        revokeAccessBtn.addEventListener('click', handleRevokeGmailAccess);
    }
}

async function checkGmailAccessStatus(userId) {
    try {
        const response = await fetch('/api/get-user-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId })
        });

        const data = await response.json();

        if (data.success && data.user) {
            updateGmailAccessUI(data.user.gmail_access_granted);
        } else {
            updateGmailAccessUI(false);
        }
    } catch (error) {
        console.error('Error checking Gmail access status:', error);
        updateGmailAccessUI(false);
    }
}

function updateGmailAccessUI(hasAccess) {
    const grantedSection = document.getElementById('gmail-access-granted');
    const neededSection = document.getElementById('gmail-access-needed');
    const navSyncBtn = document.getElementById('sync-golf-rounds-nav-btn');

    if (hasAccess) {
        if (grantedSection) grantedSection.style.display = 'block';
        if (neededSection) neededSection.style.display = 'none';
        if (navSyncBtn) navSyncBtn.style.display = 'flex'; // Show navbar sync button
    } else {
        if (grantedSection) grantedSection.style.display = 'none';
        if (neededSection) neededSection.style.display = 'block';
        if (navSyncBtn) navSyncBtn.style.display = 'none'; // Hide navbar sync button
    }
}

async function handleGrantGmailAccess() {
    const user = JSON.parse(localStorage.getItem('golfUser'));
    if (!user) {
        showNotification('Please sign in first', 'error');
        return;
    }

    try {
        const grantBtn = document.getElementById('grant-gmail-access-btn');
        grantBtn.disabled = true;
        grantBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Connecting to Gmail...</span>';

        const response = await fetch('/api/grant-gmail-access', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: user.id })
        });

        const data = await response.json();

        if (data.success && data.authorization_url) {
            // Open OAuth flow in popup window
            const popup = window.open(
                data.authorization_url,
                'gmail-oauth',
                'width=500,height=600,scrollbars=yes,resizable=yes'
            );

            // Monitor popup for completion with better cross-origin handling
            const checkClosed = setInterval(() => {
                try {
                    if (popup.closed) {
                        clearInterval(checkClosed);
                        // Check if access was granted
                        setTimeout(() => {
                            checkGmailAccessStatus(user.id);
                        }, 1000);

                        // Reset button
                        grantBtn.disabled = false;
                        grantBtn.innerHTML = '<span class="btn-icon">🔓</span><span class="btn-text">Allow Gmail Access</span>';
                    }
                } catch (e) {
                    // Handle cross-origin policy errors
                    console.log('Cross-origin policy prevented popup monitoring, checking auth status...');
                    clearInterval(checkClosed);
                    // Check if access was granted after a delay
                    setTimeout(() => {
                        checkGmailAccessStatus(user.id);
                        // Reset button
                        grantBtn.disabled = false;
                        grantBtn.innerHTML = '<span class="btn-icon">🔓</span><span class="btn-text">Allow Gmail Access</span>';
                    }, 3000);
                }
            }, 1000);

            showNotification('Complete the Gmail authorization in the popup window');

        } else {
            throw new Error(data.error || 'Failed to initiate Gmail authorization');
        }
    } catch (error) {
        console.error('Error granting Gmail access:', error);
        showNotification('Failed to grant Gmail access: ' + error.message, 'error');

        // Reset button
        const grantBtn = document.getElementById('grant-gmail-access-btn');
        grantBtn.disabled = false;
        grantBtn.innerHTML = '<span class="btn-icon">🔓</span><span class="btn-text">Allow Gmail Access</span>';
    }
}

async function handleSyncGolfRounds() {
    const user = JSON.parse(localStorage.getItem('golfUser'));
    if (!user) {
        showNotification('Please sign in first', 'error');
        return;
    }

    try {
        // Handle both settings page sync button and navbar sync button
        const syncBtn = document.getElementById('sync-golf-rounds-btn');
        const navSyncBtn = document.getElementById('sync-golf-rounds-nav-btn');
        const syncStatus = document.getElementById('sync-status');

        // Disable both buttons
        if (syncBtn) {
            syncBtn.disabled = true;
            syncBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Syncing...</span>';
        }
        if (navSyncBtn) {
            navSyncBtn.disabled = true;
            navSyncBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Syncing...</span>';
        }

        // Update status (only visible on settings page)
        if (syncStatus) {
            syncStatus.textContent = 'Searching for golf rounds in your emails...';
            syncStatus.className = 'sync-status loading';
            syncStatus.style.display = 'block';
        }

        const response = await fetch('/api/sync-golf-rounds', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: user.id })
        });

        const data = await response.json();

        if (data.success) {
            syncStatus.textContent = `✅ Successfully synced ${data.rounds_found} golf rounds!`;
            syncStatus.className = 'sync-status success';
            showNotification(`Found and synced ${data.rounds_found} golf rounds!`);

            // Refresh the dashboard data
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            throw new Error(data.error || 'Failed to sync golf rounds');
        }
    } catch (error) {
        console.error('Error syncing golf rounds:', error);
        const syncStatus = document.getElementById('sync-status');
        syncStatus.textContent = '❌ Failed to sync golf rounds: ' + error.message;
        syncStatus.className = 'sync-status error';
        syncStatus.style.display = 'block';

        showNotification('Failed to sync golf rounds: ' + error.message, 'error');
    } finally {
        // Reset both buttons after delay
        setTimeout(() => {
            const syncBtn = document.getElementById('sync-golf-rounds-btn');
            const navSyncBtn = document.getElementById('sync-golf-rounds-nav-btn');

            if (syncBtn) {
                syncBtn.disabled = false;
                syncBtn.innerHTML = '<span class="btn-icon">🔄</span><span class="btn-text">Sync Golf Rounds</span>';
            }
            if (navSyncBtn) {
                navSyncBtn.disabled = false;
                navSyncBtn.innerHTML = '<span class="btn-icon">🔄</span><span class="btn-text">Sync Rounds</span>';
            }
        }, 3000);
    }
}

// Mobile sidebar toggle (for responsive design)
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

function loadSettingsData() {
    // Load user account information
    const user = JSON.parse(localStorage.getItem('golfUser'));
    if (user) {
        const accountName = document.getElementById('account-name');
        const accountEmail = document.getElementById('account-email');

        if (accountName) accountName.textContent = user.name || 'Not available';
        if (accountEmail) accountEmail.textContent = user.email || 'Not available';

        // Check Gmail access status for settings page
        checkGmailAccessStatus(user.id);
    }
}

async function handleRevokeGmailAccess() {
    const user = JSON.parse(localStorage.getItem('golfUser'));
    if (!user) {
        showNotification('Please sign in first', 'error');
        return;
    }

    try {
        const revokeBtn = document.getElementById('revoke-gmail-access-btn');
        if (revokeBtn) {
            revokeBtn.disabled = true;
            revokeBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Revoking...</span>';
        }

        // Call server endpoint to revoke Gmail access
        const response = await fetch('/api/revoke-gmail-access', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: user.id })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Gmail access revoked successfully');

            // Update the UI to show access is revoked
            updateGmailAccessUI(false);
        } else {
            throw new Error(data.error || 'Failed to revoke Gmail access');
        }

        // Reset button
        if (revokeBtn) {
            revokeBtn.disabled = false;
            revokeBtn.innerHTML = '<span class="btn-icon">🔒</span><span class="btn-text">Revoke Access</span>';
        }

    } catch (error) {
        console.error('Error revoking Gmail access:', error);
        showNotification('Failed to revoke Gmail access: ' + error.message, 'error');

        // Reset button
        const revokeBtn = document.getElementById('revoke-gmail-access-btn');
        if (revokeBtn) {
            revokeBtn.disabled = false;
            revokeBtn.innerHTML = '<span class="btn-icon">🔒</span><span class="btn-text">Revoke Access</span>';
        }
    }
}

// Add mobile menu button for responsive design
function addMobileMenuButton() {
    const navbar = document.querySelector('.app-navbar .nav-container');
    const mobileMenuBtn = document.createElement('button');
    mobileMenuBtn.className = 'mobile-menu-btn';
    mobileMenuBtn.innerHTML = '☰';
    mobileMenuBtn.style.cssText = `
        display: none;
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #2d5016;
    `;
    
    mobileMenuBtn.addEventListener('click', toggleSidebar);
    
    // Insert before nav-links
    navbar.insertBefore(mobileMenuBtn, navbar.querySelector('.nav-links'));
    
    // Show on mobile
    if (window.innerWidth <= 768) {
        mobileMenuBtn.style.display = 'block';
    }
}

// Initialize mobile menu button
document.addEventListener('DOMContentLoaded', addMobileMenuButton);

// Handle window resize for mobile menu
window.addEventListener('resize', function() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    if (mobileMenuBtn) {
        if (window.innerWidth <= 768) {
            mobileMenuBtn.style.display = 'block';
        } else {
            mobileMenuBtn.style.display = 'none';
            // Close sidebar on desktop
            document.querySelector('.sidebar').classList.remove('open');
        }
    }
});

function setupSignoutButton() {
    console.log('Setting up signout button...');
    const signOutBtn = document.getElementById('signOutBtn');
    console.log('Signout button found:', signOutBtn);

    if (signOutBtn) {
        console.log('Adding click event listener to signout button');
        signOutBtn.addEventListener('click', handleSignOut);

        // Also try direct onclick as backup
        signOutBtn.onclick = handleSignOut;
    } else {
        console.error('Signout button not found!');
    }
}

async function handleSignOut() {
    console.log('handleSignOut called!');
    try {
        console.log('Starting sign out process...');

        // Clear local storage (same as marketing page)
        localStorage.removeItem('golfUser');
        console.log('Local storage cleared');

        // Sign out from Google if available (same as marketing page behavior)
        if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
            google.accounts.id.disableAutoSelect();
            console.log('Google auto-select disabled');
        }

        // Show notification (same as marketing page)
        showNotification('You have been signed out');
        console.log('Notification shown');

        // Redirect to main page (since we're in the app, go back to marketing page)
        console.log('Redirecting to main page...');
        window.location.href = '/';

    } catch (error) {
        console.error('Error during signout:', error);
        showNotification('Error signing out: ' + error.message, 'error');
    }
}
