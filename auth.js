// Authentication state management
let currentUser = null;

// DOM elements
const authModal = document.getElementById('authModal');
const authButtons = document.getElementById('authButtons');
const userProfile = document.getElementById('userProfile');
const signInBtn = document.getElementById('signInBtn');
const signUpBtn = document.getElementById('signUpBtn');
const signOutBtn = document.getElementById('signOutBtn');
const closeModal = document.querySelector('.close');

// Initialize authentication
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    setupEventListeners();
});

function initializeAuth() {
    // Check if user is already signed in (from localStorage)
    const savedUser = localStorage.getItem('golfUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateUI();
    }
}

function setupEventListeners() {
    // Modal controls
    signInBtn.addEventListener('click', () => openAuthModal());
    signUpBtn.addEventListener('click', () => openAuthModal());
    closeModal.addEventListener('click', closeAuthModal);
    signOutBtn.addEventListener('click', signOut);
    
    // Logo click to scroll to top
    const logoLink = document.querySelector('.logo-link');
    if (logoLink) {
        logoLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === authModal) {
            closeAuthModal();
        }
    });
}

function openAuthModal() {
    authModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeAuthModal() {
    authModal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Google Sign-In callback
function handleCredentialResponse(response) {
    // Decode the JWT token (in a real app, you'd verify this on the server)
    const responsePayload = decodeJwtResponse(response.credential);
    
    currentUser = {
        id: responsePayload.sub,
        name: responsePayload.name,
        email: responsePayload.email,
        picture: responsePayload.picture,
        provider: 'google'
    };
    
    // Save to localStorage
    localStorage.setItem('golfUser', JSON.stringify(currentUser));
    
    // Save user to database
    saveUserToDatabase(currentUser);
    
    // Update UI
    updateUI();
    closeAuthModal();
    
    // Show welcome message
    showNotification(`Welcome back, ${currentUser.name}!`);
}

// Save user data to database
async function saveUserToDatabase(userData) {
    try {
        const response = await fetch('/api/save-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        if (response.ok) {
            console.log('User data saved to database');
        } else {
            console.error('Failed to save user data to database');
        }
    } catch (error) {
        console.error('Error saving user data:', error);
    }
}

// Decode JWT token (simplified version - in production, verify on server)
function decodeJwtResponse(token) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    
    return JSON.parse(jsonPayload);
}

// Sign out function
function signOut() {
    currentUser = null;
    localStorage.removeItem('golfUser');
    updateUI();
    showNotification('You have been signed out');
}

// Update UI based on authentication state
function updateUI() {
    if (currentUser) {
        // Show user profile
        authButtons.style.display = 'none';
        userProfile.style.display = 'flex';
        
        // Update user info
        document.getElementById('userAvatar').src = currentUser.picture;
        document.getElementById('userName').textContent = currentUser.name;
        
        // Update hero buttons to show dashboard
        const heroButtons = document.querySelector('.hero-buttons');
        heroButtons.innerHTML = `
            <a href="/app" class="btn-primary">View Dashboard</a>
            <a href="/app" class="btn-secondary">Track Round</a>
        `;
    } else {
        // Show auth buttons
        authButtons.style.display = 'flex';
        userProfile.style.display = 'none';
        
        // Reset hero buttons
        const heroButtons = document.querySelector('.hero-buttons');
        heroButtons.innerHTML = `
            <button class="btn-primary">Start Free Trial</button>
            <button class="btn-secondary">Watch Demo</button>
        `;
    }
}

// Dashboard functions (placeholder)
function showDashboard() {
    showNotification('Dashboard coming soon! This would show your handicap and recent rounds.');
}

// Notification system
function showNotification(message, type = 'success') {
    // Remove existing notifications
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    if (type === 'success') {
        notification.style.backgroundColor = '#2d5016';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#dc3545';
    }
    
    document.body.appendChild(notification);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 4000);
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
