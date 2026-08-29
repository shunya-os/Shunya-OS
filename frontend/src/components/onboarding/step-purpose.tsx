/**
 * StepPurpose — "What would you like SHUNYA to start understanding?"
 *
 * Replaces the old Organization/AI/First-Object steps.
 * Provides meaningful choices that make the purpose of the workspace clear.
 * The user never creates a meaningless "object" — they tell SHUNYA what matters.
 */
import { useState, useCallback } from 'react';
import { api } from '../../api/client';
import { SessionManager } from '../../api/session';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: (result: { action: string; detail?: string }) => void;
  onBack: () => void;
  onSkip: () => void;
}

type ChoiceId = 'upload' | 'describe' | 'working_on' | 'create_org' | 'connect_org' | 'empty';

interface Choice {
  id: ChoiceId;
  icon: string;
  title: string;
  description: string;
}

const CHOICES: Choice[] = [
  { id: 'upload', icon: '📤', title: 'Upload What I Already Have', description: 'Share documents, spreadsheets, or files — SHUNYA will read and organize them.' },
  { id: 'describe', icon: '✍️', title: 'Describe What I Do', description: 'Tell SHUNYA about your work, projects, or business in your own words.' },
  { id: 'working_on', icon: '🔨', title: 'Add Something I\'m Working On', description: 'A project, a trip, a plan — anything you want SHUNYA to help track.' },
  { id: 'create_org', icon: '🏢', title: 'Create an Organization', description: 'Set up a shared workspace for your company or team.' },
  { id: 'connect_org', icon: '🔗', title: 'Connect to an Organization', description: 'Join an existing organization via invitation or code.' },
  { id: 'empty', icon: '🌱', title: 'Start with an Empty Workspace', description: 'Begin fresh and add things later as you go.' },
];

