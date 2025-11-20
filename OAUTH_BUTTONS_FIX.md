# OAuth Buttons Fix Guide

## Issue Summary
The Google and Microsoft OAuth buttons were not showing logos and not responding to clicks.

## ✅ What Was Fixed

### 1. **Replaced Font Awesome Icons with SVG Logos**

#### Before (Not Working):
```html
<button>
    <i class="fab fa-google text-red-500 mr-2"></i>
    Google
</button>
```

#### After (Working):
```html
<button type="button" id="googleLoginBtn">
    <svg class="w-5 h-5 mr-2" viewBox="0 0 24 24">
        <path fill="#4285F4" d="..."/>
        <path fill="#34A853" d="..."/>
        <path fill="#FBBC05" d="..."/>
        <path fill="#EA4335" d="..."/>
    </svg>
    Google
</button>
```

### 2. **Added Unique Button IDs**

Each button now has a unique ID:
- Login: `googleLoginBtn`, `microsoftLoginBtn`
- Register: `googleRegisterBtn`, `microsoftRegisterBtn`

### 3. **Added Event Listeners**

```javascript
// OAuth Login Functions
function handleGoogleLogin() {
    showMessage('Google Sign-In is being set up. Please use email/password for now.', 'info');
    // TODO: Implement Google OAuth
    // window.location.href = '/api/auth/google';
}

function handleMicrosoftLogin() {
    showMessage('Microsoft Sign-In is being set up. Please use email/password for now.', 'info');
    // TODO: Implement Microsoft OAuth
    // window.location.href = '/api/auth/microsoft';
}

// Attach OAuth button handlers
const googleLoginBtn = document.getElementById('googleLoginBtn');
const microsoftLoginBtn = document.getElementById('microsoftLoginBtn');
const googleRegisterBtn = document.getElementById('googleRegisterBtn');
const microsoftRegisterBtn = document.getElementById('microsoftRegisterBtn');

if (googleLoginBtn) {
    googleLoginBtn.addEventListener('click', handleGoogleLogin);
    console.log('Google login button attached');
}

if (microsoftLoginBtn) {
    microsoftLoginBtn.addEventListener('click', handleMicrosoftLogin);
    console.log('Microsoft login button attached');
}

if (googleRegisterBtn) {
    googleRegisterBtn.addEventListener('click', handleGoogleLogin);
    console.log('Google register button attached');
}

if (microsoftRegisterBtn) {
    microsoftRegisterBtn.addEventListener('click', handleMicrosoftLogin);
    console.log('Microsoft register button attached');
}
```

### 4. **Added `type="button"` Attribute**

This prevents the buttons from submitting the form:
```html
<button type="button" id="googleLoginBtn">
```

## 🎨 Logo Details

