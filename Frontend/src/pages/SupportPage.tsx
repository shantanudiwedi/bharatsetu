import { useState, useRef, useEffect } from 'react';
import { submitSupportTicket } from '@/services/api';
import { HelpCircle, Send, CheckCircle2, AlertCircle, MessageSquare, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'ai';
  content: string;
}

export default function SupportPage({ currentUser }: { currentUser?: any }) {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  // Chatbot State
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: 'Hello! I am the BharatSetu Bidder Support AI. How can I assist you with your compliance and documents today?' }
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
      setMessages(prev => [...prev, { role: 'ai', content: 'Sorry, I am currently unable to reach the support server. Please try again later.' }]);
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
      <div className="max-w-4xl mx-auto flex flex-col h-[80vh] bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center gap-3">
          <div className="bg-navy-600 p-2 rounded-lg relative">
            <Bot className="w-5 h-5 text-white" />
            <span className="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm border border-white">MOCK</span>
          </div>
          <div>
            <h2 className="font-bold text-slate-800 flex items-center gap-2">
              Compliance Assistant 
              <span className="text-[10px] font-semibold bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded uppercase">[MOCK AI]</span>
            </h2>
            <p className="text-xs text-slate-500">Ask about your documents, bid status, and verification.</p>
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
          {["What documents am I missing?", "What is my compliance status?", "Why is my bid flagged?", "Do I have any alerts?"].map((q) => (
            <button
              key={q}
              onClick={() => handleChatSubmit(q)}
              disabled={isChatLoading}
              className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 px-3 py-1.5 rounded-full transition-colors"
            >
              {q}
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
              placeholder="Type your question..."
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
    );
  }

  return (
    <div className="max-w-5xl mx-auto flex flex-col lg:flex-row gap-8">
      {/* FAQs Section */}
      <div className="flex-1 space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2 mb-1">
            <HelpCircle className="w-6 h-6 text-navy-600" />
            Help & Support
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
