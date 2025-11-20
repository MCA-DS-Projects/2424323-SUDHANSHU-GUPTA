# Issues to Fix

## 1. Audio Practice End Session Button
- Problem: Not working on first click
- Cause: Event listener added 3 times (lines 964, 967)
- Fix: Remove duplicate event listeners

## 2. Interview Simulator End Session Button  
- Need to check if it exists and works properly

## 3. Dashboard Overall Score
- Need to verify it's calculating and displaying correctly

## Files to Check:
- app/templates/user/audio_practice_mode.html
- app/templates/user/interview_simulator.html
- app/templates/user/user_dashboard.html
- app/routes/api.py (dashboard endpoint)