export function StepPurpose({ onNext, onBack, onSkip }: Props) {
  const [phase, setPhase] = useState<'choice' | 'upload' | 'describe' | 'working_on' | 'create_org'>('choice');
  const [input, setInput] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [businessType, setBusinessType] = useState('Technology');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChoice = useCallback((id: ChoiceId) => {
    if (id === 'upload') setPhase('upload');
    else if (id === 'describe') setPhase('describe');
    else if (id === 'working_on') setPhase('working_on');
    else if (id === 'create_org') setPhase('create_org');
    else if (id === 'connect_org') {
      onNext({ action: 'connect_org' });
    } else if (id === 'empty') {
      onNext({ action: 'empty' });
    }
  }, [onNext]);

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      if (phase === 'upload' && file) {
        const formData = new FormData();
        formData.append('file', file);
        const resp = await fetch('/api/v1/founder/ingest', {
          method: 'POST', credentials: 'include', body: formData,
        });
        const result = await resp.json();
        if (result.success) {
          onNext({ action: 'upload', detail: result.summary || file.name });
        } else {
          setError(result.error || 'Upload failed');
          setLoading(false);
          return;
        }
      } else if (phase === 'describe' && input.trim()) {
        // Store as a personal note
        const resp = await api.createObject(input.trim(), 'note');
        if (resp.success) {
          onNext({ action: 'describe', detail: input.trim().substring(0, 60) });
        } else {
          setError('Could not save your description');
          setLoading(false);
          return;
        }
      } else if (phase === 'working_on' && input.trim()) {
        const resp = await api.createObject(input.trim(), 'commitment');
        if (resp.success) {
          onNext({ action: 'working_on', detail: input.trim().substring(0, 60) });
        } else {
          setError('Could not save your item');
          setLoading(false);
          return;
        }
      } else if (phase === 'create_org' && companyName.trim()) {
        const resp = await api.createOrg(companyName.trim(), businessType);
        if (resp.success && resp.org_id) {
          const session = SessionManager.load();
          if (session) {
            session.orgId = resp.org_id;
            session.orgName = resp.org_name || companyName.trim();
            SessionManager.save(session);
          }
          onNext({ action: 'create_org', detail: companyName.trim() });
        } else {
          setError(resp.error ?? 'Failed to create organization');
          setLoading(false);
          return;
        }
      } else {
        onNext({ action: 'empty' });
      }
    } catch {
      setError('Something went wrong. Please try again.');
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (phase !== 'choice') {
      setPhase('choice');
    } else {
      onBack();
    }
  };

  // ── Choice Selection Screen ──
  if (phase === 'choice') {
    return (
      <div className="sh-onboarding">
        <div className="sh-onboarding-content">
          <div className="sh-onboarding-card sh-onb-fade-in">
            <div className="sh-onboarding-title">What Would You Like SHUNYA to Start Understanding?</div>
            <div className="sh-onboarding-subtitle">
              This is <strong>your personal workspace</strong>. Tell SHUNYA what matters to you.
            </div>

            <div className="sh-purpose-choices">
              {CHOICES.map(choice => (
                <button
                  key={choice.id}
                  className="sh-purpose-choice"
                  onClick={() => handleChoice(choice.id)}
                  tabIndex={0}
                >
                  <span className="sh-purpose-choice-icon">{choice.icon}</span>
                  <div className="sh-purpose-choice-text">
                    <span className="sh-purpose-choice-title">{choice.title}</span>
                    <span className="sh-purpose-choice-desc">{choice.description}</span>
                  </div>
                </button>
              ))}
            </div>

            <button
              className="sh-onboarding-btn-secondary"
              onClick={onSkip}
              tabIndex={0}
            >
              Skip for now — I'll add things later
            </button>
          </div>
        </div>
        <style>{onboardingStyles}</style>
      </div>
    );
  }

  // ── Upload Screen ──
  if (phase === 'upload') {
    return (
      <div className="sh-onboarding" onKeyDown={e => e.key === 'Escape' && handleBack()}>
        <div className="sh-onboarding-content">
          <div className="sh-onboarding-card sh-onb-fade-in">
            <div className="sh-onboarding-title">Upload to Your Personal Workspace</div>
            <div className="sh-onboarding-subtitle">
              SHUNYA will read your file and organize it into your personal workspace.
            </div>

            <div className="sh-onboarding-form">
              <div className="sh-onboarding-field">
                <label>Choose a file</label>
                <input
                  type="file"
                  accept=".pdf,.xlsx,.csv,.txt,.docx,.md,.json"
                  onChange={e => setFile(e.target.files?.[0] || null)}
                  tabIndex={0}
                />
                {file && <div className="sh-onboarding-desc">Selected: {file.name}</div>}
              </div>

              {error && <div className="sh-onboarding-error" role="alert">{error}</div>}

              <button
                className="sh-onboarding-btn"
                onClick={handleSubmit}
                disabled={loading || !file}
                tabIndex={0}
              >
                {loading ? <><span className="sh-onboarding-spinner" />Uploading…</> : 'Upload &amp; Analyze'}
              </button>
            </div>

            <button className="sh-onboarding-btn-secondary" onClick={handleBack} disabled={loading} tabIndex={0}>
              Back
            </button>
          </div>
        </div>
        <style>{onboardingStyles}</style>
      </div>
    );
  }

  // ── Describe Screen ──
  if (phase === 'describe') {
    return (
      <div className="sh-onboarding" onKeyDown={e => e.key === 'Escape' && handleBack()}>
        <div className="sh-onboarding-content">
          <div className="sh-onboarding-card sh-onb-fade-in">
            <div className="sh-onboarding-title">Tell SHUNYA About Your Work</div>
            <div className="sh-onboarding-subtitle">
              Describe what you do, your projects, or your business. SHUNYA will save this as a starting point.
            </div>

            <div className="sh-onboarding-form">
              <div className="sh-onboarding-field">
                <label htmlFor="describe-input">What should SHUNYA know about you?</label>
                <textarea
                  id="describe-input"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder="I run a travel company organizing trips to Bali...&#10;I'm planning a family vacation...&#10;I'm working on a new product launch..."
                  rows={4}
                  autoFocus
                  tabIndex={0}
                />
              </div>

              {error && <div className="sh-onboarding-error" role="alert">{error}</div>}

              <button
                className="sh-onboarding-btn"
                onClick={handleSubmit}
                disabled={loading || !input.trim()}
                tabIndex={0}
              >
                {loading ? <><span className="sh-onboarding-spinner" />Saving…</> : 'Save to My Workspace'}
              </button>
            </div>

            <button className="sh-onboarding-btn-secondary" onClick={handleBack} disabled={loading} tabIndex={0}>
              Back
            </button>
          </div>
        </div>
        <style>{onboardingStyles}</style>
      </div>
    );
  }

  // ── Working On Screen ──
  if (phase === 'working_on') {
    return (
      <div className="sh-onboarding" onKeyDown={e => e.key === 'Escape' && handleBack()}>
        <div className="sh-onboarding-content">
          <div className="sh-onboarding-card sh-onb-fade-in">
            <div className="sh-onboarding-title">Add Something You're Working On</div>
            <div className="sh-onboarding-subtitle">
              A project, a trip, a plan — SHUNYA will track this as a commitment in your personal workspace.
            </div>

            <div className="sh-onboarding-form">
              <div className="sh-onboarding-field">
                <label htmlFor="working-input">What are you working on?</label>
                <input
                  id="working-input"
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder="e.g., Planning a trip to Bali, New product launch, Q4 budget review"
                  autoFocus
                  tabIndex={0}
                />
              </div>

              {error && <div className="sh-onboarding-error" role="alert">{error}</div>}

              <button
                className="sh-onboarding-btn"
                onClick={handleSubmit}
                disabled={loading || !input.trim()}
                tabIndex={0}
              >
                {loading ? <><span className="sh-onboarding-spinner" />Saving…</> : 'Add to My Workspace'}
              </button>
            </div>

            <button className="sh-onboarding-btn-secondary" onClick={handleBack} disabled={loading} tabIndex={0}>
              Back
            </button>
          </div>
        </div>
        <style>{onboardingStyles}</style>
      </div>
    );
  }

  // ── Create Organization Screen ──
  if (phase === 'create_org') {
    return (
      <div className="sh-onboarding" onKeyDown={e => e.key === 'Escape' && handleBack()}>
        <div className="sh-onboarding-content">
          <div className="sh-onboarding-card sh-onb-fade-in">
            <div className="sh-onboarding-title">Create Your Organization</div>
            <div className="sh-onboarding-subtitle">
              This will create a shared workspace — separate from your personal SHUNYA. You'll be the owner.
            </div>

            <div className="sh-onboarding-form">
              <div className="sh-onboarding-field">
                <label htmlFor="org-name">Organization Name</label>
                <input
                  id="org-name"
                  type="text"
                  value={companyName}
                  onChange={e => setCompanyName(e.target.value)}
                  placeholder="e.g., Panchi Club"
                  autoFocus
                  tabIndex={0}
                />
              </div>

              <div className="sh-onboarding-field">
                <label htmlFor="org-type">Type</label>
                <select
                  id="org-type"
                  value={businessType}
                  onChange={e => setBusinessType(e.target.value)}
                  tabIndex={0}
                >
                  {['Technology', 'Consulting', 'Healthcare', 'Finance', 'Travel', 'Real Estate', 'Education', 'Other'].map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {error && <div className="sh-onboarding-error" role="alert">{error}</div>}

              <button
                className="sh-onboarding-btn"
                onClick={handleSubmit}
                disabled={loading || !companyName.trim()}
                tabIndex={0}
              >
                {loading ? <><span className="sh-onboarding-spinner" />Creating…</> : 'Create Organization'}
              </button>
            </div>

            <button className="sh-onboarding-btn-secondary" onClick={handleBack} disabled={loading} tabIndex={0}>
              Back
            </button>
          </div>
        </div>
        <style>{onboardingStyles}</style>
      </div>
    );
  }

  return null;
}