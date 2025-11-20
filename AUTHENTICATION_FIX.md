# Authentication Fix for Profile Settings

## Issue Fixed
The "Not authenticated" error when clicking "Save Changes" button has been resolved.

## What Was Wrong
The code was checking for `window.api.token` which doesn't exist. The token is stored in `localStorage` and retrieved automatically by the API client.

## Changes Made

### 1. Updated api.js
**File**: `app/static/js/api.js`

Added global window reference:
```javascript
// Create global API client instance
const api = new APIClient();

// Make it available globally
window.api = api;  // ← Added this line
```

### 2. Updated saveProfileData()
**File**: `app/templates/user/user_profile_settings.html`

Changed authentication check:
```javascript
// OLD (incorrect):
if (!window.api || !window.api.token) {
    throw new Error('Not authenticated');
}

// NEW (correct):
if (!window.api) {
    throw new Error('API client not initialized');
}

const token = localStorage.getItem('access_token');
if (!token) {
    throw new Error('Not authenticated. Please login again.');
}
```

### 3. Updated loadUserProfileData()
Same fix applied to the load function.

### 4. Added Debug Logging
Added console logs to help identify issues:
- ✅ API client initialization check
- ✅ Authentication token verification
- ⚠️ Warning messages for missing components

## How to Test

### 1. Clear Browser Cache
```
Press Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
Clear cached files
```

### 2. Restart Flask Application
```bash
# Stop the app (Ctrl+C)
# Start it again
python app.py
```

### 3. Test the Flow

1. **Open browser console** (F12)
2. **Navigate to** `http://localhost:5000`
3. **Login** with your credentials
4. **Go to Profile Settings**
5. **Check console** - you should see:
   ```
   ✅ Authentication token found
   ✅ API client initialized: APIClient {...}
   Profile Settings initialized successfully
   ```

6. **Fill in some fields**
7. **Click "Save Changes"**
8. **Check console** - you should see:
   ```
   Saving profile data...
   Making API request to: http://localhost:5000/api/profile/update
   Response status: 200
   Response data: {success: true, message: "Profile updated successfully", ...}
   ```

9. **Success message** should appear

### 4. Verify Data Persistence

1. **Refresh the page** (F5)
2. All your entered data should still be there
3. Or **logout and login again**
4. Navigate back to Profile Settings
5. Data should be loaded automatically

## Troubleshooting

### Still Getting "Not authenticated"?

**Check 1: Is the token in localStorage?**
```javascript
// In browser console:
localStorage.getItem('access_token')
// Should return a long string (JWT token)
```

**Check 2: Is window.api available?**
```javascript
// In browser console:
window.api
// Should return: APIClient {token: "...", ...}
```

**Check 3: Are scripts loaded in correct order?**
The HTML should have:
```html
<script src="/static/js/api.js"></script>
<script src="/static/js/user-common.js"></script>
<!-- Then your page scripts -->
```

### Token Expired?

If you see "Token is invalid" or "Token expired":
1. Logout
2. Login again
3. Try saving profile again

### API Client Not Found?

If console shows "API client not found":
1. Check if `api.js` file exists in `app/static/js/`
2. Check browser Network tab - is `api.js` loading? (should be 200 status)
3. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

### CORS Errors?

If you see CORS errors:
1. Make sure Flask app is running on `localhost:5000`
2. Check if you're accessing from the same domain
3. Verify `API_BASE_URL` in `api.js` matches your Flask URL

## Testing Checklist

- [ ] Browser console shows no errors on page load
- [ ] Console shows "✅ Authentication token found"
- [ ] Console shows "✅ API client initialized"
- [ ] Can fill in profile fields
- [ ] "Save Changes" button works without errors
- [ ] Success message appears after saving
- [ ] Data persists after page refresh
- [ ] Data persists after logout/login
- [ ] "Reset Changes" button works

## Quick Debug Commands

Open browser console (F12) and run:

```javascript
// Check if API client exists
console.log('API Client:', window.api);

// Check if token exists
console.log('Token:', localStorage.getItem('access_token'));

// Test API call manually
window.api.request('/profile/settings', {method: 'GET'})
  .then(data => console.log('Profile data:', data))
  .catch(err => console.error('Error:', err));
```

## Summary

The authentication issue is now fixed. The key changes were:

1. ✅ Added `window.api = api` to make API client globally available
2. ✅ Changed authentication check to use `localStorage.getItem('access_token')`
3. ✅ Added debug logging to help identify issues
4. ✅ Improved error messages

**The profile settings should now save successfully!**
