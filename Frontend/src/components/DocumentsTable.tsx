import { useEffect, useState } from 'react';
import { Download, Eye, FileText, RefreshCw, X, AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react';
import { DocumentRecord, downloadDocumentApi, fetchDocuments, viewDocumentApi } from '@/services/api';
import { useTranslation } from '@/i18n';

const statusClass = (status: string) => {
  const normalized = status.toLowerCase();
  if (normalized === 'verified' || normalized === 'valid') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (normalized === 'failed' || normalized === 'invalid') return 'bg-red-50 text-red-700 border-red-200';
  return 'bg-amber-50 text-amber-700 border-amber-200';
};

export default function DocumentsTable({ searchTerm = '' }: { searchTerm?: string }) {
  const { t } = useTranslation();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentRecord | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const getStatusLabel = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized === 'verified' || normalized === 'valid') return { label: `✓ ${t('valid')}`, icon: CheckCircle2 };
    if (normalized.includes('missing')) return { label: `✕ ${t('missing')}`, icon: AlertTriangle };
    if (normalized.includes('expired')) return { label: `⚠ ${t('expired')}`, icon: AlertTriangle };
    if (normalized.includes('unavailable')) return { label: `⚠ ${t('verificationUnavailable')}`, icon: AlertTriangle };
    if (normalized === 'failed' || normalized === 'invalid' || normalized === 'warning') return { label: `⚠ ${t('needsAttention')}`, icon: AlertTriangle };
    return { label: status, icon: HelpCircle };
  };

  const nextStep = (document: DocumentRecord) => {
    const result = `${document.document_status} ${document.verification_result} ${document.detail || ''}`.toLowerCase();
    if (result.includes('missing')) return 'Upload the required document before submitting the bid.';
    if (result.includes('expir')) return 'Upload a current version of this document.';
    if (result.includes('mismatch') || result.includes('match')) return 'Check whether the information in the submitted documents matches.';
    if (result.includes('unavailable')) return 'The verification source is currently unavailable. This does not automatically mean the document is invalid.';
    return document.detail || 'Review the verification details before continuing.';
  };

  const loadDocuments = () => {
    setLoading(true);
    fetchDocuments({ search: searchTerm })
      .then(setDocuments)
      .catch((error) => console.error('Failed to load documents', error))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const timer = setTimeout(loadDocuments, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {selectedDocument && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-start justify-between gap-4 mb-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{t('uploaded')} {t('documents')}</p>
                <h4 className="text-base font-bold text-slate-800 mt-1 break-all">{selectedDocument.filename}</h4>
              </div>
              <button onClick={() => setSelectedDocument(null)} aria-label={t('close')} className="text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div><p className="text-slate-400">{t('documentType')}</p><p className="font-semibold text-slate-700">{selectedDocument.document_type}</p></div>
              <div><p className="text-slate-400">{t('documentStatus')}</p><p className="font-semibold text-slate-700">{selectedDocument.document_status}</p></div>
              <div><p className="text-slate-400">{t('verification')}</p><p className="font-semibold text-slate-700">{selectedDocument.verification_result}</p></div>
              <div><p className="text-slate-400">{t('extractedFields')}</p><p className="font-semibold text-slate-700">{selectedDocument.extracted_fields_status}</p></div>
              <div className="col-span-2"><p className="text-slate-400">{t('relatedBidTender')}</p><p className="font-semibold text-slate-700">{selectedDocument.bid_reference} · {selectedDocument.tender_title}</p></div>
              <div className="col-span-2"><p className="text-slate-400">{t('uploaded')}</p><p className="font-semibold text-slate-700">{new Date(selectedDocument.upload_timestamp).toLocaleString()}</p></div>
            </div>
            <div className="mt-4 rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs text-slate-600">
              <p className="font-semibold text-slate-700 mb-1">{t('verificationDetails')}</p>
              <p>{selectedDocument.detail || selectedDocument.verification_result}</p>
              {selectedDocument.source && <p className="mt-1 text-slate-400">{t('source')}: {selectedDocument.source}</p>}
            </div>
            <div className="flex justify-end gap-2 mt-5">
              {selectedDocument.file_available && (
                <>
                  <button onClick={() => viewDocumentApi(selectedDocument.id).catch(() => alert('Failed to open document preview.'))} className="px-3 py-2 text-xs font-semibold text-indigo-700 border border-indigo-200 rounded-lg hover:bg-indigo-50 inline-flex items-center gap-1">
                    <Eye className="w-3.5 h-3.5" /> {t('preview')}
                  </button>
                  <button onClick={() => downloadDocumentApi(selectedDocument.id, selectedDocument.filename).catch(() => alert('Failed to download document.'))} className="px-3 py-2 text-xs font-semibold text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50 inline-flex items-center gap-1">
                    <Download className="w-3.5 h-3.5" /> {t('download')}
                  </button>
                </>
              )}
              <button onClick={() => setSelectedDocument(null)} className="px-3 py-2 text-xs font-semibold text-slate-600 bg-slate-100 rounded-lg">{t('close')}</button>
            </div>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
        <div>
          <h3 className="text-base font-bold text-slate-800">{t('myDocuments')}</h3>
          <p className="text-[12px] text-slate-400 mt-0.5">{t('documentStateDescription')}</p>
        </div>
        <button onClick={loadDocuments} className="flex items-center gap-1 px-3 py-1.5 text-[13px] font-medium text-slate-600 bg-slate-50 border border-slate-200 rounded-lg">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> {t('refresh')}
        </button>
      </div>

      {documents.length === 0 && !loading ? (
        <div className="px-6 py-16 text-center">
          <FileText className="w-10 h-10 mx-auto text-slate-300 mb-3" />
          <p className="text-sm font-semibold text-slate-700">{t('noDocumentsUploaded')}</p>
          <p className="text-xs text-slate-400 mt-1">{t('uploadFromBid')}</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {documents.map((document) => (
            <div key={document.id} className="px-6 py-4 hover:bg-slate-50">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  <FileText className="w-5 h-5 text-indigo-500 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-800 truncate">{document.filename}</p>
                    <p className="text-xs text-slate-500 mt-1">
                      {document.document_type} · Bid {document.bid_reference} · {document.tender_title}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {t('uploaded')} {new Date(document.upload_timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`px-2 py-1 rounded border text-[11px] font-semibold ${statusClass(document.document_status)}`}>
                    {getStatusLabel(document.document_status).label}
                  </span>
                  <span className={`px-2 py-1 rounded border text-[11px] font-semibold ${statusClass(document.extracted_fields_status)}`}>
                    {t('fields')}: {getStatusLabel(document.extracted_fields_status).label}
                  </span>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500">
                <span>{t('verification')}: <strong className="text-slate-700">{document.verification_result}</strong></span>
                {document.source && <span>{t('source')}: {document.source}</span>}
                {document.detail && <span className="text-red-600">{t('verificationDetailsLabel')}: {document.detail}</span>}
                <div className="ml-auto flex items-center gap-3">
                  {document.document_status.toLowerCase() !== 'verified' && (
                    <>
                      <button
                        onClick={() => setExpandedId(expandedId === document.id ? null : document.id)}
                        className="font-semibold text-slate-700 hover:underline inline-flex items-center gap-1"
                      >
                        <HelpCircle className="w-3.5 h-3.5" /> {t('why')} / {t('whatShouldIDo')}
                      </button>
                      {expandedId === document.id && (
                        <div className="basis-full rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-slate-700">
                          <p><strong>{t('why')}</strong> {document.detail || document.verification_result}</p>
                          <p className="mt-1"><strong>{t('whatShouldIDo')}</strong> {nextStep(document)}</p>
                        </div>
                      )}
                    </>
                  )}
                  <button onClick={() => setSelectedDocument(document)} className="font-semibold text-indigo-700 hover:underline inline-flex items-center gap-1">
                    <Eye className="w-3.5 h-3.5" /> {t('viewDetails')}
                  </button>
                  {document.file_available && (
                    <>
                      <button onClick={() => viewDocumentApi(document.id).catch(() => alert('Failed to open document preview.'))} className="font-semibold text-indigo-700 hover:underline inline-flex items-center gap-1">
                        {t('preview')}
                      </button>
                      <button onClick={() => downloadDocumentApi(document.id, document.filename).catch(() => alert('Failed to download document.'))} className="font-semibold text-slate-700 hover:underline inline-flex items-center gap-1">
                        <Download className="w-3.5 h-3.5" /> {t('download')}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
