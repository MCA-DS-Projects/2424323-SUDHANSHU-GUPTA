# Requirements Document

## Introduction

This feature adds a visual icon to the Daily Goal section in the user dashboard and fixes the streak calculation logic to properly track consecutive days of practice. The streak should increment when a user completes sessions on consecutive calendar days (12:00 AM to 11:59 PM) and reset to zero if a day is missed.

## Glossary

- **Daily Goal**: The target number of practice sessions a user aims to complete each day
- **Streak**: The number of consecutive calendar days a user has completed at least one practice session
- **Calendar Day**: A 24-hour period from 12:00 AM (00:00) to 11:59 PM (23:59)
- **Session**: A completed practice activity (interview, fluency coach, audio practice, etc.)
- **Dashboard**: The main user interface showing progress statistics and goals

## Requirements

### Requirement 1

**User Story:** As a user, I want to see a visual icon next to my Daily Goal, so that I can quickly identify this metric on my dashboard

#### Acceptance Criteria

1. THE Dashboard SHALL display an icon next to the "Daily Goal" text in the progress overview section
2. THE Dashboard SHALL use a target or bullseye icon (fas fa-target) to represent the daily goal
3. THE Dashboard SHALL maintain consistent icon styling with other dashboard metrics (Current Streak, Total Sessions)
4. THE Dashboard SHALL display the icon within a colored circular background matching the primary theme color

### Requirement 2

**User Story:** As a user, I want my streak to count consecutive calendar days, so that I can accurately track my daily practice habit

#### Acceptance Criteria

1. WHEN THE user completes a session on a calendar day, THE System SHALL count that day toward the streak
2. WHEN THE user completes multiple sessions on the same calendar day, THE System SHALL count it as one day in the streak
3. WHEN THE user completes sessions on consecutive calendar days, THE System SHALL increment the streak by one for each consecutive day
4. THE System SHALL define a calendar day as the period from 12:00 AM (00:00) to 11:59 PM (23:59) in the user's timezone

### Requirement 3

**User Story:** As a user, I want my streak to reset if I miss a day, so that the streak accurately reflects my consistency

#### Acceptance Criteria

1. WHEN THE user does not complete any sessions on a calendar day, THE System SHALL break the streak
2. WHEN THE streak is broken, THE System SHALL reset the streak count to zero
3. WHEN THE user completes a session after a broken streak, THE System SHALL start a new streak from one
4. THE System SHALL check for streak breaks when calculating the current streak value

### Requirement 4

**User Story:** As a user, I want my streak to persist correctly across midnight, so that sessions completed after midnight count toward the new day

#### Acceptance Criteria

1. WHEN THE user completes a session after 12:00 AM, THE System SHALL count it toward the new calendar day
2. WHEN THE user completes a session before 11:59 PM, THE System SHALL count it toward the current calendar day
3. THE System SHALL use UTC time for consistent streak calculation across timezones
4. THE System SHALL properly handle the transition between calendar days at midnight

### Requirement 5

**User Story:** As a developer, I want the streak calculation to be efficient and accurate, so that dashboard performance remains fast

#### Acceptance Criteria

1. THE System SHALL calculate streaks by checking consecutive calendar days backward from today
2. THE System SHALL stop checking when it finds the first day without a session
3. THE System SHALL handle edge cases such as no sessions, single session, and long streaks
4. THE System SHALL complete streak calculation in under 100 milliseconds for users with up to 1000 sessions
