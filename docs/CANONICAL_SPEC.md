# SHUNYA Canonical Landing Page — Design Specification

Source: `static/shunya_canonical_visual.png` (1536×1024px)

## 1. Layout & Dimensions

| Measurement | Value | Notes |
|------------|-------|-------|
| Page width | 1536px | Full-width browser screenshot |
| Page height | 1024px | Full viewport |
| Navigation height | 52px | Estimated from screenshot |
| Hero section | y=52 to y=411 | ~359px tall |
| Event cards section | y=411 to y=~540 | ~129px |
| Industry strip | y=~540 to y=~750 | ~210px |
| Footer | y=~950 to y=1024 | ~74px |
| Right sidebar | x=1236 to x=1536 | 300px wide (workspace, not landing page) |

## 2. Navigation

| Element | Value |
|---------|-------|
| Height | 52px |
| Background | #fefefe |
| Gold dot | 5px, #a4865f, at ~x=28, y=22 |
| Logo | "SHUNYA", 13px, 500 weight |
| Nav links | 11px, 400 weight, #rgba(26,28,29,0.28) |
| Link gap | 28px |
| Nav padding | 0 32px |

## 3. Hero Section

| Element | Value |
|---------|-------|
| Heading font | Playfair Display, serif |
| Heading size | 54px |
| Heading weight | 400 (roman), 400 italic (line 2) |
| Heading tracking | -0.025em |
| Heading leading | 1.08 |
| Heading color | #1a1c1d |
| Heading left | x=90px from viewport edge |
| Line 1 y | y=158 |
| Line 2 y | y=170 |
| Body text font | Inter, 14px, 400 weight |
| Body text color | rgba(26,28,29,0.5) |
| Body leading | 1.7 |
| Body max-width | 380px |
| Body left | x=93px |
| CTA y | y=412 |
| CTA width | 215px |
| CTA height | ~18px |
| CTA padding | 9px 22px |
| CTA radius | 10px |
| CTA font | 12px, 500 weight |
| Primary CTA bg | #1a1c1d |
| Secondary CTA | 1px border, transparent |

## 4. Artwork Panel

| Element | Value |
|---------|-------|
| Width | 736px |
| Height | 425px |
| Aspect ratio | 736:425 |
| Background | #f8f6f2 |
| Border radius | 20px |
| Top | y=65 |
| Left | x=500 |

## 5. Event Cards Section

| Element | Value |
|---------|-------|
| Section top | y=411 |
| Content | Dark text beginning at y=500 |
| Background | #fbfaf8 (page bg) |

## 6. Industry Strip

| Element | Value |
|---------|-------|
| Section top | y=~540 |
| Icon area | y=740-750 |
| Icon color | ~#6f7373 (mid gray) |
| Background | #fbfaf8 (page bg) |

## 7. Footer

| Element | Value |
|---------|-------|
| Height | ~74px |
| Content y | y=1023 |
| Background | #fbfaf8 (page bg) |

## 8. Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| Page bg | #fbfaf8 | Page background |
| Nav bg | #fefefe | Navigation strip |
| Text | #1a1c1d | Primary text |
| Text soft | rgba(26,28,29,0.5) | Body text |
| Text faint | rgba(26,28,29,0.28) | Nav links |
| Gold | #a4865f | Accent dot, ribbons |
| Artwork bg | #f8f6f2 | Artwork panel |
| Border | rgba(26,28,29,0.07) | Dividers, outline buttons |
| CTA bg | #1a1c1d | Primary button |

## 9. Typography Scale

| Element | Font | Size | Weight | Style |
|---------|------|------|--------|-------|
| Heading | Playfair Display | 54px | 400 | Roman / Italic |
| Body | Inter | 14px | 400 | — |
| CTA | Inter | 12px | 500 | — |
| Nav logo | Inter | 13px | 500 | — |
| Nav links | Inter | 11px | 400 | — |
| Section label | Inter | 11px | 600 | Uppercase, 0.12em tracking |

## 10. Spacing System

| Token | Value |
|-------|-------|
| Base unit | 4px |
| Nav padding | 32px |
| Link gap | 28px |
| Body margin-bottom | 36px |
| Section gap | ~80px |
| Card gap | ~16px |