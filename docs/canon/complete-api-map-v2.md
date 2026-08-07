# SHUNYA Living Workspace — Complete Free API Integration Map v2.0

> Every dimension of human life, powered by free/open-source APIs.
> Zero licensing cost. Every API listed has a genuine free tier or is fully open source.

## How to Read This Map

Each capability lists:
- **Life Dimension** — what area of human life this serves
- **Free API** — the actual service/library with URL
- **License / Free Tier** — proof it's free
- **Current Status** — ✅ built, ⚡ needs integration, 📋 planned
- **Time Saved per Week** — how much human time this returns

---

## 1. AUTH & IDENTITY (Foundation Layer)

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Email/password auth | [Supabase Auth](https://supabase.com/auth) | 50,000 MAU | ⚡ | — |
| Google OAuth | Supabase Auth (built-in) | Included | ⚡ | 5 min/week |
| GitHub OAuth | Supabase Auth (built-in) | Included | ⚡ | 5 min/week |
| Magic link login | Supabase Auth | Included | 📋 | 2 min/week |
| Phone auth | Supabase Auth | Included | 📋 | — |
| Session management | Supabase Auth JS client | Included | ⚡ | — |
| Realtime sync | [Supabase Realtime](https://supabase.com/realtime) | 2M msgs/month | 📋 | 30 min/week |

## 2. COMMUNICATION (Returning Time from Inbox Hell)

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Send email | [SMTP + Gmail API](https://developers.google.com/gmail/api) | 1M emails/day free | ✅ Built | 15 min/week |
| Read inbox | Gmail API | Free (auth) | ✅ GmailInbox | 30 min/week |
| Email triage | Gmail API + AI | Free (auth + OpenRouter) | 📋 | 45 min/week |
| WhatsApp messaging | [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api) | 1,000 conversations/month free | ✅ Built | 20 min/week |
| Telegram messaging | [Telegram Bot API](https://core.telegram.org/bots/api) | Unlimited, free | 📋 | 10 min/week |
| SMS notifications | [Twilio](https://www.twilio.com/try-twilio) | $15 free credits | 📋 | 5 min/week |
| Voice/video calls | [Jitsi Meet API](https://jitsi.org/api/) | Fully OSS, unlimited | 📋 | 30 min/meeting |
| Meeting scheduling | [Calendly alternative: Cal.com](https://cal.com) | Free (AGPL, self-host) | 📋 | 20 min/week |
| Email auto-reply AI | Gmail API + OpenRouter | Free (API credits) | 📋 | 20 min/week |

## 3. CALENDAR & TIME (The Second Biggest Time Return)

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Calendar view | [FullCalendar](https://fullcalendar.io) | Free (MIT) | ⚡ CalendarPanel | 5 min/week |
| Event management | [CalDAV (Radicale)](https://radicale.org) | Fully OSS | 📋 | 15 min/week |
| Google Calendar sync | [Google Calendar API](https://developers.google.com/calendar/api) | 1M queries/day free | 📋 | 30 min/week |
| Smart scheduling | [Cal.com API](https://cal.com) | Free self-host | 📋 | 20 min/week |
| Time blocking | FullCalendar + Custom | Free | 📋 | 15 min/week |
| Deadline tracking | Custom (already built) | — | ✅ Built | 10 min/week |

## 4. DOCUMENTS & CONTENT (Returning Time from Document Hell)

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Rich document editor | [BlockNote](https://www.blocknotejs.org) | Fully OSS (MIT) | 📋 | 2 hr/doc |
| Proposals | BlockNote + OpenRouter AI | Free (MIT) | ⚡ Proposal backend done | 1 hr/proposal |
| Notes & wikis | BlockNote | Free | 📋 | 30 min/week |
| PDF generation | [WeasyPrint](https://doc.courtbouillon.org/weasyprint/) / [PDFKit](https://pdfkit.org) | Free (BSD) | ✅ Built | 15 min/doc |
| PDF viewing | [PDF.js](https://mozilla.github.io/pdf.js) | Free (Apache 2) | 📋 | — |
| Markdown rendering | [Marked](https://marked.js.org) | Free (MIT) | 📋 | — |
| Contract signing | [DocuSeal](https://www.docuseal.co) | Free self-host (AGPL) | 📋 | 1 hr/contract |
| OCR / scanning | [Tesseract.js](https://tesseract.projectnaptha.com) | Free (Apache 2), in-browser | 📋 | 15 min/receipt |

## 5. MEDIA & ENTERTAINMENT (Joy, Not Time-Saving)

| Capability | Free API | Free Tier | Status | Joy Return |
|-----------|----------|-----------|--------|-----------|
| Music/video playback | [YouTube IFrame API](https://developers.google.com/youtube/iframe_api_reference) | Free, no API key | ✅ YouTubePlayer | High |
| Podcast player | [Podcast Index API](https://podcastindex.org) | Free, OSS | 📋 | High |
| Movie/TV tracking | [TMDB API](https://www.themoviedb.org/documentation/api) | Free | 📋 | Medium |
| Book tracking | [Open Library API](https://openlibrary.org/developers/api) | Free, OSS | 📋 | Medium |
| Image generation | [OpenRouter (AI image)](https://openrouter.ai) | Pay-per-use, credits | ✅ Built | Medium |
| Music generation | [Facebook AudioCraft](https://github.com/facebookresearch/audiocraft) | Fully OSS (MIT) | 📋 | High |
| Art exploration | [MET Museum API](https://metmuseum.github.io) | Free | 📋 | Low |

## 6. MAPS & TRAVEL

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Interactive maps | [Leaflet](https://leafletjs.com) + [OpenStreetMap](https://www.openstreetmap.org) | Free (BSD), OSS tiles | 📋 | — |
| Routing / directions | [OSRM](https://project-osrm.org) | Free (BSD), self-host | 📋 | 15 min/trip |
| Public transport | [OpenTripPlanner](https://www.opentripplanner.org) | Free (LGPL) | 📋 | 10 min/trip |
| Places / POIs | [Overpass API](https://overpass-api.de) (OpenStreetMap) | Free | 📋 | 10 min/search |
| Geocoding | [Nominatim](https://nominatim.org) | Free (no key, rate-limited) | 📋 | 5 min/address |
| Weather | [Open-Meteo](https://open-meteo.com) | Free, no API key | 📋 | 5 min/week |
| Currency conversion | [ExchangeRate-API](https://www.exchangerate-api.com) | 1,500 requests/month free | 📋 | 2 min/transaction |
| Time zones | [TimeZoneDB](https://timezonedb.com) | Free tier | 📋 | 2 min/meeting |

## 7. FINANCE & MONEY

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Invoice generation | Custom (already built) | — | ✅ Built | 30 min/invoice |
| Expense tracking | Tesseract.js OCR + Custom | Free | 📋 | 20 min/week |
| Budget tracking | Custom | — | 📋 | 15 min/week |
| Investment tracking | [Yahoo Finance API](https://finance.yahoo.com) | Free (unofficial) | 📋 | 10 min/week |
| Receipt scanning | Tesseract.js (in-browser) | Free | 📋 | 5 min/receipt |
| Tax document org | Custom | — | 📋 | 30 min/quarter |

## 8. LEARNING & KNOWLEDGE

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Research / papers | [ArXiv API](https://info.arxiv.org/help/api/index.html) | Free | ✅ ArXiv skill | 30 min/week |
| Wikipedia lookup | [Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page) | Free | 📋 | 5 min/query |
| Dictionary | [Free Dictionary API](https://dictionaryapi.dev) | Free, no key | 📋 | 1 min/word |
| Translation | [LibreTranslate](https://libretranslate.com) | Free self-host (AGPL) | 📋 | 10 min/doc |
| Book summaries | [Open Library API](https://openlibrary.org) | Free | 📋 | 5 min/book |
| Course tracking | Custom | — | 📋 | 10 min/week |
| Flashcard system | Custom (CRUD + spaced repetition) | — | 📋 | 20 min/week |
| Skill progress | Custom | — | 📋 | 5 min/day |

## 9. HEALTH & WELLNESS

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Step / activity tracking | [Web Bluetooth API](https://webbluetoothcg.github.io/web-bluetooth/) | Free, in-browser | 📋 | — |
| Nutrition lookup | [Open Food Facts API](https://world.openfoodfacts.org/data) | Free, OSS | 📋 | 5 min/meal |
| Medication reminders | Custom (cron + notification) | — | 📋 | 5 min/day |
| Water tracking | Custom | — | 📋 | 1 min/day |
| Mood journal | Custom | — | 📋 | 2 min/day |
| Exercise logging | Custom | — | 📋 | 5 min/day |
| Sleep tracking | Manual + Custom | — | 📋 | 2 min/day |

## 10. RELATIONSHIPS & SOCIAL

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Contact management | [CardDAV (Radicale)](https://radicale.org) | Fully OSS | 📋 | 10 min/week |
| Birthday reminders | Custom (cron) | — | 📋 | 15 min/week |
| Social posting | [Mastodon API](https://docs.joinmastodon.org/api/) | Free, OSS | 📋 | 15 min/week |
| Relationship tracking | Custom (nudge engine) | — | 📋 | — |
| Event planning | FullCalendar + Custom | Free | 📋 | 30 min/event |

## 11. HOME & LIFESTYLE

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Recipe lookup | [Spoonacular API](https://spoonacular.com/food-api) | 150 queries/day free | 📋 | 10 min/meal |
| Grocery list | Custom | — | 📋 | 10 min/week |
| Chore tracking | Custom | — | 📋 | 5 min/day |
| Home maintenance | Custom (cron reminders) | — | 📋 | 15 min/month |
| Pet care | Custom (cron) | — | 📋 | 5 min/day |

## 12. CREATIVITY & HOBBIES

| Capability | Free API | Free Tier | Status | Joy Return |
|-----------|----------|-----------|--------|-----------|
| Image generation | OpenRouter / [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | Free self-host | ✅ Built | High |
| Music generation | [AudioCraft](https://github.com/facebookresearch/audiocraft) | Fully OSS (MIT) | 📋 | High |
| Drawing / sketching | [Excalidraw](https://excalidraw.com) | Free (MIT), OSS | 📋 | High |
| ASCII art | [FIGlet](http://www.figlet.org) / [cowsay](https://en.wikipedia.org/wiki/Cowsay) | Free | ✅ Skill exists | Low |
| Screen recording | [FFmpeg](https://ffmpeg.org) | Free (LGPL) | 📋 | — |
| Photo editing | [Sharp](https://sharp.pixelplumbing.com) / [ImageMagick](https://imagemagick.org) | Free (Apache 2) | 📋 | 5 min/photo |

## 13. PRODUCTIVITY & ORGANIZATION

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Notes | BlockNote | Free (MIT) | 📋 | 30 min/week |
| Tasks | Custom (already built) | — | ✅ Built | 20 min/week |
| File storage | [Supabase Storage](https://supabase.com/storage) | 1GB free | 📋 | 15 min/week |
| Password manager | [Vaultwarden API](https://github.com/dani-garcia/vaultwarden) | Fully OSS | 📋 | 5 min/day |
| Bookmarks | Custom (CRUD) | — | 📋 | 5 min/week |
| Keyboard shortcuts | Custom (⌘K already works) | — | ✅ Built | 5 min/day |

## 15. STORAGE & SCALABILITY (No-Cost Growth)

| Capability | Free API / Service | Free Tier | Decades-Scale Strategy |
|-----------|-------------------|-----------|----------------------|
| **File storage** | [Supabase Storage](https://supabase.com/storage) | 1GB free, 10GB bandwidth | Store files only, use CDN for delivery. 1GB covers 10,000+ invoices/docs. |
| **Object storage** | [Cloudflare R2](https://www.cloudflare.com/products/r2/) | **10GB free**, no egress fees | S3-compatible, zero egress cost. Move to R2 when Supabase fills up. |
| **Database** | [Neon](https://neon.tech) (serverless PostgreSQL) | 500MB free, branching, auto-suspend | Branching for dev/staging. Auto-suspend when idle = near-zero cost. |
| **Database cache** | [Supabase PostgreSQL](https://supabase.com) | 500MB free | Shared with Supabase Auth project. One DB for auth + data. |
| **CDN / edge** | [Cloudflare Workers](https://workers.cloudflare.com) | 100k requests/day, CDN included | Offload static assets, API caching, image optimization. |
| **Server hosting** | [Fly.io](https://fly.io) | 3 shared VMs (256MB each) free | Run Flask backend + cron on free tier. Auto-sleep when idle. |
| **Serverless compute** | [Vercel](https://vercel.com) | 100GB bandwidth, 6000 build mins/month | Host frontend separately for zero-cost static serving. |
| **AI inference** | [Groq](https://wow.groq.com) | Free tier with rate limits | Significantly cheaper than OpenAI. Mixtral at 500 tok/s free. |
| **AI fallback** | [OpenRouter](https://openrouter.ai) | Pay-per-use, no monthly fee | $0.25/M tokens for most models. $25 = 100M tokens = months of usage. |
| **Search indexing** | [Meilisearch](https://www.meilisearch.com) | Self-hosted, fully OSS (MIT) | Replace Algolia. 1GB RAM serves millions of docs. |
| **Email sending** | [Resend](https://resend.com) | 100 emails/day free (or SMTP) | SMTP relay is free. Resend for transactional when needed. |
| **Monitoring** | [Uptime Kuma](https://github.com/louislam/uptime-kuma) | Self-hosted, fully OSS | Free uptime monitoring, notifications, status page. |

## 16. AI COST OPTIMIZATION

| Strategy | What It Does | Cost Impact |
|----------|-------------|-------------|
| **Groq for inference** | Runs Mixtral, Llama 3 at 500+ tok/s for free | $0 → saves 100% on inference |
| **OpenRouter for fallback** | Pay $0.25/M tokens only when needed | ~$5/month for moderate use |
| **Cache AI responses** | Store common AI results in DB/Redis | Reduces token spend 40-60% |
| **Local LLM (llama.cpp)** | Run on server for private tasks | One-time compute cost, zero ongoing |
| **Batch AI calls** | Queue non-urgent AI work in cron jobs | Better token utilization, fewer API calls |
| **Prompt compression** | Strip verbose AI outputs, use shorter prompts | 30-50% token reduction |

| Capability | Free API | Free Tier | Status | Time Saved |
|-----------|----------|-----------|--------|------------|
| Nudge engine | Custom (AI watches + cron) | — | ⚡ Recommendations done | 30 min/day |
| Job scheduling | [Cron](https://en.wikipedia.org/wiki/Cron) | Built into OS | ✅ Built | — |
| Workflow automation | [React Flow](https://reactflow.dev) | Free (MIT) | 📋 | 1 hr/week |
| Web scraping | [Playwright](https://playwright.dev) | Free (Apache 2) | ✅ Installed | — |
| Report generation | WeasyPrint + AI | Free | ✅ PDF generator | 30 min/report |
| Data export | Custom | — | 📋 | 15 min/export |

## Summary: The 80/20

The capabilities that return the MOST human time (top 10):

| Rank | Capability | API | Time Saved/Week | Effort to Build |
|------|-----------|-----|----------------|-----------------|
| 1 | **Supabase Auth** | Supabase | (Foundation) | 2-3 hrs |
| 2 | **Smart email triage** | Gmail API + AI | 45 min | 4 hrs |
| 3 | **Nudge engine** | Custom AI + cron | 30 min | ✅ Partial |
| 4 | **Document editor** | BlockNote | 2 hr/doc | 3 hrs |
| 5 | **Calendar sync** | Google Calendar API | 30 min | 4 hrs |
| 6 | **Live activity feed** | Supabase Realtime | 30 min | 2 hrs |
| 7 | **Meeting notes** | Jitsi + Whisper | 30 min/meeting | 4 hrs |
| 8 | **Receipt scanning** | Tesseract.js | 20 min | 2 hrs |
| 9 | **Contract signing** | DocuSeal | 1 hr/contract | 3 hrs |
| 10 | **Workflow automation** | React Flow | 1 hr/week | 4 hrs |