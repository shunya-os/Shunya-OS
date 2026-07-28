---
version: alpha
name: SHUNYA
description: An operating system for human organizations. Warm minimalism, editorial typography, gold-accented calm.
colors:
  bg: "#fbfaf8"
  surface: "#ffffff"
  nav-bg: "#fefefe"
  artwork-bg: "#f3ebe2"
  zone-left-bg: "#f3f2f2"
  zone-center-bg: "#fafaf8"
  zone-right-bg: "#ebebea"
  top-bar-bg: "#faf9f8"
  text: "#1a1c1d"
  text-secondary: "rgba(26,28,29,0.55)"
  text-tertiary: "rgba(26,28,29,0.35)"
  text-faint: "rgba(26,28,29,0.15)"
  gold: "#a4865f"
  gold-light: "#d4c0a8"
  gold-dark: "#8a7050"
  gold-glow: "rgba(164,134,95,0.08)"
  border: "rgba(26,28,29,0.07)"
  border-hover: "rgba(26,28,29,0.14)"
  glass: "rgba(255,255,255,0.6)"
  glass-border: "rgba(255,255,255,0.2)"
  health-green: "#51cf66"
  health-yellow: "#fab005"
  health-orange: "#fd7e14"
  health-red: "#ff6b6b"
  health-blue: "#74c0fc"
typography:
  hero:
    fontFamily: Playfair Display
    fontSize: 54px
    fontWeight: 400
    lineHeight: 1.08
    letterSpacing: "-0.025em"
  h1:
    fontFamily: Playfair Display
    fontSize: 42px
    fontWeight: 400
    lineHeight: 1.08
    letterSpacing: "-0.025em"
  h2:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  h3:
    fontFamily: Playfair Display
    fontSize: 24px
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: 300
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  display-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: 300
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    lineHeight: 1.5
  body-md:
    fontFamily: Inter
    fontSize: 14px
    lineHeight: 1.5
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    lineHeight: 1.5
  label:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: 600
    letterSpacing: "0.06em"
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: 600
    letterSpacing: "0.12em"
  nav:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: 400
    letterSpacing: "0.02em"
  nav-label:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: 600
    letterSpacing: "0.06em"
  button:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: 500
    letterSpacing: "0.02em"
  caption:
    fontFamily: Inter
    fontSize: 10px
    letterSpacing: "0.02em"
  mono:
    fontFamily: SF Mono
    fontSize: 13px
    lineHeight: 1.5
  devanagari:
    fontFamily: Noto Sans Devanagari
    fontSize: 36px
    fontWeight: 500
    letterSpacing: "0.06em"
rounded:
  sm: 10px
  md: 16px
  lg: 24px
  xl: 32px
  full: 9999px
spacing:
  unit: 4px
  space-1: 4px
  space-2: 8px
  space-3: 12px
  space-4: 16px
  space-5: 20px
  space-6: 24px
  space-8: 32px
  space-10: 40px
  space-12: 48px
  space-14: 56px
  space-16: 64px
  space-20: 80px
  space-24: 96px
  space-32: 128px
elevation:
  shadow-sm: "0 1px 4px rgba(26,28,29,0.03)"
  shadow-md: "0 2px 12px rgba(26,28,29,0.05)"
  shadow-lg: "0 4px 24px rgba(26,28,29,0.06)"
  shadow-xl: "0 8px 40px rgba(26,28,29,0.08)"
  shadow-gold: "0 4px 40px rgba(164,134,95,0.08)"
  shadow-button: "0 2px 8px rgba(26,28,29,0.06)"
  shadow-button-hover: "0 4px 16px rgba(26,28,29,0.1)"
motion:
  ease-default: "cubic-bezier(0.22, 1, 0.36, 1)"
  ease-out: "cubic-bezier(0.16, 1, 0.3, 1)"
  ease-in: "cubic-bezier(0.4, 0, 0.68, 0.06)"
  duration-fast: 200ms
  duration-normal: 400ms
  duration-slow: 600ms
  duration-slower: 800ms
  duration-slowest: 1200ms
components:
  button-primary:
    backgroundColor: "{colors.text}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: 9px 22px
    typography: "{typography.button}"
  button-primary-hover:
    opacity: 0.85
  button-primary-disabled:
    opacity: 0.4
  button-outline:
    backgroundColor: transparent
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: 9px 22px
    border: 1px solid "{colors.border}"
    typography: "{typography.button}"
  button-outline-hover:
    border: 1px solid "{colors.border-hover}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: 20px
    border: 1px solid "{colors.border}"
  card-hover:
    border: 1px solid "{colors.border-hover}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: 10px 14px
    border: 1px solid "{colors.border}"
    typography: "{typography.body-md}"
  input-focus:
    border: 1px solid rgba(26,28,29,0.2)
  input-placeholder:
    textColor: "{colors.text-faint}"
  nav-item:
    padding: 7px 16px
    typography: "{typography.nav}"
    textColor: "{colors.text-secondary}"
  nav-item-hover:
    backgroundColor: rgba(25,27,28,0.05)
    textColor: "{colors.text}"
  nav-item-active:
    backgroundColor: rgba(25,27,28,0.07)
    textColor: "{colors.text}"
    fontWeight: 500
  nav-section:
    typography: "{typography.nav-label}"
    textColor: "{colors.text-faint}"
    padding: 8px 16px 4px
  modal:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: 24px
    maxWidth: 480px
  modal-overlay:
    backgroundColor: rgba(250,249,247,0.97)
  timeline-item:
    padding: 10px 0
  tab:
    padding: 10px 16px
    typography: "{typography.body-sm}"
    textColor: "{colors.text-tertiary}"
  tab-active:
    textColor: "{colors.text}"
    borderBottom: 2px solid "{colors.text}"
  event-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: 20px
    border: 1px solid "{colors.border}"
  event-card-hover:
    border: 1px solid "{colors.gold-light}"
  conv-message-human:
    backgroundColor: "{colors.text}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: 10px 14px
    marginLeft: 32px
  conv-message-assistant:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.sm}"
    padding: 10px 14px
    border: 1px solid "{colors.border}"
    marginRight: 32px
  search-overlay:
    backgroundColor: rgba(250,249,247,0.97)
    backdropFilter: blur(12px)
  search-input:
    fontSize: 26px
    fontWeight: 300
    backgroundColor: transparent
    textColor: "{colors.text}"
    border: none
  link-chip:
    backgroundColor: "{colors.surface}"
    rounded: 20px
    padding: 6px 14px
    border: 1px solid "{colors.border}"
    textColor: "{colors.text-secondary}"
  link-chip-hover:
    border: 1px solid "{colors.border-hover}"
    textColor: "{colors.text}"
  skeleton:
    backgroundColor: "{colors.border}"
    rounded: "{rounded.sm}"
---