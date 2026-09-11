import { useEffect, useState } from 'react';
import { 
  LayoutDashboard, 
  FileCheck, 
  AlertTriangle, 
  ShieldCheck, 
  ArrowUpRight, 
  Clock, 
  Building, 
  CheckCircle2, 
  XCircle, 
  Info, 
  ChevronRight,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import { api } from '@/services/api';
import { formatINR } from '@/utils/formatINR';

interface SuggestedTender {
  tender_id: string;
  tender_reference: string;
  tender_name: string;
  department: string;
  tender_value: number;
  closing_date: string;
  match_score: number;
  readiness: 'Strong Match' | 'Good Match' | 'Requirements Need Review';
  satisfied_requirements: string[];
  missing_requirements: string[];
  failed_requirements: string[];
  reasons: string[];
  explanation: string;
}

interface ActionItem {
  issue: string;
  reason: string;
  requirement: string;
  document_id?: string;
  document_name?: string;
  action: string;
  bid_id?: string;
}

interface DashboardData {
  active_bids: number;
  pending_bids: number;
  approved_bids: number;
  rejected_bids: number;
  total_documents: number;
  verified_documents: number;
  failed_documents: number;
  compliance_percentage: number;
  action_required: number;
  action_items?: ActionItem[];
  vendor_name?: string;
}

interface BidderDashboardProps {
  currentUser?: any;
  onNavigate?: (tab: string) => void;
  onOpenTender?: (tender: any) => void;
}

export default function BidderDashboard({ currentUser, onNavigate, onOpenTender }: BidderDashboardProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [suggestedTenders, setSuggestedTenders] = useState<SuggestedTender[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterActionOnly, setFilterActionOnly] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashRes, sugRes] = await Promise.all([
        api.get('/bidder/dashboard'),
        api.get('/bidder/suggested-tenders')
      ]);
      setData(dashRes.data);
      setSuggestedTenders(sugRes.data || []);
    } catch (err: any) {
      console.error('Error loading bidder dashboard:', err);
      setError('Failed to load dashboard data. Please verify your connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatCurrency = (val: number) => formatINR(val);

  const displayName = data?.vendor_name || currentUser?.full_name || 'Vendor';

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-navy-600 animate-spin" />
          <p className="text-sm font-medium text-slate-500">Loading compliance data and suggested tenders...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-red-50 border border-red-200 rounded-xl text-red-700 m-6">
        <p className="font-bold mb-1">Dashboard Error</p>
        <p className="text-sm">{error}</p>
        <button 
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-xs font-bold hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const complianceScore = data?.compliance_percentage ?? 0;
  const verifiedCount = data?.verified_documents ?? 0;
  const totalDocs = data?.total_documents ?? 0;
  const actionRequiredCount = data?.action_required ?? 0;
  const actionItems = data?.action_items || [];

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
              Welcome back, {displayName}
            </h1>
            <span className="text-[10px] font-bold bg-navy-50 text-navy-700 border border-navy-200 px-2 py-0.5 rounded-full">
              GeM BIDDER PORTAL
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Here's your current bidding and compliance readiness.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate?.('tenders')}
            className="px-4 py-2 bg-navy-700 hover:bg-navy-800 text-white text-xs font-bold rounded-lg shadow-sm transition-all flex items-center gap-1.5"
          >
            Explore Active Tenders
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. Four Dynamic Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Bids */}
        <div 
          onClick={() => onNavigate?.('bids')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-navy-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
              <LayoutDashboard className="w-5 h-5" />
            </div>
            <span className="text-[11px] font-semibold text-slate-400">Total: {data?.active_bids ?? 0}</span>
          </div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Bids</p>
          <p className="text-2xl font-extrabold text-slate-800 mt-1">{data?.active_bids ?? 0}</p>
          <p className="text-[11px] text-slate-400 mt-2">
            {data?.pending_bids ?? 0} pending officer review
          </p>
        </div>

        {/* Compliance Score */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">
              {complianceScore >= 80 ? 'HIGH' : complianceScore >= 50 ? 'MEDIUM' : 'LOW'}
            </span>
          </div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Compliance Score</p>
          <p className="text-2xl font-extrabold text-slate-800 mt-1">{complianceScore.toFixed(1)}%</p>
          <p className="text-[11px] text-slate-400 mt-2">Deterministic rules calculation</p>
        </div>

        {/* Verified Documents */}
        <div 
          onClick={() => onNavigate?.('documents')}
          className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-emerald-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
              <FileCheck className="w-5 h-5" />
            </div>
            <span className="text-[11px] font-semibold text-slate-400">
              {totalDocs > 0 ? `${Math.round((verifiedCount / totalDocs) * 100)}%` : '0%'}
            </span>
          </div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Verified Documents</p>
          <p className="text-2xl font-extrabold text-slate-800 mt-1">
            {verifiedCount} <span className="text-sm font-normal text-slate-400">/ {totalDocs}</span>
          </p>
          <p className="text-[11px] text-slate-400 mt-2">
            Exact SHA-256 traceable docs
          </p>
        </div>

        {/* Action Required */}
        <div 
          onClick={() => setFilterActionOnly(!filterActionOnly)}
          className={`p-5 rounded-xl border shadow-sm transition-all cursor-pointer group ${
            actionRequiredCount > 0 
              ? 'bg-amber-50/60 border-amber-200 hover:border-amber-400' 
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform ${
              actionRequiredCount > 0 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'
            }`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            {actionRequiredCount > 0 && (
              <span className="text-[10px] font-bold bg-amber-200 text-amber-900 px-2 py-0.5 rounded animate-pulse">
                ACTION NEEDED
              </span>
            )}
          </div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Action Required</p>
          <p className="text-2xl font-extrabold text-slate-800 mt-1">{actionRequiredCount}</p>
          <p className="text-[11px] text-slate-500 mt-2">
            {actionRequiredCount > 0 ? 'Click to inspect & remediate' : 'All requirements satisfied'}
          </p>
        </div>
      </div>

      {/* 3. Compliance Overview & Readiness Progress Indicator */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-navy-600" />
              Compliance Overview & Readiness
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Automated deterministic verification against tender eligibility standards and registry cross-checks.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Readiness Status:</span>
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
              complianceScore >= 80 
                ? 'bg-emerald-100 text-emerald-800' 
                : complianceScore >= 50 
                  ? 'bg-amber-100 text-amber-800' 
                  : 'bg-rose-100 text-rose-800'
            }`}>
              {complianceScore >= 80 ? 'Strong Readiness' : complianceScore >= 50 ? 'Good Standing' : 'Action Needed'}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 h-3.5 rounded-full overflow-hidden mb-4 p-0.5">
          <div 
            className={`h-full rounded-full transition-all duration-500 ${
              complianceScore >= 80 
                ? 'bg-emerald-500' 
                : complianceScore >= 50 
                  ? 'bg-amber-500' 
                  : 'bg-rose-500'
            }`}
            style={{ width: `${Math.max(complianceScore, 4)}%` }}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <div>
              <p className="text-xs text-slate-400 font-medium">Compliance Rate</p>
              <p className="text-sm font-bold text-slate-800">{complianceScore.toFixed(1)}%</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
            <div>
              <p className="text-xs text-slate-400 font-medium">Verified Documents</p>
              <p className="text-sm font-bold text-slate-800">{verifiedCount} of {totalDocs} Documents</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <div>
              <p className="text-xs text-slate-400 font-medium">Pending Remediations</p>
              <p className="text-sm font-bold text-slate-800">{actionRequiredCount} Issues Flagged</p>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Action Required / Remediation Flow (Detect -> Explain -> Fix -> Reverify) */}
      {actionItems.length > 0 && (
        <div className="bg-white rounded-2xl border border-amber-200 shadow-sm overflow-hidden">
          <div className="p-5 bg-amber-50/70 border-b border-amber-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-700" />
              <h3 className="font-bold text-amber-950 text-sm">
                Remediation Items ({actionItems.length})
              </h3>
            </div>
            <span className="text-[11px] font-semibold text-amber-800 bg-amber-100 px-2.5 py-1 rounded-full">
              Detect → Explain → Fix → Reverify
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {actionItems.map((item, idx) => (
              <div key={idx} className="p-4 hover:bg-slate-50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1 max-w-2xl">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-800">{item.issue}</span>
                    <span className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      Req: {item.requirement}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    <span className="font-semibold text-slate-700">Reason:</span> {item.reason}
                  </p>
                  {item.document_name && (
                    <p className="text-[11px] text-slate-400">
                      Target File: <span className="font-mono text-slate-600">{item.document_name}</span>
                    </p>
                  )}
                </div>

                <div className="shrink-0">
                  <button
                    onClick={() => onNavigate?.('bids')}
                    className="px-3.5 py-1.5 bg-navy-700 hover:bg-navy-800 text-white text-xs font-bold rounded-lg shadow-sm transition-all flex items-center gap-1"
                  >
                    {item.action}
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Suggested Tenders For You (Filtered server-side for >= 1 Lakh) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              Suggested Tenders For You
              <span className="text-xs font-medium text-slate-400">
                (Excludes bids below ₹1,00,000)
              </span>
            </h3>
            <p className="text-xs text-slate-500">
              AI & deterministic matching based exclusively on your currently verified documents.
            </p>
          </div>
          <button
            onClick={() => onNavigate?.('tenders')}
            className="text-xs font-bold text-navy-600 hover:text-navy-800 flex items-center gap-1"
          >
            View All Tenders
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {suggestedTenders.length === 0 ? (
          <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center">
            <Building className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <h4 className="text-sm font-bold text-slate-700 mb-1">No Matching Tenders Found</h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto mb-4">
              All listed tenders meet the GeM minimum procurement threshold (₹1,00,000). Upload and verify more documents to increase your eligibility match.
            </p>
            <button
              onClick={() => onNavigate?.('tenders')}
              className="px-4 py-2 bg-navy-700 text-white text-xs font-bold rounded-lg hover:bg-navy-800"
            >
              Browse Active Tenders
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {suggestedTenders.map((tender) => {
              const badgeCls = 
                tender.readiness === 'Strong Match' 
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                  : tender.readiness === 'Good Match'
                    ? 'bg-blue-50 text-blue-700 border-blue-200'
                    : 'bg-amber-50 text-amber-700 border-amber-200';

              return (
                <div 
                  key={tender.tender_id}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {/* Badge & Score */}
                    <div className="flex items-center justify-between gap-2">
                      <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${badgeCls}`}>
                        {tender.readiness}
                      </span>
                      <div className="flex items-center gap-1 text-xs font-extrabold text-navy-800 bg-navy-50 px-2 py-0.5 rounded">
                        <span>{tender.match_score}%</span>
                        <span className="text-[10px] text-slate-400 font-normal">Match</span>
                      </div>
                    </div>

                    {/* Title & Ref */}
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm leading-snug line-clamp-2">
                        {tender.tender_name}
                      </h4>
                      <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                        Ref: {tender.tender_reference}
                      </p>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-1">
                        {tender.department}
                      </p>
                    </div>

                    {/* Tender Value & Deadline */}
                    <div className="grid grid-cols-2 gap-2 p-2.5 bg-slate-50 rounded-xl text-xs">
                      <div>
                        <p className="text-[10px] text-slate-400 font-semibold uppercase">Estimated Value</p>
                        <p className="font-bold text-slate-800 mt-0.5">
                          {formatCurrency(tender.tender_value)}
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-slate-400 font-semibold uppercase">Closing Date</p>
                        <p className="font-bold text-slate-800 mt-0.5 flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          {tender.closing_date}
                        </p>
                      </div>
                    </div>

                    {/* Explainable Reasons */}
                    <div className="space-y-1 pt-1">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Compliance Fit</p>
                      <p className="text-xs text-slate-600 leading-snug">{tender.explanation}</p>
                      {tender.satisfied_requirements.length > 0 && (
                        <p className="text-[11px] text-emerald-700 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 shrink-0" />
                          Satisfied: {tender.satisfied_requirements.slice(0, 2).join(', ')}
                          {tender.satisfied_requirements.length > 2 && ` +${tender.satisfied_requirements.length - 2} more`}
                        </p>
                      )}
                      {tender.missing_requirements.length > 0 && (
                        <p className="text-[11px] text-amber-700 flex items-center gap-1">
                          <Info className="w-3 h-3 shrink-0" />
                          Missing: {tender.missing_requirements.slice(0, 2).join(', ')}
                          {tender.missing_requirements.length > 2 && ` +${tender.missing_requirements.length - 2} more`}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Button */}
                  <div className="pt-4 mt-4 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => {
                        if (onOpenTender) {
                          onOpenTender({
                            id: tender.tender_id,
                            tender_id: tender.tender_reference,
                            title: tender.tender_name,
                            department: tender.department,
                            estimated_value: tender.tender_value
                          });
                        } else {
                          onNavigate?.('tenders');
                        }
                      }}
                      className="w-full py-2 bg-navy-700 hover:bg-navy-800 text-white text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-1 shadow-sm"
                    >
                      View Tender & Submit Bid
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
