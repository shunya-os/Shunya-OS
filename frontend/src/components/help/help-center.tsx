/**
 * Help Center — help panel with common task links, FAQ, contact.
 */
import { useState } from 'react';
import { IconHelp, IconChevronDown, IconChevronRight, IconExternalLink, IconMail, IconBook, IconSearch, IconUsers, IconSettings } from '@tabler/icons-react';

interface FaqItem {
  q: string;
  a: string;
}

const HELP_LINKS = [
  { label: 'Getting Started Guide', icon: <IconBook size={14} />, href: '#' },
  { label: 'Search & Find Data', icon: <IconSearch size={14} />, href: '#' },
  { label: 'Managing Relationships', icon: <IconUsers size={14} />, href: '#' },
  { label: 'Workspace Settings', icon: <IconSettings size={14} />, href: '#' },
  { label: 'Keyboard Shortcuts', icon: <IconHelp size={14} />, href: '#' },
];

const FAQS: FaqItem[] = [
  { q: 'How do I create a new object?', a: 'Press Ctrl+N or use the command palette (Ctrl+K) and type "create". You can also navigate to any domain workspace and use the "New" button.' },
  { q: 'How do I search across everything?', a: 'Use the universal search bar at the bottom (Ctrl+K → type your query) or press Ctrl+F in any workspace view for in-page search.' },
  { q: 'How does SHUNYA determine what to recommend?', a: 'SHUNYA monitors your organization through events, signals, and observations. It prioritizes based on urgency (time-sensitive items first), then relevance, then novelty.' },
  { q: 'Can I delete data permanently?', a: 'Yes. Open the object you want to remove, click the menu (⋮) and select "Delete". Deletion is permanent and cannot be undone.' },
  { q: 'How do I export my data?', a: 'Visit the Import/Export panel from the sidebar. You can export objects, relationships, and reports as CSV or JSON.' },
  { q: 'What is the difference between a workspace and an object?', a: 'A workspace is a focused surface for working with a domain (e.g., People, Finance). An object is an individual entity within that domain (e.g., a specific contact, invoice).' },
];

export function HelpCenter() {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  return (
    <div className="hc-container">
      <div className="hc-header">
        <div className="hc-header-icon"><IconHelp size={22} /></div>
        <div>
          <h2 className="hc-title">Help Center</h2>
          <p className="hc-subtitle">Guides, FAQs, and how to get support</p>
        </div>
      </div>

      {/* Quick Links */}
      <div className="hc-section">
        <h3 className="hc-section-title">Quick Links</h3>
        <div className="hc-links">
          {HELP_LINKS.map((link, i) => (
            <a key={i} className="hc-link" href={link.href}>
              <span className="hc-link-icon">{link.icon}</span>
              <span className="hc-link-label">{link.label}</span>
              <IconExternalLink size={12} className="hc-link-ext" />
            </a>
          ))}
        </div>
      </div>

      {/* FAQ */}
      <div className="hc-section">
        <h3 className="hc-section-title">Frequently Asked Questions</h3>
        <div className="hc-faqs">
          {FAQS.map((faq, i) => (
            <div key={i} className="hc-faq">
              <button
                className="hc-faq-q"
                onClick={() => setExpandedFaq(expandedFaq === i ? null : i)}
              >
                <span className="hc-faq-icon">
                  {expandedFaq === i ? <IconChevronDown size={12} /> : <IconChevronRight size={12} />}
                </span>
                <span className="hc-faq-text">{faq.q}</span>
              </button>
              {expandedFaq === i && (
                <div className="hc-faq-a">
                  <p>{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Contact */}
      <div className="hc-section">
        <h3 className="hc-section-title">Need More Help?</h3>
        <div className="hc-contact">
          <div className="hc-contact-item">
            <IconMail size={14} />
            <span>Email support at <strong>support@shunyaos.com</strong></span>
          </div>
          <p className="hc-contact-note">
            We typically respond within 24 hours during business days.
          </p>
        </div>
      </div>

      <style>{hcCss}</style>
    </div>
  );
}

const hcCss = `
.hc-container { display: flex; flex-direction: column; gap: 20px; padding: 32px; max-width: 640px; }
.hc-header { display: flex; align-items: center; gap: 12px; }
.hc-header-icon { width: 40px; height: 40px; border-radius: 12px; background: rgba(164,134,95,0.10); color: #A4865F; display: flex; align-items: center; justify-content: center; }
.hc-title { font-size: 18px; font-weight: 600; color: #1A1C1D; margin: 0; }
.hc-subtitle { font-size: 12px; color: rgba(26,28,29,0.45); margin: 2px 0 0; }
.hc-section { }
.hc-section-title { font-size: 11px; font-weight: 600; color: rgba(26,28,29,0.5); text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 10px; }
.hc-links { display: flex; flex-direction: column; gap: 4px; }
.hc-link { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: rgba(255,255,255,0.6); border: 1px solid rgba(26,28,29,0.06); border-radius: 8px; text-decoration: none; color: #1A1C1D; font-size: 13px; transition: all 0.15s; }
.hc-link:hover { border-color: #A4865F; background: rgba(255,255,255,0.8); }
.hc-link-icon { color: rgba(26,28,29,0.4); }
.hc-link-label { flex: 1; }
.hc-link-ext { color: rgba(26,28,29,0.3); }

.hc-faqs { background: rgba(255,255,255,0.6); border: 1px solid rgba(26,28,29,0.06); border-radius: 10px; overflow: hidden; }
.hc-faq { border-bottom: 1px solid rgba(26,28,29,0.03); }
.hc-faq:last-child { border-bottom: none; }
.hc-faq-q { display: flex; align-items: center; gap: 8px; width: 100%; padding: 12px 14px; border: none; background: transparent; cursor: pointer; text-align: left; font-family: inherit; font-size: 13px; color: #1A1C1D; transition: background 0.15s; }
.hc-faq-q:hover { background: rgba(26,28,29,0.02); }
.hc-faq-icon { font-size: 10px; color: rgba(26,28,29,0.3); flex-shrink: 0; width: 12px; text-align: center; }
.hc-faq-text { flex: 1; }
.hc-faq-a { padding: 0 14px 14px 34px; }
.hc-faq-a p { font-size: 13px; color: rgba(26,28,29,0.6); margin: 0; line-height: 1.6; }

.hc-contact { background: rgba(255,255,255,0.6); border: 1px solid rgba(26,28,29,0.06); border-radius: 10px; padding: 16px; }
.hc-contact-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #1A1C1D; margin-bottom: 8px; }
.hc-contact-note { font-size: 12px; color: rgba(26,28,29,0.45); margin: 0; }

@media (max-width: 480px) {
  .hc-container { padding: 20px; }
}
`;