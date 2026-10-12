/**
 * SHUNYA i18n layer — lightweight language context.
 *
 * Languages: en (English), hi (Devanagari Hindi), hinglish (Romanized
 * Hinglish), auto (UI stays English; speech recognition falls back to the
 * browser default).
 *
 * Persistence: localStorage (shunya_lang) + best-effort report of the
 * preference to the backend profile preferences endpoint (locale field).
 *
 * The context has a safe default value, so components that use `useI18n()`
 * outside of a <LanguageProvider> still render with English strings
 * (important for unit tests that mount single components).
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export type LangCode = 'en' | 'hi' | 'hinglish' | 'auto';

export interface LanguageEntry {
  code: LangCode;
  /** Native label shown in the switcher. */
  label: string;
  /** Browser speech-recognition locale; undefined → browser default (auto). */
  speech: string | undefined;
  /** Backend `locale` preference value. */
  locale: string;
}

export const LANGUAGES: LanguageEntry[] = [
  { code: 'en', label: 'English', speech: 'en-US', locale: 'en' },
  { code: 'hi', label: 'हिन्दी', speech: 'hi-IN', locale: 'hi-IN' },
  { code: 'hinglish', label: 'Hinglish', speech: 'hi-IN', locale: 'en-IN' },
  { code: 'auto', label: 'Auto', speech: undefined, locale: 'auto' },
];

/** Map a UI language to the Web Speech API `lang` value. */
export function speechRecognitionLang(lang: LangCode): string {
  const entry = LANGUAGES.find((l) => l.code === lang);
  return entry?.speech ?? '';
}

export function localeForLang(lang: LangCode): string {
  const entry = LANGUAGES.find((l) => l.code === lang);
  return entry?.locale ?? 'en';
}

const STORAGE_KEY = 'shunya_lang';

type Dict = Record<string, string>;

const EN: Dict = {
  home: 'Home',
  search: 'Search',
  ask: 'Ask',
  new: 'New',
  save: 'Save',
  cancel: 'Cancel',
  settings: 'Settings',
  workspaceSettings: 'Workspace Settings',
  notifications: 'Notifications',
  logout: 'Logout',
  workspace: 'Workspace',
  signIn: 'Sign In',
  signInLoading: 'Signing in…',
  signOut: 'Sign out',
  createAccount: 'Create account',
  welcome: 'Welcome',
  loading: 'Loading…',
  noResults: 'No results found',
  searchPlaceholder: 'Search your business…',
  askPlaceholder: 'Ask anything…',
  askShunya: 'Ask SHUNYA or type a command…',
  voiceInput: 'Voice input',
  stopRecording: 'Stop recording',
  startRecording: 'Start voice input',
  recording: 'Recording… speak now',
  submit: 'Submit',
  clear: 'Clear',
  tryAgain: 'Try again',
  retry: 'Retry',
  email: 'Email',
  password: 'Password',
  forgotPassword: 'Forgot password?',
  or: 'OR',
  language: 'Language',
  collapse: 'Collapse',
  expand: 'Expand',
  open: 'Open',
  close: 'Close',
  back: 'Back',
  delete: 'Delete',
  edit: 'Edit',
  view: 'View',
  profile: 'Profile',
  help: 'Help',
  shortcuts: 'Shortcuts',
  analytics: 'Analytics',
  apiDocs: 'API Docs',
  team: 'Team',
  typeCommand: 'Type a command…',
  switchWorkspace: 'Switch to workspace…',
  shortcutsHelp: 'Keyboard shortcuts',
  everythingCalm: 'Everything is calm.',
  tapToContinue: 'Tap to continue',
  searchFailed: 'Search is unavailable right now. Please try again.',
  voiceUnsupported: 'Voice input is not supported in this browser.',
  micPermission: 'Microphone permission is required for voice input. Allow access in your browser and try again.',
  noMic: 'No microphone detected. Connect a microphone and try again.',
  networkError: 'Voice recognition requires a network connection. Check your connection and try again.',
  noSpeech: 'No speech detected. Please try again.',
  voiceUnavailable: 'Voice input unavailable',
  speechError: 'Voice input could not start.',
  voiceErrorHint: 'Voice input is unavailable in this browser.',
  draftPlaceholder: 'Your speech will appear here. You can edit it.',
  typeToSearch: 'Type to search, or press Enter to ask SHUNYA',
  pressEnter: 'Enter',
  resultsByType: 'Results',
  web: 'Web',
  openWeb: 'Open in new tab',
  micUnavailable: 'Voice is unavailable in this browser.',
  whatsInOrg: "What's in your organization",
  toolsAndHelp: 'Tools & Help',
  orgFooter: 'Ask SHUNYA or click to explore any area',
  searchYourBusiness: 'Search your business…',
};

