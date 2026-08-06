/**
 * ContentStudio 4.0 — Jasper-level AI content generation studio.
 *
 * 9 content formats: Blog, Social, Email, Product, PR, SEO, Ad, Landing, Repurpose
 * Brand Voice System: 5 profiles (Professional, Casual, Luxury, Technical, Friendly)
 * Tone Control Slider: 5 levels from Very Professional to Very Casual
 * History tab with localStorage persistence
 *
 * Warm glass-morphism design, inline CSS.
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import {
  FileText,
  Hash,
  Mail,
  Package,
  Newspaper,
  Search,
  Megaphone,
  Layout,
  RefreshCw,
  History,
  BookOpen,
  Copy,
  Check,
  Save,
  Trash2,
  Edit3,
  AlertCircle,
  Loader2,
  Sparkles,
  Sliders,
} from 'lucide-react';

// ── Types ─────────────────────────────────────────────────────

export type ToneOption = 'professional' | 'casual' | 'funny';
export type ContentFormat =
  | 'blog'
  | 'social'
  | 'email'
  | 'product'
  | 'press'
  | 'seo'
  | 'ad'
  | 'landing'
  | 'repurpose'
  | 'history';

export type BrandVoice = 'professional' | 'casual' | 'luxury' | 'technical' | 'friendly';
export type ToneLevel = 1 | 2 | 3 | 4 | 5;
export type SocialPlatform = 'twitter' | 'linkedin' | 'instagram' | 'threads';
export type AdPlatform = 'google' | 'facebook' | 'linkedin';

export interface SavedContent {
  id: string;
  format: ContentFormat;
  label: string;
  content: string;
  createdAt: string;
}

export interface BrandVoiceProfile {
  label: string;
  formality: string;
  vocabulary: string;
  sentenceLength: string;
  promptSuffix: string;
}

// ── API helpers ──

function generateId(): string {
  return `cnt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

// ── Constants ─────────────────────────────────────────────────

const BRAND_VOICES: { value: BrandVoice; profile: BrandVoiceProfile }[] = [
  {
    value: 'professional',
    profile: {
      label: 'Professional',
      formality: 'High',
      vocabulary: 'Business-grade',
      sentenceLength: 'Moderate',
      promptSuffix:
        'Use a professional, polished tone. Prefer clear business vocabulary, moderate sentence length, and a confident but respectful voice. Avoid slang and overly casual expressions.',
    },
  },
  {
    value: 'casual',
    profile: {
      label: 'Casual',
      formality: 'Low',
      vocabulary: 'Conversational',
      sentenceLength: 'Short',
      promptSuffix:
        'Use a casual, friendly tone. Write as if speaking to a friend. Use contractions, short sentences, and everyday language. Be warm and approachable.',
    },
  },
  {
    value: 'luxury',
    profile: {
      label: 'Luxury',
      formality: 'Very High',
      vocabulary: 'Refined / elevated',
      sentenceLength: 'Longer, flowing',
      promptSuffix:
        'Use a sophisticated, luxurious tone. Employ refined vocabulary, elegant phrasing, and flowing sentences. Evoke exclusivity and premium quality. Avoid anything that feels mass-market or ordinary.',
    },
  },
  {
    value: 'technical',
    profile: {
      label: 'Technical',
      formality: 'High',
      vocabulary: 'Domain-specific',
      sentenceLength: 'Moderate to long',
      promptSuffix:
        'Use a technical, precise tone. Employ domain-specific terminology where appropriate. Prioritize accuracy and clarity over flair. Use structured explanations suitable for an expert audience.',
    },
  },
  {
    value: 'friendly',
    profile: {
      label: 'Friendly',
      formality: 'Low',
      vocabulary: 'Warm, simple',
      sentenceLength: 'Short to moderate',
      promptSuffix:
        'Use a warm, friendly tone. Be encouraging and positive. Use simple, accessible language that makes the reader feel welcome. Include occasional exclamation points to convey enthusiasm.',
    },
  },
];

const FORMAT_TABS: { value: ContentFormat; icon: React.ReactNode; label: string }[] = [
  { value: 'blog', icon: <FileText size={12} />, label: 'Blog Post' },
  { value: 'social', icon: <Hash size={12} />, label: 'Social Post' },
  { value: 'email', icon: <Mail size={12} />, label: 'Email Campaign' },
  { value: 'product', icon: <Package size={12} />, label: 'Product Desc' },
  { value: 'press', icon: <Newspaper size={12} />, label: 'Press Release' },
  { value: 'seo', icon: <Search size={12} />, label: 'SEO Meta' },
  { value: 'ad', icon: <Megaphone size={12} />, label: 'Ad Copy' },
  { value: 'landing', icon: <Layout size={12} />, label: 'Landing Page' },
  { value: 'repurpose', icon: <RefreshCw size={12} />, label: 'Repurpose' },
  { value: 'history', icon: <History size={12} />, label: 'History' },
];

const SOCIAL_PLATFORMS: { value: SocialPlatform; label: string; limit: number }[] = [
  { value: 'twitter', label: 'Twitter / X', limit: 280 },
  { value: 'linkedin', label: 'LinkedIn', limit: 3000 },
  { value: 'instagram', label: 'Instagram', limit: 2200 },
  { value: 'threads', label: 'Threads', limit: 500 },
];

const AD_PLATFORMS: { value: AdPlatform; label: string }[] = [
  { value: 'google', label: 'Google Ads' },
  { value: 'facebook', label: 'Facebook Ads' },
  { value: 'linkedin', label: 'LinkedIn Ads' },
];

const TONE_LABELS: Record<number, string> = {
  1: 'Very Professional',
  2: 'Professional',
  3: 'Neutral',
  4: 'Casual',
  5: 'Very Casual',
};

const STORAGE_KEY = 'shunya_content_saved';

// ── Helpers ───────────────────────────────────────────────────

function loadSaved(): SavedContent[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveToStorage(items: SavedContent[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

function wordCount(text: string): number {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

function charCount(text: string): number {
  return text.length;
}

function getToneStyleDirective(toneLevel: ToneLevel): string {
  const dirs: Record<number, string> = {
    1: 'Write in a very formal, highly professional tone. Use sophisticated vocabulary, complex sentences, and maintain strict formality. Avoid any contractions or colloquialisms.',
    2: 'Write in a professional tone. Use business-appropriate vocabulary and moderate sentence length. Maintain a polished but accessible voice.',
    3: 'Write in a neutral, balanced tone. Use straightforward language that is neither too formal nor too casual. Aim for clarity and readability.',
    4: 'Write in a casual, relaxed tone. Use conversational language, contractions, and shorter sentences. Be friendly and approachable.',
    5: 'Write in a very casual, informal tone. Use everyday language, slang where appropriate, and very short sentences. Be highly conversational and warm.',
  };
  return dirs[toneLevel] || dirs[3];
}

function getToneBasedTemperature(toneLabel: string): number {
  // Map tone labels to temperatures for non-numeric tones
  const map: Record<string, number> = {
    'Very Professional': 0.3,
    Professional: 0.4,
    Neutral: 0.6,
    Casual: 0.75,
    'Very Casual': 0.85,
  };
  return map[toneLabel] ?? 0.6;
}

// ── AI Chat Helper ────────────────────────────────────────────

async function generateContent(prompt: string, system: string, temperature?: number): Promise<string> {
  const resp = await fetch('/api/v1/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: prompt },
      ],
      temperature: temperature ?? 0.7,
      max_tokens: 4096,
    }),
  });
  if (!resp.ok) {
    const errBody = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
    throw new Error(errBody.error || `AI service error (${resp.status})`);
  }
  const result = await resp.json();
  if (!result.content) {
    throw new Error(result.error || 'AI returned empty content');
  }
  return result.content;
}

// ── Sub-components ────────────────────────────────────────────

function FormatTabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button className={`cs-tab-btn ${active ? 'cs-tab-active' : ''}`} onClick={onClick} title={label}>
      {icon}
      <span>{label}</span>
    </button>
  );
}

function CopyButton({ text, size = 12 }: { text: string; size?: number }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [text]);
  return (
    <button className="cs-icon-btn" onClick={handleCopy} title="Copy">
      {copied ? <Check size={size} /> : <Copy size={size} />}
    </button>
  );
}

function BrandVoiceSelector({
  value,
  onChange,
}: {
  value: BrandVoice;
  onChange: (v: BrandVoice) => void;
}) {
  return (
    <div className="cs-field">
      <label className="cs-label">Brand Voice</label>
      <div className="cs-voice-grid">
        {BRAND_VOICES.map((b) => (
          <button
            key={b.value}
            className={`cs-voice-btn ${value === b.value ? 'cs-voice-active' : ''}`}
            onClick={() => onChange(b.value)}
          >
            <BookOpen size={11} />
            <span>{b.profile.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function ToneControl({
  value,
  onChange,
}: {
  value: ToneLevel;
  onChange: (v: ToneLevel) => void;
}) {
  return (
    <div className="cs-field">
      <label className="cs-label">Tone Control</label>
      <div className="cs-tone-slider-row">
        <Sliders size={12} className="cs-slider-icon" />
        <input
          type="range"
          min={1}
          max={5}
          step={1}
          value={value}
          onChange={(e) => onChange(Number(e.target.value) as ToneLevel)}
          className="cs-range"
        />
        <span className="cs-tone-label">{TONE_LABELS[value]}</span>
      </div>
    </div>
  );
}

function CharacterCount({ current, max }: { current: number; max: number }) {
  const ratio = current / max;
  let color = 'rgba(26,28,29,0.35)';
  if (ratio > 0.9) color = '#B91C1C';
  else if (ratio > 0.75) color = '#D97706';
  const pct = Math.min(ratio * 100, 100);
  return (
    <div className="cs-char-count">
      <div className="cs-char-bar-track">
        <div className="cs-char-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="cs-char-text" style={{ color }}>
        {current} / {max}
      </span>
    </div>
  );
}

function WordCountDisplay({ text }: { text: string }) {
  const wc = wordCount(text);
  return <span className="cs-meta">{wc} words</span>;
}

function ReadabilityScore({ text }: { text: string }) {
  // Simple Flesch-like heuristic based on avg word length and sentence length
  const words = text.trim().split(/\s+/);
  if (words.length < 5) return <span className="cs-meta">Readability: —</span>;
  const sentences = text.split(/[.!?]+/).filter((s) => s.trim().length > 0);
  const avgWordLen = words.reduce((sum, w) => sum + w.length, 0) / words.length;
  const avgSentLen = words.length / Math.max(sentences.length, 1);
  // Rough score 0-100, higher = easier
  const score = Math.max(0, Math.min(100, 206.835 - 1.015 * avgSentLen - 84.6 * avgWordLen));
  let grade: string;
  if (score >= 90) grade = 'Very Easy';
  else if (score >= 70) grade = 'Easy';
  else if (score >= 50) grade = 'Fairly Easy';
  else if (score >= 30) grade = 'Standard';
  else if (score >= 10) grade = 'Fairly Difficult';
  else grade = 'Difficult';
  return (
    <span className="cs-meta" title={`Readability score: ${Math.round(score)}`}>
      Readability: {grade}
    </span>
  );
}

function FormatPreview({
  content,
  onSave,
  showStats,
}: {
  content: string;
  onSave: () => void;
  showStats?: boolean;
}) {
  return (
    <div className="cs-output">
      <div className="cs-output-header">
        <span className="cs-output-label">Generated Content</span>
        <div className="cs-output-actions">
          {showStats && (
            <>
              <WordCountDisplay text={content} />
            </>
          )}
          <CopyButton text={content} />
          <button className="cs-icon-btn" onClick={onSave} title="Save">
            <Save size={12} />
          </button>
        </div>
      </div>
      {showStats && (
        <div className="cs-output-stats">
          <ReadabilityScore text={content} />
        </div>
      )}
      <pre className="cs-output-text">{content}</pre>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────

export function ContentStudio() {
  const [activeFormat, setActiveFormat] = useState<ContentFormat>('blog');
  const [generating, setGenerating] = useState(false);
  const [output, setOutput] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedItems, setSavedItems] = useState<SavedContent[]>(() => loadSaved());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  // Brand Voice & Tone
  const [brandVoice, setBrandVoice] = useState<BrandVoice>('professional');
  const [toneLevel, setToneLevel] = useState<ToneLevel>(3);

  const mountedRef = useRef(true);

  // ── Blog fields ──
  const [blogTopic, setBlogTopic] = useState('');
  const [blogKeywords, setBlogKeywords] = useState('');
  const [blogAudience, setBlogAudience] = useState('');
  const [blogTone, setBlogTone] = useState<ToneOption>('professional');
  const [blogLength, setBlogLength] = useState<'short' | 'medium' | 'long'>('medium');

  // ── Social fields ──
  const [socialPlatform, setSocialPlatform] = useState<SocialPlatform>('twitter');
  const [socialTopic, setSocialTopic] = useState('');
  const [socialMessage, setSocialMessage] = useState('');
  const [socialHashtags, setSocialHashtags] = useState('');
  const [socialCta, setSocialCta] = useState('');

  // ── Email fields ──
  const [emailSubject, setEmailSubject] = useState('');
  const [emailPreheader, setEmailPreheader] = useState('');
  const [emailMessage, setEmailMessage] = useState('');
  const [emailCtaText, setEmailCtaText] = useState('');
  const [emailAudience, setEmailAudience] = useState('');

  // ── Product fields ──
  const [productName, setProductName] = useState('');
  const [productFeatures, setProductFeatures] = useState('');
  const [productAudience, setProductAudience] = useState('');
  const [productTone, setProductTone] = useState<ToneOption>('professional');

  // ── Press Release fields ──
  const [pressHeadline, setPressHeadline] = useState('');
  const [pressSubhead, setPressSubhead] = useState('');
  const [pressDate, setPressDate] = useState('');
  const [pressLocation, setPressLocation] = useState('');
  const [pressQuoteSource, setPressQuoteSource] = useState('');
  const [pressQuote, setPressQuote] = useState('');
  const [pressBoilerplate, setPressBoilerplate] = useState('');

  // ── SEO fields ──
  const [seoPageTopic, setSeoPageTopic] = useState('');
  const [seoKeyword, setSeoKeyword] = useState('');
  const [seoCompetitorUrl, setSeoCompetitorUrl] = useState('');

  // ── Ad Copy fields ──
  const [adProduct, setAdProduct] = useState('');
  const [adAudience, setAdAudience] = useState('');
  const [adBenefit, setAdBenefit] = useState('');
  const [adPlatform, setAdPlatform] = useState<AdPlatform>('google');

  // ── Landing Page fields ──
  const [landingProduct, setLandingProduct] = useState('');
  const [landingValueProp, setLandingValueProp] = useState('');
  const [landingFeatures, setLandingFeatures] = useState('');
  const [landingAudience, setLandingAudience] = useState('');

  // ── Repurpose fields ──
  const [repurposeSource, setRepurposeSource] = useState('');
  const [repurposeTarget, setRepurposeTarget] = useState<ContentFormat>('social');

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // ── Save handler ──
  const handleSave = useCallback(
    (format: ContentFormat, label: string, content: string) => {
      const newItem: SavedContent = {
        id: generateId(),
        format,
        label,
        content,
        createdAt: new Date().toISOString(),
      };
      const updated = [newItem, ...savedItems];
      setSavedItems(updated);
      saveToStorage(updated);
    },
    [savedItems],
  );

  // ── Delete saved ──
  const handleDelete = useCallback(
    (id: string) => {
      const updated = savedItems.filter((i) => i.id !== id);
      setSavedItems(updated);
      saveToStorage(updated);
    },
    [savedItems],
  );

  // ── Edit saved ──
  const handleEditSave = useCallback(
    (id: string) => {
      const updated = savedItems.map((i) => (i.id === id ? { ...i, content: editContent } : i));
      setSavedItems(updated);
      saveToStorage(updated);
      setEditingId(null);
      setEditContent('');
    },
    [savedItems, editContent],
  );

  // ── Build system prompt helper ──
  const buildSystemPrompt = useCallback(
    (extra: string): string => {
      const voiceProfile = BRAND_VOICES.find((b) => b.value === brandVoice);
      const voice = voiceProfile ? voiceProfile.profile.promptSuffix : '';
      const tone = getToneStyleDirective(toneLevel);
      return `${voice}\n\n${tone}\n\n${extra}`;
    },
    [brandVoice, toneLevel],
  );

  // ── Generic generate handler ──
  const doGenerate = useCallback(
    async (systemExtra: string, prompt: string) => {
      setGenerating(true);
      setError(null);
      setOutput(null);
      try {
        const system = buildSystemPrompt(systemExtra);
        const temp = getToneBasedTemperature(TONE_LABELS[toneLevel]);
        const content = await generateContent(prompt, system, temp);
        if (mountedRef.current) setOutput(content);
      } catch (err: unknown) {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : 'Failed to generate content.');
        }
      } finally {
        if (mountedRef.current) setGenerating(false);
      }
    },
    [buildSystemPrompt, toneLevel],
  );

  // ── Format-specific generate functions ──
  const generateBlog = useCallback(() => {
    if (!blogTopic.trim()) return;
    const lenMap = { short: '300-500 words', medium: '800-1200 words', long: '1500-2500 words' };
    const systemExtra = `You are a professional blog writer. Write a blog post in a ${blogTone} tone. Target audience: ${blogAudience || 'general audience'}. Target length: ${lenMap[blogLength]}. Use markdown formatting with H2 and H3 subheadings. Include a meta description at the end.`;
    const prompt = `Write a blog post about: ${blogTopic}${blogKeywords ? `\n\nKeywords to include: ${blogKeywords}` : ''}`;
    doGenerate(systemExtra, prompt);
  }, [blogTopic, blogKeywords, blogAudience, blogTone, blogLength, doGenerate]);

  const generateSocial = useCallback(() => {
    if (!socialTopic.trim()) return;
    const platformInfo = SOCIAL_PLATFORMS.find((p) => p.value === socialPlatform)!;
    const systemExtra = `You are a social media content creator. Write a ${platformInfo.label} post (max ${platformInfo.limit} characters). Keep it concise and engaging.${socialHashtags ? ` Include these hashtags: ${socialHashtags}` : ''}${socialCta ? ` End with this CTA: ${socialCta}` : ''}`;
    const prompt = `Write a ${socialPlatform} post about: ${socialTopic}${socialMessage ? `\nKey message: ${socialMessage}` : ''}`;
    doGenerate(systemExtra, prompt);
  }, [socialTopic, socialPlatform, socialMessage, socialHashtags, socialCta, doGenerate]);

  const generateEmail = useCallback(() => {
    if (!emailMessage.trim()) return;
    const systemExtra = `You are an email marketing specialist. Write a compelling email campaign.${emailSubject ? ` Subject line: ${emailSubject}` : ' Generate a compelling subject line.'}${emailPreheader ? ` Preheader: ${emailPreheader}` : ''}${emailCtaText ? ` CTA button text: ${emailCtaText}` : ''}${emailAudience ? ` Target audience: ${emailAudience}` : ''} Format the body with a clear CTA button.`;
    const prompt = `Write an email about: ${emailMessage}`;
    doGenerate(systemExtra, prompt);
  }, [emailSubject, emailPreheader, emailMessage, emailCtaText, emailAudience, doGenerate]);

  const generateProduct = useCallback(() => {
    if (!productName.trim()) return;
    const systemExtra = `You are a product copywriter specializing in feature-to-benefit transformation. Write a compelling product description in a ${productTone} tone. Target audience: ${productAudience || 'general consumers'}. Transform each feature into a clear benefit. Include SEO-optimized keyword integration. Use bullet points for features.`;
    const prompt = `Write a product description for: ${productName}\n\nFeatures:\n${productFeatures || 'Describe key features'}${productAudience ? `\n\nTarget audience: ${productAudience}` : ''}`;
    doGenerate(systemExtra, prompt);
  }, [productName, productFeatures, productAudience, productTone, doGenerate]);

  const generatePress = useCallback(() => {
    if (!pressHeadline.trim()) return;
    const systemExtra = `You are a PR professional. Write a formal press release following AP style. Include a dateline, body paragraphs, a quote block, and an "About" section. Format strictly as a press release.`;
    const prompt = `Write a press release.\n\nHeadline: ${pressHeadline}\n${pressSubhead ? `Subhead: ${pressSubhead}\n` : ''}${pressDate ? `Date: ${pressDate}\n` : ''}${pressLocation ? `Location: ${pressLocation}\n` : ''}${pressQuoteSource ? `Quote from: ${pressQuoteSource}\nQuote: ${pressQuote || 'Provide a relevant quote'}\n` : ''}${pressBoilerplate ? `Company boilerplate: ${pressBoilerplate}\n` : ''}`;
    doGenerate(systemExtra, prompt);
  }, [pressHeadline, pressSubhead, pressDate, pressLocation, pressQuoteSource, pressQuote, pressBoilerplate, doGenerate]);

  const generateSeo = useCallback(() => {
    if (!seoPageTopic.trim()) return;
    const systemExtra = `You are an SEO specialist. Generate optimized meta tags for the given page topic. Title tag must be 50-60 characters. Meta description must be 150-160 characters. Suggest a URL slug and H1 heading.`;
    const prompt = `Generate SEO meta tags for topic: ${seoPageTopic}\n\nTarget keyword: ${seoKeyword || 'primary keyword'}${seoCompetitorUrl ? `\nCompetitor URL for reference: ${seoCompetitorUrl}` : ''}`;
    doGenerate(systemExtra, prompt);
  }, [seoPageTopic, seoKeyword, seoCompetitorUrl, doGenerate]);

  const generateAd = useCallback(() => {
    if (!adProduct.trim()) return;
    const platformLabel = AD_PLATFORMS.find((p) => p.value === adPlatform)!.label;
    const systemExtra = `You are an advertising copywriter specializing in ${platformLabel}. Generate 3 headline variants and 3 description variants. Include a CTA. Format the output as a comparison table for A/B testing.`;
    const prompt = `Write ad copy for: ${adProduct}\n\nTarget audience: ${adAudience || 'general'}\nKey benefit: ${adBenefit || 'main value proposition'}\nPlatform: ${platformLabel}`;
    doGenerate(systemExtra, prompt);
  }, [adProduct, adAudience, adBenefit, adPlatform, doGenerate]);

  const generateLanding = useCallback(() => {
    if (!landingProduct.trim()) return;
    const systemExtra = `You are a conversion copywriter. Write a complete landing page structure. Include: Hero section (headline + subheadline), 3 feature blocks with icon suggestions, pricing section structure, CTA, and FAQ (3-4 items). Format with clear section dividers.`;
    const prompt = `Write landing page copy for: ${landingProduct}\n\nValue proposition: ${landingValueProp || 'main value'}\nFeatures: ${landingFeatures || 'key features'}\nTarget audience: ${landingAudience || 'general'}`;
    doGenerate(systemExtra, prompt);
  }, [landingProduct, landingValueProp, landingFeatures, landingAudience, doGenerate]);

  const generateRepurpose = useCallback(() => {
    if (!repurposeSource.trim()) return;
    const targetLabels: Record<string, string> = {
      blog: 'a blog post',
      social: 'a social media post',
      email: 'an email campaign',
      product: 'a product description',
      press: 'a press release',
      seo: 'SEO meta tags',
      ad: 'ad copy',
      landing: 'a landing page',
    };
    const targetLabel = targetLabels[repurposeTarget] || 'content';
    const systemExtra = `You are a content repurposing specialist. Adapt the source content into ${targetLabel}. Preserve all key messages and core information. Adapt the tone and format to suit the target medium. Do not lose important details.`;
    const prompt = `Repurpose the following content into ${targetLabel}:\n\n---SOURCE CONTENT---\n${repurposeSource}`;
    doGenerate(systemExtra, prompt);
  }, [repurposeSource, repurposeTarget, doGenerate]);

  // Determine which generate function to call based on activeFormat
  const handleGenerate = useCallback(() => {
    switch (activeFormat) {
      case 'blog':
        generateBlog();
        break;
      case 'social':
        generateSocial();
        break;
      case 'email':
        generateEmail();
        break;
      case 'product':
        generateProduct();
        break;
      case 'press':
        generatePress();
        break;
      case 'seo':
        generateSeo();
        break;
      case 'ad':
        generateAd();
        break;
      case 'landing':
        generateLanding();
        break;
      case 'repurpose':
        generateRepurpose();
        break;
      default:
        break;
    }
  }, [
    activeFormat,
    generateBlog,
    generateSocial,
    generateEmail,
    generateProduct,
    generatePress,
    generateSeo,
    generateAd,
    generateLanding,
    generateRepurpose,
  ]);

  // Check if current format has valid inputs
  const canGenerate = ((): boolean => {
    switch (activeFormat) {
      case 'blog':
        return !!blogTopic.trim();
      case 'social':
        return !!socialTopic.trim();
      case 'email':
        return !!emailMessage.trim();
      case 'product':
        return !!productName.trim();
      case 'press':
        return !!pressHeadline.trim();
      case 'seo':
        return !!seoPageTopic.trim();
      case 'ad':
        return !!adProduct.trim();
      case 'landing':
        return !!landingProduct.trim();
      case 'repurpose':
        return !!repurposeSource.trim();
      default:
        return false;
    }
  })();

  // Label for saving
  const getSaveLabel = useCallback((): string => {
    switch (activeFormat) {
      case 'blog':
        return `Blog: ${blogTopic}`;
      case 'social':
        return `Social: ${socialTopic}`;
      case 'email':
        return `Email: ${emailSubject || emailMessage.slice(0, 30)}`;
      case 'product':
        return `Product: ${productName}`;
      case 'press':
        return `Press: ${pressHeadline}`;
      case 'seo':
        return `SEO: ${seoPageTopic}`;
      case 'ad':
        return `Ad: ${adProduct}`;
      case 'landing':
        return `Landing: ${landingProduct}`;
      case 'repurpose':
        return `Repurpose: ${repurposeSource.slice(0, 30)}`;
      default:
        return 'Content';
    }
  }, [
    activeFormat,
    blogTopic,
    socialTopic,
    emailSubject,
    emailMessage,
    productName,
    pressHeadline,
    seoPageTopic,
    adProduct,
    landingProduct,
    repurposeSource,
  ]);

  // ── Render ──
  return (
    <div className="cs-container">
      {/* Header */}
      <div className="cs-header">
        <div className="cs-header-left">
          <Sparkles size={14} style={{ color: '#6C4AE2' }} />
          <span className="cs-header-title">Content Studio 4.0</span>
        </div>
        <div className="cs-header-right">
          <span className="cs-header-count">{savedItems.length} saved</span>
        </div>
      </div>

      {/* Brand Voice & Tone Control */}
      <div className="cs-controls-row">
        <BrandVoiceSelector value={brandVoice} onChange={setBrandVoice} />
        <ToneControl value={toneLevel} onChange={setToneLevel} />
      </div>

      {/* Format Tabs */}
      <div className="cs-tabs">
        {FORMAT_TABS.map((tab) => (
          <FormatTabButton
            key={tab.value}
            active={activeFormat === tab.value}
            onClick={() => setActiveFormat(tab.value)}
            icon={tab.icon}
            label={tab.label}
          />
        ))}
      </div>

      {/* Tab Content */}
      <div className="cs-body">
        {activeFormat !== 'history' && (
          <div className="cs-tab-panel">
            {/* ── Blog Form ── */}
            {activeFormat === 'blog' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Topic</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={blogTopic}
                    onChange={(e) => setBlogTopic(e.target.value)}
                    placeholder="e.g., The Future of Remote Work"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Keywords (comma-separated)</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={blogKeywords}
                    onChange={(e) => setBlogKeywords(e.target.value)}
                    placeholder="e.g., remote work, productivity, WFH tips"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Target Audience</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={blogAudience}
                    onChange={(e) => setBlogAudience(e.target.value)}
                    placeholder="e.g., Startup founders, tech professionals"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Tone</label>
                  <div className="cs-tone-grid">
                    {(['professional', 'casual', 'funny'] as ToneOption[]).map((t) => (
                      <button
                        key={t}
                        className={`cs-tone-btn ${blogTone === t ? 'cs-tone-active' : ''}`}
                        onClick={() => setBlogTone(t)}
                      >
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="cs-field">
                  <label className="cs-label">Length</label>
                  <div className="cs-tone-grid">
                    {(['short', 'medium', 'long'] as const).map((l) => (
                      <button
                        key={l}
                        className={`cs-tone-btn ${blogLength === l ? 'cs-tone-active' : ''}`}
                        onClick={() => setBlogLength(l)}
                      >
                        {l.charAt(0).toUpperCase() + l.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* ── Social Form ── */}
            {activeFormat === 'social' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Platform</label>
                  <div className="cs-platform-grid">
                    {SOCIAL_PLATFORMS.map((p) => (
                      <button
                        key={p.value}
                        className={`cs-tone-btn ${socialPlatform === p.value ? 'cs-tone-active' : ''}`}
                        onClick={() => setSocialPlatform(p.value)}
                      >
                        {p.label} ({p.limit})
                      </button>
                    ))}
                  </div>
                </div>
                {socialPlatform && (
                  <CharacterCount
                    current={charCount(socialTopic + ' ' + socialMessage + ' ' + socialHashtags)}
                    max={SOCIAL_PLATFORMS.find((p) => p.value === socialPlatform)?.limit ?? 280}
                  />
                )}
                <div className="cs-field">
                  <label className="cs-label">Topic</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={socialTopic}
                    onChange={(e) => setSocialTopic(e.target.value)}
                    placeholder="e.g., New product launch announcement"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Key Message</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={socialMessage}
                    onChange={(e) => setSocialMessage(e.target.value)}
                    placeholder="What's the main thing to say?"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Hashtags</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={socialHashtags}
                    onChange={(e) => setSocialHashtags(e.target.value)}
                    placeholder="e.g., #innovation #tech"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">CTA</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={socialCta}
                    onChange={(e) => setSocialCta(e.target.value)}
                    placeholder="e.g., Sign up now, Learn more"
                  />
                </div>
              </>
            )}

            {/* ── Email Form ── */}
            {activeFormat === 'email' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Subject Line</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    placeholder="e.g., Your weekly digest is here"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Preheader</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={emailPreheader}
                    onChange={(e) => setEmailPreheader(e.target.value)}
                    placeholder="Short preview text after subject"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Key Message</label>
                  <textarea
                    className="cs-textarea"
                    value={emailMessage}
                    onChange={(e) => setEmailMessage(e.target.value)}
                    placeholder="What is the email about?"
                    rows={3}
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">CTA Text</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={emailCtaText}
                    onChange={(e) => setEmailCtaText(e.target.value)}
                    placeholder="e.g., Get Started, Download Now"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Target Audience</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={emailAudience}
                    onChange={(e) => setEmailAudience(e.target.value)}
                    placeholder="e.g., Newsletter subscribers, VIP customers"
                  />
                </div>
              </>
            )}

            {/* ── Product Form ── */}
            {activeFormat === 'product' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Product Name</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={productName}
                    onChange={(e) => setProductName(e.target.value)}
                    placeholder="e.g., SmartHome Hub Pro"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Features (list)</label>
                  <textarea
                    className="cs-textarea"
                    value={productFeatures}
                    onChange={(e) => setProductFeatures(e.target.value)}
                    placeholder="One feature per line&#10;e.g., 24-hour battery life&#10;Water resistant IP68&#10;Voice control"
                    rows={4}
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Target Audience</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={productAudience}
                    onChange={(e) => setProductAudience(e.target.value)}
                    placeholder="e.g., Homeowners, tech enthusiasts"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Tone</label>
                  <div className="cs-tone-grid">
                    {(['professional', 'casual', 'funny'] as ToneOption[]).map((t) => (
                      <button
                        key={t}
                        className={`cs-tone-btn ${productTone === t ? 'cs-tone-active' : ''}`}
                        onClick={() => setProductTone(t)}
                      >
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* ── Press Release Form ── */}
            {activeFormat === 'press' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Headline</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={pressHeadline}
                    onChange={(e) => setPressHeadline(e.target.value)}
                    placeholder="e.g., Company Launches Revolutionary Product"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Subhead</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={pressSubhead}
                    onChange={(e) => setPressSubhead(e.target.value)}
                    placeholder="Optional subheading"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Date</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={pressDate}
                    onChange={(e) => setPressDate(e.target.value)}
                    placeholder="e.g., August 3, 2026"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Location</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={pressLocation}
                    onChange={(e) => setPressLocation(e.target.value)}
                    placeholder="e.g., San Francisco, CA"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Quote Source</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={pressQuoteSource}
                    onChange={(e) => setPressQuoteSource(e.target.value)}
                    placeholder="e.g., CEO Name, Title"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Quote</label>
                  <textarea
                    className="cs-textarea"
                    value={pressQuote}
                    onChange={(e) => setPressQuote(e.target.value)}
                    placeholder="Quote from the source"
                    rows={3}
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Company Boilerplate</label>
                  <textarea
                    className="cs-textarea"
                    value={pressBoilerplate}
                    onChange={(e) => setPressBoilerplate(e.target.value)}
                    placeholder="Brief description of the company"
                    rows={3}
                  />
                </div>
              </>
            )}

            {/* ── SEO Form ── */}
            {activeFormat === 'seo' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Page Topic</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={seoPageTopic}
                    onChange={(e) => setSeoPageTopic(e.target.value)}
                    placeholder="e.g., Best CRM Software for Small Business"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Target Keyword</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={seoKeyword}
                    onChange={(e) => setSeoKeyword(e.target.value)}
                    placeholder="e.g., CRM for small business"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Competitor URL (optional)</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={seoCompetitorUrl}
                    onChange={(e) => setSeoCompetitorUrl(e.target.value)}
                    placeholder="e.g., https://competitor.com/product"
                  />
                </div>
              </>
            )}

            {/* ── Ad Copy Form ── */}
            {activeFormat === 'ad' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Platform</label>
                  <div className="cs-platform-grid">
                    {AD_PLATFORMS.map((p) => (
                      <button
                        key={p.value}
                        className={`cs-tone-btn ${adPlatform === p.value ? 'cs-tone-active' : ''}`}
                        onClick={() => setAdPlatform(p.value)}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="cs-field">
                  <label className="cs-label">Product / Service</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={adProduct}
                    onChange={(e) => setAdProduct(e.target.value)}
                    placeholder="e.g., AI-powered analytics platform"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Target Audience</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={adAudience}
                    onChange={(e) => setAdAudience(e.target.value)}
                    placeholder="e.g., Marketing directors at SaaS companies"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Key Benefit</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={adBenefit}
                    onChange={(e) => setAdBenefit(e.target.value)}
                    placeholder="e.g., Reduce churn by 40%"
                  />
                </div>
              </>
            )}

            {/* ── Landing Page Form ── */}
            {activeFormat === 'landing' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Product Name</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={landingProduct}
                    onChange={(e) => setLandingProduct(e.target.value)}
                    placeholder="e.g., CloudSync Pro"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Value Proposition</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={landingValueProp}
                    onChange={(e) => setLandingValueProp(e.target.value)}
                    placeholder="e.g., Sync all your files instantly"
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Features</label>
                  <textarea
                    className="cs-textarea"
                    value={landingFeatures}
                    onChange={(e) => setLandingFeatures(e.target.value)}
                    placeholder="One feature per line"
                    rows={4}
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Target Audience</label>
                  <input
                    className="cs-input"
                    type="text"
                    value={landingAudience}
                    onChange={(e) => setLandingAudience(e.target.value)}
                    placeholder="e.g., Remote teams, freelancers"
                  />
                </div>
              </>
            )}

            {/* ── Repurpose Form ── */}
            {activeFormat === 'repurpose' && (
              <>
                <div className="cs-field">
                  <label className="cs-label">Source Content</label>
                  <textarea
                    className="cs-textarea"
                    value={repurposeSource}
                    onChange={(e) => setRepurposeSource(e.target.value)}
                    placeholder="Paste your source content here (blog post, article, video transcript, etc.)"
                    rows={6}
                  />
                </div>
                <div className="cs-field">
                  <label className="cs-label">Target Format</label>
                  <div className="cs-platform-grid">
                    {FORMAT_TABS.filter((f) => f.value !== 'history' && f.value !== 'repurpose').map((f) => (
                      <button
                        key={f.value}
                        className={`cs-tone-btn ${repurposeTarget === f.value ? 'cs-tone-active' : ''}`}
                        onClick={() => setRepurposeTarget(f.value as ContentFormat)}
                      >
                        {f.icon}
                        <span>{f.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Generate Button */}
            <button
              className="cs-generate-btn"
              onClick={handleGenerate}
              disabled={generating || !canGenerate}
            >
              {generating ? <Loader2 size={13} className="cs-spin" /> : <Sparkles size={13} />}
              <span>
                {generating
                  ? 'Generating…'
                  : activeFormat === 'seo'
                    ? 'Generate SEO Meta'
                    : activeFormat === 'ad'
                      ? 'Generate Ad Copy'
                      : activeFormat === 'repurpose'
                        ? 'Repurpose Content'
                        : 'Generate'}
              </span>
            </button>
          </div>
        )}

        {/* ── History Tab ── */}
        {activeFormat === 'history' && (
          <div className="cs-tab-panel">
            {savedItems.length === 0 ? (
              <div className="cs-empty">
                <History size={24} style={{ color: 'rgba(26,28,29,0.15)' }} />
                <span className="cs-empty-text">No saved content yet</span>
                <span className="cs-empty-hint">Generate content and save it to see it here</span>
                <button className="cs-empty-cta" onClick={() => setActiveFormat('blog')}>
                  <Sparkles size={13} />
                  Generate your first post
                </button>
              </div>
            ) : (
              <div className="cs-saved-list">
                {savedItems.map((item) => (
                  <div key={item.id} className="cs-saved-card">
                    <div className="cs-saved-header">
                      <span className="cs-saved-badge" data-format={item.format}>
                        {item.format}
                      </span>
                      <span className="cs-saved-label">{item.label}</span>
                      <span className="cs-saved-date">{new Date(item.createdAt).toLocaleDateString()}</span>
                    </div>
                    {editingId === item.id ? (
                      <div className="cs-saved-edit">
                        <textarea
                          className="cs-textarea"
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          rows={4}
                        />
                        <div className="cs-saved-edit-actions">
                          <button className="cs-btn cs-btn-primary" onClick={() => handleEditSave(item.id)}>
                            <Save size={11} />
                            <span>Save</span>
                          </button>
                          <button
                            className="cs-btn cs-btn-ghost"
                            onClick={() => {
                              setEditingId(null);
                              setEditContent('');
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="cs-saved-content">
                        {item.content.slice(0, 300)}
                        {item.content.length > 300 ? '…' : ''}
                      </div>
                    )}
                    <div className="cs-saved-actions">
                      <CopyButton text={item.content} />
                      <button
                        className="cs-icon-btn"
                        onClick={() => {
                          setEditingId(item.id);
                          setEditContent(item.content);
                        }}
                        title="Edit"
                      >
                        <Edit3 size={12} />
                      </button>
                      <button
                        className="cs-icon-btn cs-icon-danger"
                        onClick={() => handleDelete(item.id)}
                        title="Delete"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Output Area */}
      {output && activeFormat !== 'history' && (
        <FormatPreview
          content={output}
          onSave={() => handleSave(activeFormat, getSaveLabel(), output)}
          showStats={activeFormat === 'blog' || activeFormat === 'product'}
        />
      )}

      {/* Loading */}
      {generating && !output && (
        <div className="cs-loading">
          <Loader2 size={16} className="cs-spin" />
          <span>Generating content with AI…</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="cs-error">
          <AlertCircle size={13} />
          <span>{error}</span>
        </div>
      )}

      <style>{csCss}</style>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────

const csCss = `
.cs-container { display: flex; flex-direction: column; gap: 12px; width: 100%; animation: cs-fade-in 0.25s ease-out both; }
@keyframes cs-fade-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

.cs-header { display: flex; align-items: center; justify-content: space-between; }
.cs-header-left { display: flex; align-items: center; gap: 8px; }
.cs-header-title { font-size: 13px; font-weight: 600; color: #1A1C1D; }
.cs-header-right { display: flex; align-items: center; gap: 6px; }
.cs-header-count { font-size: 10px; color: rgba(26,28,29,0.35); background: rgba(26,28,29,0.04); padding: 2px 8px; border-radius: 10px; }

.cs-controls-row { display: flex; flex-direction: column; gap: 8px; background: rgba(26,28,29,0.02); border-radius: 10px; padding: 10px; border: 1px solid rgba(26,28,29,0.04); }

.cs-voice-grid { display: flex; flex-wrap: wrap; gap: 5px; }
.cs-voice-btn { display: inline-flex; align-items: center; gap: 4px; padding: 5px 10px; border: 1px solid rgba(26,28,29,0.06); border-radius: 8px; background: rgba(255,255,255,0.4); cursor: pointer; font-size: 10px; font-weight: 500; color: rgba(26,28,29,0.55); font-family: inherit; transition: all 0.15s; }
.cs-voice-btn:hover { border-color: rgba(108,74,226,0.2); color: #6C4AE2; background: rgba(108,74,226,0.04); }
.cs-voice-active { border-color: #6C4AE2; color: #6C4AE2; background: rgba(108,74,226,0.08); }

.cs-tone-slider-row { display: flex; align-items: center; gap: 10px; }
.cs-slider-icon { color: rgba(26,28,29,0.35); flex-shrink: 0; }
.cs-range { flex: 1; height: 4px; appearance: none; -webkit-appearance: none; background: rgba(108,74,226,0.15); border-radius: 2px; outline: none; cursor: pointer; }
.cs-range::-webkit-slider-thumb { appearance: none; -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%; background: #6C4AE2; border: 2px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.15); cursor: pointer; }
.cs-range::-moz-range-thumb { width: 14px; height: 14px; border-radius: 50%; background: #6C4AE2; border: 2px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.15); cursor: pointer; }
.cs-tone-label { font-size: 10px; font-weight: 600; color: #6C4AE2; min-width: 90px; text-align: right; }

.cs-tabs { display: flex; gap: 3px; background: rgba(26,28,29,0.03); border-radius: 10px; padding: 3px; flex-wrap: wrap; }
.cs-tab-btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 10px; border: none; border-radius: 7px; background: transparent; cursor: pointer; font-size: 10px; font-weight: 500; color: rgba(26,28,29,0.45); font-family: inherit; transition: all 0.15s; flex-shrink: 0; }
.cs-tab-btn:hover { color: #1A1C1D; background: rgba(255,255,255,0.4); }
.cs-tab-active { color: #6C4AE2; background: rgba(255,255,255,0.7); box-shadow: 0 1px 3px rgba(26,28,29,0.04); }

.cs-body { display: flex; flex-direction: column; gap: 10px; }
.cs-tab-panel { display: flex; flex-direction: column; gap: 12px; }

.cs-field { display: flex; flex-direction: column; gap: 5px; }
.cs-label { font-size: 10px; font-weight: 600; color: rgba(26,28,29,0.5); text-transform: uppercase; letter-spacing: 0.06em; }

.cs-input { width: 100%; padding: 8px 12px; border: 1px solid rgba(26,28,29,0.06); border-radius: 8px; background: rgba(255,255,255,0.5); font-size: 12px; color: #1A1C1D; font-family: inherit; outline: none; transition: border-color 0.15s; box-sizing: border-box; }
.cs-input:focus { border-color: #6C4AE2; }
.cs-input::placeholder { color: rgba(26,28,29,0.25); }

.cs-tone-grid, .cs-platform-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.cs-tone-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border: 1px solid rgba(26,28,29,0.06); border-radius: 8px; background: rgba(255,255,255,0.4); cursor: pointer; font-size: 11px; font-weight: 500; color: rgba(26,28,29,0.55); font-family: inherit; transition: all 0.15s; }
.cs-tone-btn:hover { border-color: rgba(108,74,226,0.2); color: #6C4AE2; background: rgba(108,74,226,0.04); }
.cs-tone-active { border-color: #6C4AE2; color: #6C4AE2; background: rgba(108,74,226,0.08); }

.cs-generate-btn { display: inline-flex; align-items: center; gap: 6px; padding: 9px 18px; border: none; border-radius: 8px; background: #6C4AE2; color: #fff; font-size: 12px; font-weight: 500; cursor: pointer; font-family: inherit; transition: all 0.15s; align-self: flex-start; }
.cs-generate-btn:hover:not(:disabled) { background: #5B3CC8; }
.cs-generate-btn:disabled { opacity: 0.5; cursor: default; }

.cs-loading { display: flex; align-items: center; gap: 8px; padding: 16px; background: rgba(255,255,255,0.5); border-radius: 12px; font-size: 12px; color: rgba(26,28,29,0.55); }
.cs-loading .cs-spin { color: #6C4AE2; }

.cs-error { display: flex; align-items: center; gap: 6px; padding: 8px 10px; background: rgba(185,28,28,0.06); border: 1px solid rgba(185,28,28,0.10); border-radius: 8px; font-size: 11px; color: #B91C1C; }

.cs-spin { animation: cs-rotate 0.8s linear infinite; }
@keyframes cs-rotate { to { transform: rotate(360deg); } }

.cs-output { display: flex; flex-direction: column; gap: 8px; padding: 14px; background: rgba(255,255,255,0.5); border-radius: 12px; border: 1px solid rgba(26,28,29,0.04); }
.cs-output-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px; }
.cs-output-label { font-size: 10px; font-weight: 600; color: rgba(26,28,29,0.5); text-transform: uppercase; letter-spacing: 0.06em; }
.cs-output-actions { display: flex; gap: 4px; align-items: center; flex-wrap: wrap; }
.cs-output-stats { display: flex; gap: 12px; }
.cs-output-text { font-size: 12px; color: #1A1C1D; line-height: 1.6; white-space: pre-wrap; word-break: break-word; margin: 0; font-family: inherit; max-height: 350px; overflow-y: auto; }

.cs-meta { font-size: 10px; color: rgba(26,28,29,0.4); white-space: nowrap; }

.cs-icon-btn { width: 28px; height: 28px; border-radius: 6px; border: none; background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: center; color: rgba(26,28,29,0.3); transition: all 0.15s; flex-shrink: 0; }
.cs-icon-btn:hover { background: rgba(26,28,29,0.04); color: #1A1C1D; }
.cs-icon-danger:hover { color: #B91C1C; background: rgba(185,28,28,0.06); }

.cs-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 32px 16px; }
.cs-empty-text { font-size: 13px; font-weight: 500; color: rgba(26,28,29,0.4); }
.cs-empty-hint { font-size: 11px; color: rgba(26,28,29,0.25); }
.cs-empty-cta { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border: none; border-radius: 8px; background: #6C4AE2; color: #fff; font-size: 12px; font-weight: 500; cursor: pointer; font-family: inherit; transition: all 0.15s; margin-top: 4px; }
.cs-empty-cta:hover { background: #5B3CC8; }

.cs-saved-list { display: flex; flex-direction: column; gap: 8px; }
.cs-saved-card { padding: 12px; background: rgba(255,255,255,0.5); border-radius: 10px; border: 1px solid rgba(26,28,29,0.04); display: flex; flex-direction: column; gap: 8px; }
.cs-saved-header { display: flex; align-items: center; gap: 8px; }
.cs-saved-badge { font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; padding: 2px 6px; border-radius: 4px; }
.cs-saved-badge[data-format="blog"] { color: #6C4AE2; background: rgba(108,74,226,0.08); }
.cs-saved-badge[data-format="social"] { color: #0891B2; background: rgba(8,145,178,0.08); }
.cs-saved-badge[data-format="email"] { color: #059669; background: rgba(5,150,105,0.08); }
.cs-saved-badge[data-format="product"] { color: #D97706; background: rgba(217,119,6,0.08); }
.cs-saved-badge[data-format="press"] { color: #7C3AED; background: rgba(124,58,237,0.08); }
.cs-saved-badge[data-format="seo"] { color: #0284C7; background: rgba(2,132,199,0.08); }
.cs-saved-badge[data-format="ad"] { color: #DC2626; background: rgba(220,38,38,0.08); }
.cs-saved-badge[data-format="landing"] { color: #0891B2; background: rgba(8,145,178,0.08); }
.cs-saved-badge[data-format="repurpose"] { color: #7C3AED; background: rgba(124,58,237,0.08); }
.cs-saved-badge[data-format="history"] { color: rgba(26,28,29,0.4); background: rgba(26,28,29,0.04); }
.cs-saved-label { font-size: 11px; font-weight: 600; color: #1A1C1D; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cs-saved-date { font-size: 9px; color: rgba(26,28,29,0.3); flex-shrink: 0; }
.cs-saved-content { font-size: 11px; color: rgba(26,28,29,0.6); line-height: 1.5; }
.cs-saved-actions { display: flex; gap: 2px; justify-content: flex-end; }
.cs-saved-edit { display: flex; flex-direction: column; gap: 6px; }
.cs-saved-edit-actions { display: flex; gap: 6px; }

.cs-textarea { width: 100%; min-height: 60px; padding: 8px 10px; border: 1px solid rgba(26,28,29,0.06); border-radius: 8px; background: rgba(255,255,255,0.5); font-size: 12px; color: #1A1C1D; font-family: inherit; resize: vertical; outline: none; transition: border-color 0.15s; box-sizing: border-box; }
.cs-textarea:focus { border-color: #6C4AE2; }

.cs-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 6px; border: 1px solid transparent; font-size: 11px; font-weight: 500; cursor: pointer; font-family: inherit; transition: all 0.15s; }
.cs-btn-primary { background: #6C4AE2; color: #fff; }
.cs-btn-primary:hover { background: #5B3CC8; }
.cs-btn-ghost { background: transparent; color: rgba(26,28,29,0.45); border-color: transparent; }
.cs-btn-ghost:hover { color: #1A1C1D; background: rgba(26,28,29,0.04); }

.cs-char-count { display: flex; align-items: center; gap: 8px; }
.cs-char-bar-track { flex: 1; height: 4px; background: rgba(26,28,29,0.06); border-radius: 2px; overflow: hidden; }
.cs-char-bar-fill { height: 100%; border-radius: 2px; transition: width 0.2s, background 0.2s; }
.cs-char-text { font-size: 10px; font-weight: 600; min-width: 70px; text-align: right; }
`;