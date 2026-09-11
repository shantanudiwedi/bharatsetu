import { useState } from 'react';
import {
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  CheckCircle2,
  XCircle,
  Clock3,
  FileText,
  Sparkles,
  UserCog,
  Link2,
  ArrowUpRight,
  ThumbsUp,
  ThumbsDown,
  Flag,
} from 'lucide-react';
import type { VerificationRecord, DocStatus, RiskLevel, VerificationStatus } from '@/data/records';

const riskConfig: Record<RiskLevel, { label: string; cls: string; icon: typeof ShieldCheck }> = {
  low: { label: 'Low Risk', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: ShieldCheck },
  medium: { label: 'Medium Risk', cls: 'bg-amber-50 text-amber-700 border-amber-200', icon: ShieldAlert },
  high: { label: 'High Risk', cls: 'bg-red-50 text-red-700 border-red-200', icon: ShieldX },
};

const statusConfig: Record<VerificationStatus, { label: string; cls: string; dot: string }> = {
  pending_review: { label: 'Pending Review', cls: 'bg-navy-50 text-navy-700', dot: 'bg-navy-500' },
  approved: { label: 'Approved', cls: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
  rejected: { label: 'Rejected', cls: 'bg-red-50 text-red-700', dot: 'bg-red-500' },
  flagged: { label: 'Flagged', cls: 'bg-amber-50 text-amber-700', dot: 'bg-amber-500' },
};

const docStatusConfig: Record<DocStatus, { icon: typeof CheckCircle2; color: string; label: string }> = {
  verified: { icon: CheckCircle2, color: 'text-emerald-500', label: 'Verified' },
  failed: { icon: XCircle, color: 'text-red-500', label: 'Failed' },
  pending: { icon: Clock3, color: 'text-amber-500', label: 'Pending' },
};

const auditStatusConfig: Record<string, { color: string; icon: typeof CheckCircle2 }> = {
  pass: { color: 'text-emerald-500', icon: CheckCircle2 },
  fail: { color: 'text-red-500', icon: XCircle },
  checking: { color: 'text-amber-500', icon: Clock3 },
};

export default function VerificationTable() {
  const [expandedId, setExpandedId] = useState<string | null>('GEM-2026-04827');

  const toggle = (id: string) => setExpandedId((prev) => (prev === id ? null : id));

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Table header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
        <div>
          <h3 className="text-base font-bold text-slate-800">Verification Queue</h3>
          <p className="text-[12px] text-slate-400 mt-0.5">
            AI-assisted review · Officer makes final decision on every bid
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1.5 text-[13px] font-medium text-slate-600 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors">
            All Status
          </button>
          <button className="px-3 py-1.5 text-[13px] font-medium text-white bg-navy-700 rounded-lg hover:bg-navy-800 transition-colors">
            Export
          </button>
        </div>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[40px_1.5fr_1fr_1fr_1fr_120px_40px] gap-3 px-6 py-3 bg-slate-50 border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        <div></div>
        <div>Vendor</div>
        <div>Category</div>
        <div>Bid Amount</div>
        <div>Documents</div>
        <div>Risk</div>
        <div></div>
      </div>

      {/* Rows */}
      <div className="divide-y divide-slate-100">
        {records.map((rec) => {
          const isOpen = expandedId === rec.id;
          const risk = riskConfig[rec.riskLevel];
          const status = statusConfig[rec.status];

          return (
            <div key={rec.id}>
              {/* Summary row */}
              <button
                onClick={() => toggle(rec.id)}
                className={`w-full grid grid-cols-[40px_1.5fr_1fr_1fr_1fr_120px_40px] gap-3 px-6 py-4 items-center text-left transition-colors ${
                  isOpen ? 'bg-navy-50/50' : 'hover:bg-slate-50'
                }`}
              >
                {/* Status dot + expand */}
                <div className="flex items-center justify-center">
                  <span className={`w-2.5 h-2.5 rounded-full ${status.dot} shrink-0`}></span>
                </div>

                {/* Vendor */}
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-800 truncate">{rec.vendorName}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[11px] text-slate-400 font-mono">{rec.id}</span>
                    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${status.cls}`}>
                      {status.label}
                    </span>
                  </div>
                </div>

                {/* Category */}
                <div className="text-sm text-slate-600 truncate">{rec.category}</div>

                {/* Bid */}
                <div className="text-sm font-semibold text-slate-700">{rec.bidAmount}</div>

                {/* Doc status grid */}
                <div className="flex items-center gap-1.5">
                  {rec.documents.map((doc) => {
                    const dc = docStatusConfig[doc.status];
                    return (
                      <div
                        key={doc.name}
                        title={`${doc.name}: ${dc.label} — ${doc.detail}`}
                        className={`flex items-center gap-1 px-1.5 py-1 rounded-md border text-[10px] font-semibold ${
                          doc.status === 'verified'
                            ? 'bg-emerald-50 border-emerald-200 text-emerald-600'
                            : doc.status === 'failed'
                              ? 'bg-red-50 border-red-200 text-red-600'
                              : 'bg-amber-50 border-amber-200 text-amber-600'
                        }`}
                      >
                        <dc.icon className="w-3 h-3" strokeWidth={2.5} />
                        <span>{doc.name}</span>
                      </div>
                    );
                  })}
                </div>

                {/* Risk pill */}
                <div>
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-semibold ${risk.cls}`}
                  >
                    <risk.icon className="w-3 h-3" strokeWidth={2.5} />
                    {risk.label}
                  </span>
                </div>

                {/* Chevron */}
                <div className="flex justify-center">
                  <ChevronRight
                    className={`w-5 h-5 text-slate-400 transition-transform duration-200 ${
                      isOpen ? 'rotate-90' : ''
                    }`}
                  />
                </div>
              </button>

              {/* Expanded detail */}
              {isOpen && (
                <div className="px-6 pb-6 bg-navy-50/30 animate-fade-in">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 pt-2">
                    {/* Left: Document details */}
                    <div className="lg:col-span-2 space-y-5">
                      {/* AI Recommendation */}
                      <div className="bg-white rounded-xl border border-slate-200 p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-navy-500 to-navy-700 flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white" />
                          </div>
                          <h4 className="text-sm font-bold text-slate-800">AI Recommendation</h4>
                          <span className="ml-auto text-[11px] font-semibold text-navy-600 bg-navy-50 px-2 py-0.5 rounded">
                            {rec.aiConfidence}% confidence
                          </span>
                        </div>
                        <p className="text-[13px] text-slate-600 leading-relaxed mb-3">
                          {rec.aiRecommendation}
                        </p>
                        <p className="text-[12px] text-slate-400 leading-relaxed">{rec.aiSummary}</p>

                        {/* Human oversight banner */}
                        <div className="mt-4 flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5">
                          <UserCog className="w-4 h-4 text-amber-600 shrink-0" />
                          <p className="text-[12px] text-amber-700 font-medium">
                            Officer decides. AI does not auto-approve or reject.
                          </p>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 mt-4">
                          <button className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors">
                            <ThumbsUp className="w-4 h-4" />
                            Approve
                          </button>
                          <button className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors">
                            <ThumbsDown className="w-4 h-4" />
                            Reject
                          </button>
                          <button className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors">
                            <Flag className="w-4 h-4" />
                            Flag for Escalation
                          </button>
                        </div>
                      </div>

                      {/* Document verification grid */}
                      <div className="bg-white rounded-xl border border-slate-200 p-5">
                        <h4 className="text-sm font-bold text-slate-800 mb-4">Document Verification</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {rec.documents.map((doc) => {
                            const dc = docStatusConfig[doc.status];
                            return (
                              <div
                                key={doc.name}
                                className={`rounded-lg border p-3 ${
                                  doc.status === 'verified'
                                    ? 'border-emerald-200 bg-emerald-50/40'
                                    : doc.status === 'failed'
                                      ? 'border-red-200 bg-red-50/40'
                                      : 'border-amber-200 bg-amber-50/40'
                                }`}
                              >
                                <div className="flex items-center justify-between mb-1.5">
                                  <div className="flex items-center gap-2">
                                    <FileText className={`w-4 h-4 ${dc.color}`} />
                                    <span className="text-[13px] font-semibold text-slate-700">
                                      {doc.name}
                                    </span>
                                  </div>
                                  <span className={`flex items-center gap-1 text-[11px] font-semibold ${dc.color}`}>
                                    <dc.icon className="w-3.5 h-3.5" strokeWidth={2.5} />
                                    {dc.label}
                                  </span>
                                </div>
                                <p className="text-[11px] text-slate-400 flex items-center gap-1 mb-1">
                                  <Link2 className="w-3 h-3" />
                                  {doc.source}
                                </p>
                                <p className="text-[12px] text-slate-500 leading-snug">{doc.detail}</p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>

                    {/* Right: Source Trace audit trail */}
                    <div className="bg-white rounded-xl border border-slate-200 p-5">
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center">
                          <ShieldCheck className="w-4 h-4 text-slate-600" />
                        </div>
                        <h4 className="text-sm font-bold text-slate-800">Source Trace</h4>
                      </div>
                      <p className="text-[11px] text-slate-400 mb-4">
                        Checked against official government portals in real time.
                      </p>

                      <div className="relative">
                        {/* Vertical line */}
                        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-slate-200"></div>

                        <div className="space-y-4">
                          {rec.auditTrail.map((entry, i) => {
                            const ac = auditStatusConfig[entry.status];
                            return (
                              <div key={i} className="relative flex items-start gap-3 pl-0">
                                <div className={`w-[15px] h-[15px] rounded-full ${ac.color} bg-white border-2 border-current flex items-center justify-center shrink-0 z-10 mt-0.5`}>
                                  <ac.icon className="w-2.5 h-2.5" strokeWidth={3} />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between gap-2">
                                    <p className="text-[12px] font-semibold text-slate-700">{entry.source}</p>
                                    <span className="text-[10px] text-slate-400 font-mono shrink-0">
                                      {entry.timestamp}
                                    </span>
                                  </div>
                                  <p className="text-[11px] text-slate-400 leading-snug mt-0.5">
                                    {entry.label}
                                  </p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {rec.officer && (
                        <div className="mt-5 pt-4 border-t border-slate-100">
                          <p className="text-[11px] text-slate-400">Reviewed by</p>
                          <p className="text-[13px] font-semibold text-slate-700">{rec.officer}</p>
                        </div>
                      )}

                      <button className="w-full mt-5 flex items-center justify-center gap-1.5 py-2 text-[12px] font-semibold text-navy-600 bg-navy-50 rounded-lg hover:bg-navy-100 transition-colors">
                        View Full Audit Log
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Import records at module scope via separate import to avoid circular issues
import { records } from '@/data/records';