### Google Logo (4-Color Design):
- **Blue** (#4285F4): Top section
- **Green** (#34A853): Right section
- **Yellow** (#FBBC05): Bottom-left section
- **Red** (#EA4335): Left section

### Microsoft Logo (4-Square Design):
- **Red** (#f35325): Top-left square
- **Green** (#81bc06): Top-right square
- **Blue** (#05a6f0): Bottom-left square
- **Yellow** (#ffba08): Bottom-right square

## 🧪 Testing

### Test the Buttons:

1. **Open the login page** in your browser
2. **Open browser console** (F12)
3. **Click Google button** - You should see:
   - Console log: "Google login button attached"
   - Notification: "Google Sign-In is being set up..."
4. **Click Microsoft button** - You should see:
   - Console log: "Microsoft login button attached"
   - Notification: "Microsoft Sign-In is being set up..."

### Test File:
Open `test_oauth_buttons.html` in your browser to see the buttons in isolation.

## 🔍 Troubleshooting

### Problem: Logos Still Not Showing

**Check 1**: Verify SVG code is present
```bash
# Search for SVG in the file
grep -n "viewBox" app/templates/auth/login_register.html
```

**Check 2**: Inspect element in browser
- Right-click on button
- Select "Inspect"
- Look for `<svg>` tag inside button
- Check if paths have `fill` attributes

**Check 3**: Clear browser cache
- Press Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
- Clear cached images and files
- Reload page

### Problem: Buttons Not Responding

**Check 1**: Verify button IDs
```javascript
// In browser console
console.log(document.getElementById('googleLoginBtn'));
// Should show: <button type="button" id="googleLoginBtn">...</button>
```

**Check 2**: Check event listeners
```javascript
// In browser console
getEventListeners(document.getElementById('googleLoginBtn'));
// Should show click event listener
```

**Check 3**: Check for JavaScript errors
- Open browser console (F12)
- Look for red error messages
- Fix any errors before the event listener attachment

### Problem: Buttons Submit Form

**Solution**: Ensure `type="button"` is present
```html
<!-- Correct -->
<button type="button" id="googleLoginBtn">

<!-- Wrong (will submit form) -->
<button id="googleLoginBtn">
```

## 📋 Checklist

Before testing, verify:
- [ ] SVG logos are in the HTML (not Font Awesome icons)
- [ ] Each button has unique ID
- [ ] Buttons have `type="button"` attribute
- [ ] Event handlers are defined (handleGoogleLogin, handleMicrosoftLogin)
- [ ] Event listeners are attached in DOMContentLoaded
- [ ] Console logs appear when page loads
- [ ] No JavaScript errors in console

## 🚀 Next Steps: Full OAuth Implementation

### Backend Setup Required:

1. **Register OAuth Apps**:
   - Google: https://console.cloud.google.com/
   - Microsoft: https://portal.azure.com/

2. **Get Credentials**:
   - Client ID
   - Client Secret
   - Redirect URI

3. **Create Backend Endpoints**:
```python
# app/routes/auth.py

@auth_bp.route('/auth/google')
def google_login():
    # Redirect to Google OAuth
    pass

@auth_bp.route('/auth/google/callback')
def google_callback():
    # Handle Google OAuth callback
    pass

@auth_bp.route('/auth/microsoft')
def microsoft_login():
    # Redirect to Microsoft OAuth
    pass

@auth_bp.route('/auth/microsoft/callback')
def microsoft_callback():
    # Handle Microsoft OAuth callback
    pass
```

4. **Update Frontend**:
```javascript
function handleGoogleLogin() {
    window.location.href = '/api/auth/google';
}

function handleMicrosoftLogin() {
    window.location.href = '/api/auth/microsoft';
}
```

5. **Install OAuth Libraries**:
```bash
pip install authlib
pip install requests
```

6. **Add to .env**:
```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
```

## 📸 Expected Result

When working correctly, you should see:

**Login Form:**
```
┌─────────────────────────────────┐
│  Or continue with               │
├─────────────────┬───────────────┤
│ [G] Google      │ [⊞] Microsoft │
└─────────────────┴───────────────┘
```

**Register Form:**
```
┌─────────────────────────────────┐
│  Or sign up with                │
├─────────────────┬───────────────┤
│ [G] Google      │ [⊞] Microsoft │
└─────────────────┴───────────────┘
```

Where [G] is the colorful Google logo and [⊞] is the Microsoft 4-square logo.

## ✅ Verification

Run these commands to verify the fix:

```bash
# Check if SVG logos are present
grep -c "viewBox" app/templates/auth/login_register.html
# Should return: 4 (2 Google + 2 Microsoft)

# Check if button IDs are present
grep -c "googleLoginBtn\|microsoftLoginBtn\|googleRegisterBtn\|microsoftRegisterBtn" app/templates/auth/login_register.html
# Should return: 8+ (buttons + event listeners)

# Check if event handlers are defined
grep -c "handleGoogleLogin\|handleMicrosoftLogin" app/templates/auth/login_register.html
# Should return: 6+ (definitions + calls)
```

## 🎉 Success Indicators

You'll know it's working when:
1. ✅ You see colorful Google logo (4 colors)
2. ✅ You see Microsoft logo (4 colored squares)
3. ✅ Clicking shows notification message
4. ✅ Console shows "button attached" messages
5. ✅ No JavaScript errors in console
6. ✅ Buttons don't submit the form

---

**Status**: ✅ Fixed and Ready for OAuth Backend Integration
