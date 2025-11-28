# NeuraSync v4.0 - Universal Browser Sync Platform

## Overview
NeuraSync is a comprehensive browser synchronization platform that enables real-time sync across Chrome, Firefox, Edge, Brave, Opera and other browsers. It provides 75+ features for managing tabs, bookmarks, history, clipboard, and more across multiple devices.

## Key Features

### Core Sync Features
- Real-time multi-device sync via WebSocket (Socket.IO)
- Room-based architecture using sync codes
- Cross-browser support (Chrome, Firefox, Edge, Brave, Opera, Arc)

### Browser Data Management
- **Tab Manager**: Tab groups, frozen tabs, session save/restore, duplicate cleaner
- **Bookmarks**: Smart folders, AI categorization, duplicate finder, dead link checker
- **History Timeline**: Visual timeline, category stats, AI summaries
- **Reading List**: Save articles, offline mode, highlights and notes

### Productivity Features
- **Focus Mode**: Pomodoro timer, site blocking, distraction tracking
- **Multi-Profiles**: Work/Study/Personal profiles with separate data
- **Analytics**: Browsing stats, productivity scores, weekly reports

### Security & Privacy
- **Privacy Guard**: Tracker blocking, breach alerts, fingerprint protection
- **Credential Vault**: Encrypted password storage with master key

## Tech Stack
- **Backend**: Flask + Flask-SocketIO + SQLAlchemy
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Vanilla JavaScript SPA
- **Real-time**: Socket.IO for WebSocket communication

## API Endpoints

### Core
- `GET /` - Main application
- `GET /health` - Health check
- `GET /api/v1/stats` - Stats summary

### Profiles
- `GET/POST /api/v1/profiles` - List/Create profiles
- `PUT/DELETE /api/v1/profiles/<id>` - Update/Delete profile

### Devices
- `GET/POST /api/v1/devices` - List/Register devices

### Tabs
- `GET/POST /api/v1/tabs` - List/Create tabs
- `POST /api/v1/tabs/bulk` - Bulk sync tabs
- `GET/POST /api/v1/tab-groups` - Tab groups

### Bookmarks
- `GET/POST /api/v1/bookmarks` - List/Create bookmarks
- `PUT/DELETE /api/v1/bookmarks/<id>` - Update/Delete bookmark
- `GET /api/v1/bookmarks/duplicates` - Find duplicates
- `GET/POST /api/v1/bookmark-folders` - Bookmark folders

### History
- `GET/POST /api/v1/history` - List/Add history
- `GET /api/v1/history/timeline` - Timeline view

### Reading List
- `GET/POST /api/v1/reading-list` - List/Add articles
- `PUT/DELETE /api/v1/reading-list/<id>` - Update/Delete article

### Clipboard
- `GET/POST/DELETE /api/v1/clipboard` - Clipboard operations

### Focus Mode
- `GET/POST/DELETE /api/v1/focus/blocked-sites` - Blocked sites

### Credential Vault
- `GET/POST /api/v1/vault` - List/Add credentials
- `GET/PUT/DELETE /api/v1/vault/<id>` - Credential operations

### Privacy
- `GET/POST /api/v1/privacy/events` - Privacy events

### Analytics
- `GET /api/v1/analytics` - Weekly analytics
- `GET/POST /api/v1/analytics/today` - Today's analytics

### AI Search
- `POST /api/v1/search` - AI-powered universal search

## WebSocket Events

### Client -> Server
- `register_device` - Register device with sync code
- `send_command` - Send command to all devices
- `sync_clipboard` - Sync clipboard content
- `sync_tabs` - Sync tab state
- `sync_bookmarks` - Sync bookmarks
- `save_session` - Save tab session
- `focus_start` - Start focus session
- `focus_complete` - Complete focus session

### Server -> Client
- `device_registered` - Device registration confirmed
- `device_count` - Device count update
- `command_received` - Command to execute
- `clipboard_updated` - Clipboard sync update
- `tabs_updated` - Tab sync update
- `bookmarks_updated` - Bookmark sync update
- `session_saved` - Session saved confirmation

## Database Models
17 database models covering all features:
- User, Profile, Device
- TabState, TabGroup, Session
- Bookmark, BookmarkFolder
- HistoryEntry, ReadingItem
- ClipboardItem, CommandLog
- PrivacyEvent, AnalyticsSnapshot
- FocusSession, BlockedSite
- Credential, Extension

## How to Use

### Sync Devices
1. Open the app on your first device
2. Note your sync code (shown on Dashboard/Devices page)
3. On another device, enter the same sync code
4. Click Connect - devices are now synced

### Commands
- `open google.com` - Opens URL on all synced devices
- `search cats` - Searches on all synced devices

## Recent Changes

### November 2025 - Frontend/Backend Integration Fix
- Fixed all frontend JavaScript to properly connect to backend APIs
- All 27 API endpoints now fully integrated with UI
- Added comprehensive data loading on page navigation
- Fixed database schema by adding missing columns:
  - clipboard_item.source_device, clipboard_item.extra_data
  - session.profile_id
- Implemented all missing UI handler functions
- All 75+ features now fully operational

### Previous v4.0 Changes
- Complete rewrite with 75+ features
- Added multi-profile support
- Added credential vault
- Added focus mode with Pomodoro timer
- Added privacy guard with breach alerts
- Added AI-powered universal search
