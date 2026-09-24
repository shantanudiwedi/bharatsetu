import { useState, useRef, useEffect } from 'react';
import { submitSupportTicket } from '@/services/api';
import { HelpCircle, Send, CheckCircle2, AlertCircle, MessageSquare, Bot, ClipboardList, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useTranslation, type TranslationKey } from '@/i18n';

interface Message {
  role: 'user' | 'ai';
  content: string;
}

function SurveyPanel() {
  const { t } = useTranslation();
  const surveyQuestionKeys: TranslationKey[] = Array.from({ length: 10 }, (_, index) => `surveyQuestion${index + 1}` as TranslationKey);
  const surveyUrl = import.meta.env.VITE_SURVEY_URL?.trim();
  const [surveyMessage, setSurveyMessage] = useState('');

  const openSurvey = () => {
    if (!surveyUrl) {
      setSurveyMessage(t('surveySoon'));
      return;
    }
    try {
      const parsedUrl = new URL(surveyUrl);
      if (parsedUrl.protocol !== 'https:' && parsedUrl.protocol !== 'http:') {
        throw new Error('Unsupported survey URL protocol');
      }
      window.open(parsedUrl.toString(), '_blank', 'noopener,noreferrer');
    } catch {
      setSurveyMessage(t('surveySoon'));
    }
  };

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center shrink-0">
          <ClipboardList className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <h3 className="font-bold text-slate-800">{t('userFeedback')}</h3>
          <p className="text-sm text-slate-600 mt-1">
            {t('surveyIntro')}
          </p>
          <button
            type="button"
            onClick={openSurvey}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-navy-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-navy-800"
          >
            {t('takeSurvey')}
            {surveyUrl && <ExternalLink className="w-4 h-4" />}
          </button>
          {surveyMessage && (
            <p role="status" className="mt-3 text-sm font-medium text-amber-700">{surveyMessage}</p>
          )}
        </div>
      </div>

      <details className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-3">
        <summary className="cursor-pointer text-sm font-semibold text-slate-700">{t('surveyQuestionsTitle')}</summary>
        <div className="mt-3 space-y-3 text-xs text-slate-600">
          <p><strong>{t('surveyRole')}:</strong> {t('surveyRoleOptions')}</p>
          <ol className="list-decimal pl-5 space-y-1.5">
            {surveyQuestionKeys.map((key) => <li key={key}>{t(key)}</li>)}
          </ol>
        </div>
      </details>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 p-4">
          <h4 className="font-semibold text-slate-800">{t('whyBharatSetu')}</h4>
          <p className="mt-2 text-xs leading-relaxed text-slate-600">
            {t('whyDescription')}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 p-4">
          <h4 className="font-semibold text-slate-800">{t('feedbackInfluence')}</h4>
          <p className="mt-2 text-xs text-slate-500">{t('realResultsSoon')}</p>
          <ul className="mt-2 space-y-1 text-xs text-slate-700">
            {[
              t('featureSimpleWorkflow'),
              t('featureMultilingual'),
              t('featureClearStatus'),
              t('featureExplainable'),
              t('featureSelfCheck'),
              t('featureHumanDecision')
            ].map((feature) => (
              <li key={feature}>✓ {feature}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

export default function SupportPage({ currentUser }: { currentUser?: any }) {
  const { t } = useTranslation();
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  // Chatbot State
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: t('supportGreeting') }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleChatSubmit = async (text: string) => {
    if (!text.trim()) return;
    
    const newMsg: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, newMsg]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const { api } = await import('@/services/api');
      const res = await api.post('/support/chat', { query: text });
      setMessages(prev => [...prev, { role: 'ai', content: res.data.reply }]);
    } catch (error: any) {
      console.error("Chat API Error:", error?.response?.data || error);
      setMessages(prev => [...prev, { role: 'ai', content: t('supportUnavailable') }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) return;
    
    setStatus('loading');
    try {
      await submitSupportTicket(subject, description);
      setStatus('success');
      setSubject('');
      setDescription('');
    } catch (error) {
      setStatus('error');
    }
  };

  if (currentUser?.role === 'BIDDER') {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex flex-col h-[80vh] bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Chat Header */}
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center gap-3">
            <div className="bg-navy-600 p-2 rounded-lg relative">
              <Bot className="w-5 h-5 text-white" />
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm border border-white">MOCK</span>
            </div>
            <div>
              <h2 className="font-bold text-slate-800 flex items-center gap-2">
                {t('help')} · {t('complianceAssistant')}
                <span className="text-[10px] font-semibold bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded uppercase">[MOCK AI]</span>
              </h2>
              <p className="text-xs text-slate-500">{t('askDocumentsBidStatus')}</p>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl p-3 text-sm ${
                msg.role === 'user' 
                  ? 'bg-navy-600 text-white rounded-tr-none' 
                  : 'bg-white border border-slate-200 text-slate-700 rounded-tl-none shadow-sm'
              }`}>
                {msg.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm max-w-none text-slate-700 leading-relaxed [&_p]:mb-2 [&_p:last-child]:mb-0 [&_ul]:list-disc [&_ul]:pl-4 [&_ul]:my-1.5 [&_li]:my-0.5 [&_h1]:text-base [&_h1]:font-bold [&_h2]:text-sm [&_h2]:font-bold [&_h3]:text-xs [&_h3]:font-semibold [&_strong]:font-semibold [&_strong]:text-slate-900">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                )}
              </div>
            </div>
          ))}
          {isChatLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 text-slate-400 rounded-2xl rounded-tl-none p-3 shadow-sm flex items-center gap-2">
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce delay-75"></span>
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce delay-150"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

          {/* Suggested Prompts */}
          <div className="px-4 py-3 bg-white border-t border-slate-100 flex flex-wrap gap-2">
          {[
            [t('quickDocumentsNeeded'), 'What documents do I need?'],
            [t('quickMissingDocument'), 'Which document is missing?'],
            [t('quickFlaggedDocument'), 'Why was this document flagged?'],
            [t('quickFixIssue'), 'How do I fix this issue?']
          ].map(([label, query]) => (
            <button
              key={label}
              onClick={() => handleChatSubmit(query)}
              disabled={isChatLoading}
              className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 px-3 py-1.5 rounded-full transition-colors"
            >
              {label}
            </button>
          ))}
          </div>

          {/* Chat Input */}
          <div className="p-4 bg-white border-t border-slate-200">
          <form 
            onSubmit={(e) => { e.preventDefault(); handleChatSubmit(chatInput); }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={t('typeQuestion')}
              className="flex-1 px-4 py-2 bg-slate-50 border border-slate-200 rounded-full focus:outline-none focus:ring-2 focus:ring-navy-400 text-sm"
              disabled={isChatLoading}
            />
            <button
              type="submit"
              disabled={isChatLoading || !chatInput.trim()}
              className="p-2 bg-navy-600 text-white rounded-full hover:bg-navy-700 disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          </div>
        </div>
        <SurveyPanel />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto flex flex-col lg:flex-row gap-8">
      {/* FAQs Section */}
      <div className="flex-1 space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2 mb-1">
            <HelpCircle className="w-6 h-6 text-navy-600" />
            {t('helpSupport')}
          </h2>
          <p className="text-slate-500 text-sm">Frequently asked questions and system guidance.</p>
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="font-semibold text-slate-800 mb-2">How does the Risk Engine work?</h3>
            <p className="text-sm text-slate-600">The Verification Engine automatically cross-checks vendor documents against simulated government databases (GST, PAN, Udyam, etc.). The Risk Score is calculated based on discrepancies found during these checks. A score above 70 is flagged as High Risk.</p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="font-semibold text-slate-800 mb-2">What happens when a bid is Escalated?</h3>
            <p className="text-sm text-slate-600">When an L1 or L2 officer escalates a bid, it is flagged for senior review. It will appear in the Flagged cases queue until an L3 officer or administrator makes a final Approval or Rejection decision.</p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="font-semibold text-slate-800 mb-2">What does the system verify?</h3>
            <p className="text-sm text-slate-600">This module records and reviews each document, tender requirement, and vendor verification step as part of the procurement compliance pipeline.</p>
          </div>
          
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="font-semibold text-slate-800 mb-2">Document Upload Guidelines</h3>
            <p className="text-sm text-slate-600">Supported formats are PDF, PNG, and JPG. The system automatically detects duplicates using SHA-256 hashing to prevent redundant verifications.</p>
          </div>
        </div>
        <SurveyPanel />
      </div>

      {/* Contact Form Section */}
      <div className="lg:w-[400px]">
        <div className="bg-white rounded-xl border border-slate-200 p-6 sticky top-24">
          <h3 className="font-bold text-slate-800 mb-1">Contact Support</h3>
          <p className="text-xs text-slate-500 mb-6">Submit an internal ticket for technical assistance.</p>
          
          {status === 'success' ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex flex-col items-center justify-center text-center py-8">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mb-3" />
              <h4 className="font-bold text-emerald-800 mb-1">Request Submitted</h4>
              <p className="text-sm text-emerald-600">Your support ticket has been created successfully. Our team will review it shortly.</p>
              <button 
                onClick={() => setStatus('idle')}
                className="mt-6 px-4 py-2 bg-white border border-emerald-200 text-emerald-700 rounded-lg text-sm font-medium hover:bg-emerald-50 transition-colors"
              >
                Submit another ticket
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {status === 'error' && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2 text-red-700 text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <p>Failed to submit support request. Please try again.</p>
                </div>
              )}
              
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">Subject</label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="E.g. Issue with risk calculation"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-navy-400 focus:bg-white transition-all text-sm"
                  disabled={status === 'loading'}
                />
              </div>
              
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">Description</label>
                <textarea
                  required
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Please describe your issue in detail..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-navy-400 focus:bg-white transition-all text-sm resize-none"
                  disabled={status === 'loading'}
                />
              </div>
              
              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-navy-600 hover:bg-navy-700 text-white font-medium rounded-lg transition-colors shadow-sm disabled:opacity-70"
              >
                {status === 'loading' ? (
                  <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Submit Request
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