const HI: Dict = {
  home: 'होम',
  search: 'खोज',
  ask: 'पूछें',
  new: 'नया',
  save: 'सहेजें',
  cancel: 'रद्द करें',
  settings: 'सेटिंग्स',
  workspaceSettings: 'कार्यक्षेत्र सेटिंग्स',
  notifications: 'सूचनाएँ',
  logout: 'लॉग आउट',
  workspace: 'कार्यक्षेत्र',
  signIn: 'साइन इन',
  signInLoading: 'साइन इन हो रहा है…',
  signOut: 'साइन आउट',
  createAccount: 'खाता बनाएं',
  welcome: 'स्वागत है',
  loading: 'लोड हो रहा है…',
  noResults: 'कोई परिणाम नहीं मिला',
  searchPlaceholder: 'अपना व्यवसाय खोजें…',
  askPlaceholder: 'कुछ भी पूछें…',
  askShunya: 'SHUNYA से पूछें या कमांड टाइप करें…',
  voiceInput: 'वॉइस इनपुट',
  stopRecording: 'रिकॉर्डिंग रोकें',
  startRecording: 'वॉइस इनपुट शुरू करें',
  recording: 'रिकॉर्ड हो रहा है… अभी बोलें',
  submit: 'जमा करें',
  clear: 'साफ़ करें',
  tryAgain: 'फिर कोशिश करें',
  retry: 'पुनः प्रयास करें',
  email: 'ईमेल',
  password: 'पासवर्ड',
  forgotPassword: 'पासवर्ड भूल गए?',
  or: 'या',
  language: 'भाषा',
  collapse: 'सिकोड़ें',
  expand: 'विस्तार करें',
  open: 'खोलें',
  close: 'बंद करें',
  back: 'वापस',
  delete: 'हटाएं',
  edit: 'संपादित करें',
  view: 'देखें',
  profile: 'प्रोफ़ाइल',
  help: 'सहायता',
  shortcuts: 'शॉर्टकट',
  analytics: 'विश्लेषण',
  apiDocs: 'API दस्तावेज़',
  team: 'टीम',
  typeCommand: 'कमांड टाइप करें…',
  switchWorkspace: 'कार्यक्षेत्र बदलें…',
  shortcutsHelp: 'कीबोर्ड शॉर्टकट',
  everythingCalm: 'सब कुछ शांत है।',
  tapToContinue: 'जारी रखने के लिए टैप करें',
  searchFailed: 'खोज अभी उपलब्ध नहीं है। कृपया फिर कोशिश करें।',
  voiceUnsupported: 'वॉइस इनपुट इस ब्राउज़र में समर्थित नहीं है।',
  micPermission: 'वॉइस इनपुट के लिए माइक्रोफ़ोन अनुमति आवश्यक है। ब्राउज़र में अनुमति दें और फिर कोशिश करें।',
  noMic: 'कोई माइक्रोफ़ोन नहीं मिला। माइक्रोफ़ोन जोड़ें और फिर कोशिश करें।',
  networkError: 'वॉइस पहचान के लिए इंटरनेट कनेक्शन आवश्यक है। कनेक्शन जांचें और फिर कोशिश करें।',
  noSpeech: 'कोई आवाज़ नहीं सुनी गई। कृपया फिर कोशिश करें।',
  voiceUnavailable: 'वॉइस इनपुट उपलब्ध नहीं',
  speechError: 'वॉइस इनपुट शुरू नहीं हो सका।',
  voiceErrorHint: 'वॉइस इनपुट इस ब्राउज़र में उपलब्ध नहीं है।',
  draftPlaceholder: 'आपकी आवाज़ यहाँ दिखाई देगी। आप इसे संपादित कर सकते हैं।',
  typeToSearch: 'खोजने के लिए टाइप करें, या SHUNYA से पूछने के लिए Enter दबाएं',
  pressEnter: 'Enter',
  resultsByType: 'परिणाम',
  web: 'वेब',
  openWeb: 'नए टैब में खोलें',
  micUnavailable: 'वॉइस इस ब्राउज़र में उपलब्ध नहीं है।',
  whatsInOrg: 'आपके संगठन में क्या है',
  toolsAndHelp: 'उपकरण और सहायता',
  orgFooter: 'SHUNYA से पूछें या किसी भी क्षेत्र को देखने के लिए क्लिक करें',
  searchYourBusiness: 'अपना व्यवसाय खोजें…',
};

