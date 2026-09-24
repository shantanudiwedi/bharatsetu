import { useEffect, useRef, useState } from 'react';
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
  Upload,
  Download,
  Eye,
  RefreshCw,
} from 'lucide-react';
import {
  fetchBids,
  approveBidApi,
  rejectBidApi,
  escalateBidApi,
  uploadBidDocument,
  triggerBidVerification,
  BidRecord,
  viewDocumentApi,
  downloadDocumentApi,
  downloadComplianceReportApi
} from '@/services/api';
import { formatINR } from '@/utils/formatINR';
import { useTranslation } from '@/i18n';

export default function VerificationTable({ searchTerm = '', currentUser, listMode = 'bids' }: { searchTerm?: string; currentUser?: any; listMode?: 'bids' | 'documents' }) {
  const { t } = useTranslation();
  const riskConfig: Record<'low' | 'medium' | 'high', { label: string; cls: string; icon: typeof ShieldCheck }> = {
    low: { label: t('lowRisk'), cls: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: ShieldCheck },
    medium: { label: t('mediumRisk'), cls: 'bg-amber-50 text-amber-700 border-amber-200', icon: ShieldAlert },
    high: { label: t('highRisk'), cls: 'bg-red-50 text-red-700 border-red-200', icon: ShieldX },
  };
  const statusConfig: Record<string, { label: string; cls: string; dot: string }> = {
    pending_review: { label: t('pendingReviewStatus'), cls: 'bg-navy-50 text-navy-700', dot: 'bg-navy-500' },
    approved: { label: t('approved'), cls: 'bg-emerald-50 text-emerald-700', dot: 'bg-emerald-500' },
    rejected: { label: t('rejected'), cls: 'bg-red-50 text-red-700', dot: 'bg-red-500' },
    flagged: { label: t('flagged'), cls: 'bg-amber-50 text-amber-700', dot: 'bg-amber-500' },
  };
  const docStatusConfig: Record<string, { icon: typeof CheckCircle2; color: string; label: string }> = {
    verified: { icon: CheckCircle2, color: 'text-emerald-500', label: t('verified') },
    failed: { icon: XCircle, color: 'text-red-500', label: t('failed') },
    pending: { icon: Clock3, color: 'text-amber-500', label: t('pending') },
    uploaded: { icon: Clock3, color: 'text-amber-500', label: t('uploaded') },
    processing: { icon: Clock3, color: 'text-amber-500', label: t('processing') },
    in_progress: { icon: Clock3, color: 'text-amber-500', label: t('inProgress') },
    manual_review_required: { icon: Clock3, color: 'text-amber-500', label: t('manualReview') },
    warning: { icon: Clock3, color: 'text-amber-500', label: t('warning') },
  };
  const [records, setRecords] = useState<BidRecord[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>('GEM-2026-04827');
  const [actionReason, setActionReason] = useState<string>('');
  const [activeActionModal, setActiveActionModal] = useState<{ id: string; action: 'reject' | 'escalate' } | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploadingDoc, setUploadingDoc] = useState<boolean>(false);
  const fileInputs = useRef<Record<string, HTMLInputElement | null>>({});

  const loadBids = () => {
    setLoading(true);
    fetchBids({ search: searchTerm })
      .then((data) => {
        const filteredRecords = listMode === 'documents'
          ? data.filter((bid) => bid.documents && bid.documents.length > 0)
          : data;
        setRecords(filteredRecords);
        if (filteredRecords.length > 0 && !expandedId) {
          setExpandedId(filteredRecords[0].id);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadBids();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm, listMode]);

  const filteredRecords = listMode === 'documents'
    ? records.filter((bid) => bid.documents && bid.documents.length > 0)
    : records;

  const toggle = (id: string) => setExpandedId((prev) => (prev === id ? null : id));

  const handleApprove = async (bidId: string) => {
    try {
      await approveBidApi(bidId, 'Compliance verified by procurement officer.');
      loadBids();
    } catch (e) {
      alert('Failed to approve bid');
    }
  };

  const submitActionWithReason = async () => {
    if (!activeActionModal) return;
    if (!actionReason.trim()) {
      alert('Please enter a comment/reason for this decision');
      return;
    }
    try {
      if (activeActionModal.action === 'reject') {
        await rejectBidApi(activeActionModal.id, actionReason);
      } else {
        await escalateBidApi(activeActionModal.id, actionReason);
      }
      setActiveActionModal(null);
      setActionReason('');
      loadBids();
    } catch (e) {
      alert('Failed to submit decision');
    }
  };

  const handleFileUpload = async (bidId: string, file: File, documentType?: string) => {
    setUploadingDoc(true);
    try {
      await uploadBidDocument(bidId, file, documentType);
      await triggerBidVerification(bidId);
      loadBids();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Document upload error');
    } finally {
      setUploadingDoc(false);
    }
  };

  const downloadReport = async (bidId: string) => {
    try {
      await downloadComplianceReportApi(bidId);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to generate compliance report.');
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden relative">
      {/* Action Reason Modal */}
      {activeActionModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-fade-in">
            <h4 className="text-base font-bold text-slate-800 mb-2">
              {activeActionModal.action === 'reject' ? 'Reject Bid Submission' : 'Escalate Bid for Senior Review'}
            </h4>
            <p className="text-xs text-slate-500 mb-4">
              Enter mandatory officer decision comment/reason for audit trail recording:
            </p>
            <textarea
              rows={3}
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
              placeholder="Enter official reason..."
              className="w-full p-3 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-navy-400 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setActiveActionModal(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={submitActionWithReason}
                className={`px-4 py-2 text-xs font-semibold text-white rounded-lg ${
                  activeActionModal.action === 'reject' ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-600 hover:bg-amber-700'
                }`}
              >
                Confirm {activeActionModal.action === 'reject' ? 'Rejection' : 'Escalation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
        <div>
          <h3 className="text-base font-bold text-slate-800">
            {listMode === 'documents' ? t('myDocuments') : currentUser?.role === 'BIDDER' ? t('myBids') : t('verificationQueue')}
          </h3>
          <p className="text-[12px] text-slate-400 mt-0.5">
            {listMode === 'documents'
              ? t('documentStateDescription')
              : t('aiAssistedVerification')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadBids}
            className="flex items-center gap-1 px-3 py-1.5 text-[13px] font-medium text-slate-600 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            {t('refresh')}
          </button>
        </div>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[40px_1.5fr_1fr_1fr_1fr_120px_40px] gap-3 px-6 py-3 bg-slate-50 border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        <div></div>
        <div>{t('vendorColumn')}</div>
        <div>{t('categoryColumn')}</div>
        <div>{t('bidAmount')}</div>
        <div>{t('documentsColumn')}</div>
        <div>{t('riskProfile')}</div>
        <div></div>
      </div>

      <div className="divide-y divide-slate-100">
        {filteredRecords.map((rec) => {
          const isOpen = expandedId === rec.id;
          const risk = riskConfig[rec.riskLevel] || riskConfig.medium;
          const status = statusConfig[rec.status] || statusConfig.pending_review;

          return (
            <div key={rec.id}>
              {/* Summary row */}
              <button
                onClick={() => toggle(rec.id)}
                className={`w-full grid grid-cols-[40px_1.5fr_1fr_1fr_1fr_120px_40px] gap-3 px-6 py-4 items-center text-left transition-colors ${
                  isOpen ? 'bg-navy-50/50' : 'hover:bg-slate-50'
                }`}
              >
                {/* Status dot */}
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
                <div className="text-sm font-semibold text-slate-700">{formatINR(rec.bidAmount)}</div>

                {/* Doc status grid */}
                <div className="flex items-center gap-1.5 overflow-x-auto">
                  {rec.documents.map((doc, idx) => {
                    const dc = docStatusConfig[doc.status] || docStatusConfig.pending;
                    return (
                      <div
                        key={idx}
                        title={`${doc.name}: ${dc.label} — ${doc.detail}`}
                        className={`flex items-center gap-1 px-1.5 py-1 rounded-md border text-[10px] font-semibold shrink-0 ${
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
                <div className="px-6 pb-6 bg-navy-50/30">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 pt-2">
                    {/* Left: AI summary & documents */}
                    <div className="lg:col-span-2 space-y-5">
                      {/* AI Recommendation */}
                      <div className="bg-white rounded-xl border border-slate-200 p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-navy-500 to-navy-700 flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white" />
                          </div>
                          <h4 className="text-sm font-bold text-slate-800">Explainable AI Summary</h4>
                          <span className="ml-auto text-[11px] font-semibold text-navy-600 bg-navy-50 px-2 py-0.5 rounded">
                            {rec.aiConfidence}% confidence
                          </span>
                        </div>
                        <p className="text-[13px] text-slate-600 leading-relaxed mb-3">
                          {rec.aiRecommendation}
                        </p>
                        <p className="text-[12px] text-slate-400 leading-relaxed">{rec.aiSummary}</p>

                        {/* Human oversight banner */}
                        {currentUser?.role !== 'BIDDER' && (
                          <div className="mt-4 flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5">
                            <UserCog className="w-4 h-4 text-amber-600 shrink-0" />
                            <p className="text-[12px] text-amber-700 font-medium">
                              Authorized Human Officer Decision Required. AI provides decision support only.
                            </p>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex flex-wrap items-center gap-2 mt-4">
                          {currentUser?.role !== 'BIDDER' && (
                            <>
                              <button
                                onClick={() => handleApprove(rec.id)}
                                className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors shadow-sm"
                              >
                                <ThumbsUp className="w-4 h-4" />
                                Approve
                              </button>
                              <button
                                onClick={() => setActiveActionModal({ id: rec.id, action: 'reject' })}
                                className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors shadow-sm"
                              >
                                <ThumbsDown className="w-4 h-4" />
                                Reject
                              </button>
                              <button
                                onClick={() => setActiveActionModal({ id: rec.id, action: 'escalate' })}
                                className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors"
                              >
                                <Flag className="w-4 h-4" />
                                Flag for Escalation
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => downloadReport(rec.id)}
                            className="flex items-center gap-1.5 px-4 py-2 text-[13px] font-semibold text-slate-700 bg-slate-100 border border-slate-200 rounded-lg hover:bg-slate-200 transition-colors ml-auto"
                          >
                            <Download className="w-4 h-4 text-slate-500" />
                            PDF Compliance Report
                          </button>
                        </div>
                      </div>

                      {/* Document verification grid & Upload */}
                      <div className="bg-white rounded-xl border border-slate-200 p-5">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-sm font-bold text-slate-800">Document Verification & Upload</h4>
                        </div>

                        {currentUser?.role === 'BIDDER' && rec.requirements && rec.requirements.length > 0 && (
                          <div className="mb-4 rounded-lg border border-slate-200 divide-y divide-slate-100">
                            {rec.requirements.map((requirement) => {
                                              const requirementType = requirement.document_type.trim().toUpperCase();
                                              const matchingDocuments = rec.documents.filter((document) => (
                                                (document.document_type || document.name || '').trim().toUpperCase() === requirementType
                                              ));
                                              const uploaded = matchingDocuments.length > 0;
                                              const latestDocument = matchingDocuments[matchingDocuments.length - 1];
                                              return (
                                                <div key={requirementType} className="flex items-center gap-3 px-3 py-2.5">
                                                  {uploaded ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <Clock3 className="w-4 h-4 text-slate-400 shrink-0" />}
                                                  <div className="min-w-0 flex-1">
                                                    <p className="text-xs font-bold text-slate-700">{requirementType}</p>
                                                    <p className="text-[11px] text-slate-500">
                                                      {uploadingDoc
                                                        ? 'Uploading...'
                                                        : uploaded
                                                          ? `${latestDocument?.status === 'verified' ? 'Verified' : latestDocument?.status === 'failed' ? 'Failed - Replace available' : 'Uploaded - Pending Verification'}${latestDocument?.detail ? ` - ${latestDocument.detail}` : ''}`
                                                          : requirement.is_mandatory ? 'Required - Not uploaded' : 'Optional - Not uploaded'}
                                                    </p>
                                                  </div>
                                                  <button
                                                    type="button"
                                                    disabled={uploadingDoc}
                                                    onClick={() => fileInputs.current[requirementType]?.click()}
                                                    className="px-2.5 py-1.5 text-[11px] font-semibold text-navy-700 bg-navy-50 rounded-md hover:bg-navy-100 disabled:opacity-50"
                                                  >
                                                    {uploaded ? 'Replace' : 'Upload'}
                                                  </button>
                                                  <input
                                                    ref={(input) => {
                                                      fileInputs.current[requirementType] = input;
                                                    }}
                                                    type="file"
                                                    accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                                                    className="sr-only"
                                                    disabled={uploadingDoc}
                                                    onChange={(event) => {
                                                      const file = event.currentTarget.files?.[0];
                                                      if (file) {
                                                        void handleFileUpload(rec.id, file, requirementType);
                                                      }
                                                      event.currentTarget.value = '';
                                                    }}
                                                  />
                                                </div>
                                              );
                                            })}
                          </div>
                        )}

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {rec.documents.map((doc, idx) => {
                            const dc = docStatusConfig[doc.status] || docStatusConfig.pending;
                            return (
                              <div
                                key={idx}
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
                                    <span 
                                      className="text-[13px] font-semibold text-slate-700 cursor-pointer hover:text-navy-600 hover:underline"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        if (doc.id) {
                                          viewDocumentApi(doc.id).catch(() => alert('Failed to open document.'));
                                        } else {
                                          alert('Document ID is missing.');
                                        }
                                      }}
                                    >
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
                                <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-200/60">
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      if (doc.id) viewDocumentApi(doc.id).catch(() => alert('Failed to open document preview.'));
                                    }}
                                    className="text-[11px] font-semibold text-navy-700 hover:text-navy-900 flex items-center gap-1 hover:underline"
                                  >
                                    <Eye className="w-3 h-3" /> Preview
                                  </button>
                                  <span className="text-slate-300">|</span>
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      if (doc.id) downloadDocumentApi(doc.id, doc.name).catch(() => alert('Failed to download document.'));
                                    }}
                                    className="text-[11px] font-semibold text-slate-600 hover:text-slate-800 flex items-center gap-1 hover:underline"
                                  >
                                    <Download className="w-3 h-3" /> Download
                                  </button>
                                  {currentUser?.role === 'BIDDER' && (
                                    <>
                                      <span className="text-slate-300">|</span>
                                      <button
                                        type="button"
                                        disabled={uploadingDoc}
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          const documentType = (doc.document_type || doc.name || '').trim().toUpperCase();
                                          fileInputs.current[documentType]?.click();
                                        }}
                                        className="text-[11px] font-semibold text-navy-700 hover:text-navy-900 flex items-center gap-1 hover:underline disabled:opacity-50"
                                      >
                                        <RefreshCw className="w-3 h-3" /> Replace
                                      </button>
                                    </>
                                  )}
                                </div>
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
                        Verified against simulated government registries.
                      </p>

                      <div className="relative">
                        {/* Vertical line */}
                        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-slate-200"></div>

                        <div className="space-y-4">
                          {rec.audit_trail.map((entry, i) => {
                            const isPass = entry.status === 'pass';
                            const isFail = entry.status === 'fail';
                            return (
                              <div key={i} className="relative flex items-start gap-3 pl-0">
                                <div className={`w-[15px] h-[15px] rounded-full ${
                                  isPass ? 'text-emerald-500' : isFail ? 'text-red-500' : 'text-amber-500'
                                } bg-white border-2 border-current flex items-center justify-center shrink-0 z-10 mt-0.5`}>
                                  {isPass ? (
                                    <CheckCircle2 className="w-2.5 h-2.5" strokeWidth={3} />
                                  ) : isFail ? (
                                    <XCircle className="w-2.5 h-2.5" strokeWidth={3} />
                                  ) : (
                                    <Clock3 className="w-2.5 h-2.5" strokeWidth={3} />
                                  )}
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
