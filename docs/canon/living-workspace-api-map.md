# SHUNYA Living Workspace — Free API Integration Map

The homepage is alive. The workspace should feel the same way.
Every API below is free-tier or open-source — zero licensing cost.

## Auth & Identity (replacing our custom auth)

| API | What It Does | Free Tier | Integration |
|-----|-------------|-----------|-------------|
| **[Supabase Auth](https://supabase.com/auth)** | Email/password, OAuth (Google, GitHub, Apple), magic links, phone auth, session management | 50,000 MAU, unlimited projects | Replace auth_routes.py + AuthOverlay → Supabase JS client |
| **[Supabase Realtime](https://supabase.com/realtime)** | Live WebSocket sync — broadcast, presence, PostgreSQL changes | 2 million messages/month | Live activity feed, nudge push, multi-device sync |

## Workspace "Living" Layer

| API | What It Does | Free Tier | Integration |
|-----|-------------|-----------|-------------|
| **[Liveblocks](https://liveblocks.io)** | Real-time cursors, presence, document sync | 1M blocks/month | Collaborative workspace editing |
| **[Novu](https://novu.co)** | Notification infrastructure — email, SMS, in-app, push | 30,000 events/month | Replace polling notification bell with real-time push |
| **[Socket.io](https://socket.io)** | Bidirectional real-time communication | Free (self-host) | Live activity stream, nudge delivery |

## Content & Documents

| API | What It Does | Free Tier | Integration |
|-----|-------------|-----------|-------------|
| **[BlockNote](https://www.blocknotejs.org)** | Notion-like block editor (React, OSS, MIT) | Free | Document workspace editor |
| **[Tiptap](https://tiptap.dev)** | ProseMirror-based rich text editor | Free (MIT) | Proposals, notes, document drafting |
| **[PDF.js](https://mozilla.github.io/pdf.js)** | In-browser PDF rendering | Free (Mozilla, Apache 2) | PDF preview in file workspace |
| **[Marked](https://marked.js.org)** | Fast markdown rendering | Free (MIT) | AI output rendering, chat messages |

## Media & Files

| API | What It Does | Free Tier | Integration |
|-----|-------------|-----------|-------------|
| **[Supabase Storage](https://supabase.com/storage)** | File uploads, images, documents | 1GB storage, 10GB bandwidth | Replace custom file upload |
| **[Tesseract.js](https://tesseract.projectnaptha.com)** | OCR in-browser (100+ languages) | Free (Apache 2) | Receipt scanning, document OCR |
| **[YouTube IFrame API](https://developers.google.com/youtube/iframe_api_reference)** | Video/music playback | Free (no API key) | Already built in YouTubePlayer |
| **[Leaflet](https://leafletjs.com)** | Lightweight interactive maps | Free (BSD 2-Clause) | Location preview, travel workspace |

## Data & Intelligence

| API | What It Does | Free Tier | Integration |
|-----|-------------|-----------|-------------|
| **[OpenRouter](https://openrouter.ai)** | Multi-model AI gateway (GPT, Claude, Gemini, etc.) | Pay-per-use, credits | Already integrated |
| **[Recharts](https://recharts.org)** | Composable chart library (React) | Free (MIT) | Report charts, analytics panels |
| **[FullCalendar](https://fullcalendar.io)** | Drag-and-drop calendar | Free (MIT) | Calendar workspace upgrade |
| **[React Flow](https://reactflow.dev)** | Node-based workflow builder | Free (MIT) | Workflow/automation workspace |

## What to Build First (in order)

1. **Supabase Auth** ← replaces custom auth, enables OAuth for real
2. **Supabase Realtime** ← live activity feed, instant nudge delivery
3. **BlockNote / Tiptap** ← document workspace (proposals, notes, reports)
4. **Supabase Storage** ← file management, image uploads
5. **Novu** ← notification infrastructure
6. **FullCalendar** ← calendar workspace upgrade
7. **React Flow** ← workflow automation