const HINGLISH: Dict = {
  home: 'Home',
  search: 'Khoj',
  ask: 'Poochho',
  new: 'Naya',
  save: 'Save karo',
  cancel: 'Rad kar do',
  settings: 'Settings',
  workspaceSettings: 'Workspace Settings',
  notifications: 'Soochnayein',
  logout: 'Logout',
  workspace: 'Kaaryakshetra',
  signIn: 'Sign in karo',
  signInLoading: 'Sign in ho raha hai…',
  signOut: 'Sign out karo',
  createAccount: 'Account banao',
  welcome: 'Swagat hai',
  loading: 'Load ho raha hai…',
  noResults: 'Koi result nahi mila',
  searchPlaceholder: 'Apna business khojo…',
  askPlaceholder: 'Kuch bhi poochho…',
  askShunya: 'SHUNYA se poochho ya command likho…',
  voiceInput: 'Voice input',
  stopRecording: 'Recording band karo',
  startRecording: 'Voice input shuru karo',
  recording: 'Recording… ab bolo',
  submit: 'Submit karo',
  clear: 'Saaf karo',
  tryAgain: 'Phir se koshish karo',
  retry: 'Phir koshish karo',
  email: 'Email',
  password: 'Password',
  forgotPassword: 'Password bhool gaye?',
  or: 'ya',
  language: 'Bhasha',
  collapse: 'Chhota karo',
  expand: 'Bada karo',
  open: 'Kholo',
  close: 'Band karo',
  back: 'Wapas',
  delete: 'Hatao',
  edit: 'Sampadit karo',
  view: 'Dekho',
  profile: 'Profile',
  help: 'Madad',
  shortcuts: 'Shortcuts',
  analytics: 'Analytics',
  apiDocs: 'API Docs',
  team: 'Team',
  typeCommand: 'Command likho…',
  switchWorkspace: 'Workspace badlo…',
  shortcutsHelp: 'Keyboard shortcuts',
  everythingCalm: 'Sab kuch shant hai.',
  tapToContinue: 'Aage badhne ke liye tap karo',
  searchFailed: 'Khoj abhi available nahi hai. Phir se try karo.',
  voiceUnsupported: 'Voice input is browser mein support nahi hai.',
  micPermission: 'Voice input ke liye microphone permission zaroori hai. Browser mein allow karo aur phir try karo.',
  noMic: 'Koi microphone nahi mila. Microphone jodo aur phir try karo.',
  networkError: 'Voice recognition ke liye internet connection zaroori hai. Connection check karo aur try karo.',
  noSpeech: 'Koi awaaz nahi sunai di. Phir se try karo.',
  voiceUnavailable: 'Voice input available nahi',
  speechError: 'Voice input shuru nahi ho saka.',
  voiceErrorHint: 'Voice input is browser mein available nahi hai.',
  draftPlaceholder: 'Aapki awaaz yahan dikhegi. Aap ise edit kar sakte ho.',
  typeToSearch: 'Khojne ke liye type karo, ya SHUNYA se poochhne ke liye Enter dabao',
  pressEnter: 'Enter',
  resultsByType: 'Results',
  web: 'Web',
  openWeb: 'Naye tab mein kholo',
  micUnavailable: 'Voice is browser mein available nahi hai.',
  whatsInOrg: 'Aapke sangathan mein kya hai',
  toolsAndHelp: 'Tools aur Madad',
  orgFooter: 'SHUNYA se poochho ya kisi bhi area ko explore karne ke liye click karo',
  searchYourBusiness: 'Apna business khojo…',
};

