/**
 * Common user functionality for all user pages
 */

// User management functions
async function loadUserData() {
    try {
        console.log('Loading user data...');
        // Check if user is logged in
        if (!api.token) {
            console.log('No token found, redirecting to login');
            window.location.href = '/auth/login';
            return;
        }
        
        // Get current user data
        const response = await api.getCurrentUser();
        const user = response.user;
        console.log('User data loaded:', user);
        
        // Update UI with user data
        const userNameElement = document.getElementById('userName');
        const userAvatarElement = document.getElementById('userAvatar');
        const welcomeMessageElement = document.getElementById('welcomeMessage');
        
        // Use display_name or name, fallback to email
        const displayName = user.display_name || user.name || user.displayName || user.email?.split('@')[0] || 'User';
        
        if (userNameElement) {
            userNameElement.textContent = displayName;
        }
        
        if (welcomeMessageElement) {
            const firstName = displayName.split(' ')[0];
            welcomeMessageElement.textContent = `Welcome back, ${firstName}!`;
        }
        
        // Load user avatar from database - update all avatar elements
        if (user.profile_picture) {
            // Update header avatar
            if (userAvatarElement) {
                userAvatarElement.src = user.profile_picture;
            }
            
            // Update profile settings page avatar
            const profilePhotoElement = document.getElementById('profilePhoto');
            if (profilePhotoElement) {
                profilePhotoElement.src = user.profile_picture;
            }
            
            // Update any other avatar elements
            const allAvatarElements = document.querySelectorAll('[id*="avatar"], [id*="Avatar"], [id*="photo"], [id*="Photo"]');
            allAvatarElements.forEach(element => {
                if (element.tagName === 'IMG') {
                    element.src = user.profile_picture;
                }
            });
        }
        
        // Store user data globally for other functions
        window.currentUser = user;
        
    } catch (error) {
        console.error('Error loading user data:', error);
        // Redirect to login if token is invalid
        api.clearToken();
        window.location.href = '/auth/login';
    }
}

function setupUserDropdown() {
    console.log('Setting up user dropdown...');
    
    // Check if dropdown is already initialized by header script
    if (window.dropdownInitialized) {
        console.log('Dropdown already initialized by header script');
        setupLogoutButton();
        return;
    }
    
    // Fallback initialization if header script didn't run
    const userMenuButton = document.getElementById('userMenuButton');
    const userDropdown = document.getElementById('userDropdown');
    
    console.log('Elements found:', {
        userMenuButton: !!userMenuButton,
        userDropdown: !!userDropdown
    });
    
    if (!userMenuButton || !userDropdown) {
        console.warn('User dropdown elements not found');
        setupLogoutButton();
        return;
    }
    
    // Only setup logout button functionality
    setupLogoutButton();
    
    // Let the header script handle dropdown toggle
    console.log('User dropdown setup delegated to header script');
}

function setupLogoutButton() {
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (logoutBtn) {
        // Remove existing listeners to prevent duplicates
        const newLogoutBtn = logoutBtn.cloneNode(true);
        logoutBtn.parentNode.replaceChild(newLogoutBtn, logoutBtn);
        
        // Add logout functionality
        newLogoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to logout?')) {
                api.clearToken();
                // Don't clear profile picture data - it's now stored in database
                window.location.href = '/auth/login';
            }
        });
        
        console.log('Logout button setup complete');
    }
}

function setActiveNavLink() {
    // Get current page from URL
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Profile photo management
async function updateUserAvatar(imageUrl) {
    // Update all avatar/photo elements
    const avatarSelectors = [
        '#userAvatar',
        '#profilePhoto',
        '[id*="avatar"]',
        '[id*="Avatar"]', 
        '[id*="photo"]',
        '[id*="Photo"]'
    ];
    
    avatarSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            if (element.tagName === 'IMG') {
                element.src = imageUrl;
            }
        });
    });
    
    // Save to database via API
    if (window.currentUser && api.token) {
        try {
            await api.request('/profile/update-picture', {
                method: 'POST',
                body: JSON.stringify({ profile_picture: imageUrl })
            });
            console.log('Profile picture saved to database');
            
            // Update the current user object
            window.currentUser.profile_picture = imageUrl;
            
        } catch (error) {
            console.error('Failed to save profile picture:', error);
            throw error;
        }
    }
}

// Function to handle profile photo upload
async function handleProfilePhotoUpload(file) {
    try {
        // Validate file
        if (!file || !file.type.startsWith('image/')) {
            throw new Error('Please select a valid image file');
        }
        
        // Check file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            throw new Error('Image size must be less than 5MB');
        }
        
        // Create FormData for upload
        const formData = new FormData();
        formData.append('profile_picture', file);
        
        // Show loading state
        showPhotoUploadLoading(true);
        
        // Upload to server
        const response = await api.request('/profile/upload-picture', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content-type for FormData
        });
        
        if (response.profile_picture_url) {
            // Update all avatar elements with new image
            await updateUserAvatar(response.profile_picture_url);
            
            // Show success message
            if (window.notifications) {
                window.notifications.success('Profile photo updated successfully!');
            }
            
            return response.profile_picture_url;
        } else {
            throw new Error('Failed to upload image');
        }
        
    } catch (error) {
        console.error('Profile photo upload error:', error);
        
        // Show error message
        if (window.notifications) {
            window.notifications.error(error.message || 'Failed to upload profile photo');
        }
        
        throw error;
    } finally {
        showPhotoUploadLoading(false);
    }
}

// Show/hide photo upload loading state
function showPhotoUploadLoading(isLoading) {
    const cameraBtn = document.getElementById('cameraBtn');
    const profilePhoto = document.getElementById('profilePhoto');
    
    if (isLoading) {
        if (cameraBtn) {
            cameraBtn.innerHTML = '<i class="fas fa-spinner fa-spin text-sm"></i>';
            cameraBtn.disabled = true;
        }
        if (profilePhoto) {
            profilePhoto.style.opacity = '0.6';
        }
    } else {
        if (cameraBtn) {
            cameraBtn.innerHTML = '<i class="fas fa-camera text-sm"></i>';
            cameraBtn.disabled = false;
        }
        if (profilePhoto) {
            profilePhoto.style.opacity = '1';
        }
    }
}

// Initialize user functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('User-common.js loaded');
    loadUserData();
    setupUserDropdown();
    setActiveNavLink();
});