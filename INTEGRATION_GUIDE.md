# Frontend-Backend Integration Guide

## Overview

This guide explains how to connect the ProSpeak AI frontend to the Flask backend.

## Setup

### 1. Include API Client

Add the API client script to your HTML pages:

```html
<script src="../js/api.js"></script>
```

### 2. Configure API Base URL

The API client is pre-configured to use `http://localhost:5000/api`. To change this, edit `js/api.js`:

```javascript
const API_BASE_URL = 'https://your-api-domain.com/api';
```

## Usage Examples

### Authentication

#### Login
```javascript
// In login_registration.html
document.querySelector('#loginForm form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('lo