const DICTS: Record<LangCode, Dict> = { en: EN, hi: HI, hinglish: HINGLISH, auto: EN };

function resolveInitialLang(): LangCode {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'en' || saved === 'hi' || saved === 'hinglish' || saved === 'auto') {
      return saved;
    }
    if ((navigator.language || '').toLowerCase().startsWith('hi')) return 'hi';
  } catch {
    /* storage unavailable */
  }
  return 'en';
}

export interface I18nValue {
  lang: LangCode;
  setLang: (lang: LangCode) => void;
  t: (key: string) => string;
}

const noopSetLang = (_: LangCode) => {};

// Safe default — components render in English even without the provider
// (unit tests mount components directly; the real app wraps at the root).
const DEFAULT_VALUE: I18nValue = {
  lang: 'en',
  setLang: noopSetLang,
  t: (key: string) => EN[key] ?? key,
};

const I18nContext = createContext<I18nValue>(DEFAULT_VALUE);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<LangCode>(resolveInitialLang);

  const setLang = useCallback((next: LangCode) => {
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* storage unavailable */
    }
    // Best-effort backend report — the profile preferences endpoint accepts a
    // `locale` field. Fire-and-forget: failure must never break switching.
    const locale = localeForLang(next);
    fetch('/api/v1/profile/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ locale }),
    }).catch(() => {});
  }, []);

  useEffect(() => {
    document.documentElement.lang = localeForLang(lang);
  }, [lang]);

  const t = useCallback(
    (key: string) => DICTS[lang][key] ?? EN[key] ?? key,
    [lang],
  );

  const value = useMemo<I18nValue>(() => ({ lang, setLang, t }), [lang, setLang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  return useContext(I18nContext);
}

// ── Language switcher (Mantine ActionIcon + Menu, 🌐) ────────────────

import { ActionIcon, Menu } from '@mantine/core';
import { IconLanguage, IconCheck } from '@tabler/icons-react';

export function LanguageSwitcher({ size = 'md' }: { size?: 'xs' | 'sm' | 'md' | 'lg' }) {
  const { lang, setLang } = useI18n();
  return (
    <Menu shadow="md" width={180} position="bottom-end" withinPortal>
      <Menu.Target>
        <ActionIcon
          variant="subtle"
          color="gray"
          size={size}
          aria-label="Language"
          title="Language"
          data-testid="language-switcher"
        >
          <IconLanguage size={16} />
        </ActionIcon>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>Language / भाषा / Bhasha</Menu.Label>
        {LANGUAGES.map((l) => (
          <Menu.Item
            key={l.code}
            rightSection={lang === l.code ? <IconCheck size={14} /> : null}
            onClick={() => setLang(l.code)}
          >
            {l.label}
          </Menu.Item>
        ))}
      </Menu.Dropdown>
    </Menu>
  );
}