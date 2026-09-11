import { useEffect, useState } from 'react';
import { Download, Eye, FileText, RefreshCw, X } from 'lucide-react';
import { DocumentRecord, downloadDocumentApi, fetchDocuments, viewDocumentApi } from '@/services/api';

const statusClass = (status: string) => {
  const normalized = status.toLowerCase();
  if (normalized === 'verified' || normalized === 'valid') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (normalized === 'failed' || normalized === 'invalid') return 'bg-red-50 text-red-700 border-red-200';
  return 'bg-amber-50 text-amber-700 border-amber-200';
};

export default function DocumentsTable({ searchTerm = '' }: { searchTerm?: string }) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentRecord | null>(null);

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
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Uploaded document</p>
                <h4 className="text-base font-bold text-slate-800 mt-1 break-all">{selectedDocument.filename}</h4>
              </div>
              <button onClick={() => setSelectedDocument(null)} aria-label="Close document details" className="text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div><p className="text-slate-400">Document type</p><p className="font-semibold text-slate-700">{selectedDocument.document_type}</p></div>
              <div><p className="text-slate-400">Document status</p><p className="font-semibold text-slate-700">{selectedDocument.document_status}</p></div>
              <div><p className="text-slate-400">Verification</p><p className="font-semibold text-slate-700">{selectedDocument.verification_result}</p></div>
              <div><p className="text-slate-400">Extracted fields</p><p className="font-semibold text-slate-700">{selectedDocument.extracted_fields_status}</p></div>
              <div className="col-span-2"><p className="text-slate-400">Related bid/tender</p><p className="font-semibold text-slate-700">{selectedDocument.bid_reference} · {selectedDocument.tender_title}</p></div>
              <div className="col-span-2"><p className="text-slate-400">Uploaded</p><p className="font-semibold text-slate-700">{new Date(selectedDocument.upload_timestamp).toLocaleString()}</p></div>
            </div>
            <div className="mt-4 rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs text-slate-600">
              <p className="font-semibold text-slate-700 mb-1">Verification details</p>
              <p>{selectedDocument.detail || selectedDocument.verification_result}</p>
              {selectedDocument.source && <p className="mt-1 text-slate-400">Source: {selectedDocument.source}</p>}
            </div>
            <div className="flex justify-end gap-2 mt-5">
              {selectedDocument.file_available && (
                <>
                  <button onClick={() => viewDocumentApi(selectedDocument.id).catch(() => alert('Failed to open document preview.'))} className="px-3 py-2 text-xs font-semibold text-indigo-700 border border-indigo-200 rounded-lg hover:bg-indigo-50 inline-flex items-center gap-1">
                    <Eye className="w-3.5 h-3.5" /> Preview
                  </button>
                  <button onClick={() => downloadDocumentApi(selectedDocument.id, selectedDocument.filename).catch(() => alert('Failed to download document.'))} className="px-3 py-2 text-xs font-semibold text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50 inline-flex items-center gap-1">
                    <Download className="w-3.5 h-3.5" /> Download
                  </button>
                </>
              )}
              <button onClick={() => setSelectedDocument(null)} className="px-3 py-2 text-xs font-semibold text-slate-600 bg-slate-100 rounded-lg">Close</button>
            </div>
          </div>
        </div>
      )}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
        <div>
          <h3 className="text-base font-bold text-slate-800">My Documents</h3>
          <p className="text-[12px] text-slate-400 mt-0.5">Individual uploaded documents and their verification state.</p>
        </div>
        <button onClick={loadDocuments} className="flex items-center gap-1 px-3 py-1.5 text-[13px] font-medium text-slate-600 bg-slate-50 border border-slate-200 rounded-lg">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {documents.length === 0 && !loading ? (
        <div className="px-6 py-16 text-center">
          <FileText className="w-10 h-10 mx-auto text-slate-300 mb-3" />
          <p className="text-sm font-semibold text-slate-700">No documents uploaded yet</p>
          <p className="text-xs text-slate-400 mt-1">Upload a document from a bid to see it here.</p>
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
                      Uploaded {new Date(document.upload_timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`px-2 py-1 rounded border text-[11px] font-semibold ${statusClass(document.document_status)}`}>
                    {document.document_status}
                  </span>
                  <span className={`px-2 py-1 rounded border text-[11px] font-semibold ${statusClass(document.extracted_fields_status)}`}>
                    Fields: {document.extracted_fields_status}
                  </span>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500">
                <span>Verification: <strong className="text-slate-700">{document.verification_result}</strong></span>
                {document.source && <span>Source: {document.source}</span>}
                {document.detail && <span className="text-red-600">Verification details: {document.detail}</span>}
                <div className="ml-auto flex items-center gap-3">
                  <button onClick={() => setSelectedDocument(document)} className="font-semibold text-indigo-700 hover:underline inline-flex items-center gap-1">
                    <Eye className="w-3.5 h-3.5" /> View details
                  </button>
                  {document.file_available && (
                    <>
                      <button onClick={() => viewDocumentApi(document.id).catch(() => alert('Failed to open document preview.'))} className="font-semibold text-indigo-700 hover:underline inline-flex items-center gap-1">
                        Preview
                      </button>
                      <button onClick={() => downloadDocumentApi(document.id, document.filename).catch(() => alert('Failed to download document.'))} className="font-semibold text-slate-700 hover:underline inline-flex items-center gap-1">
                        <Download className="w-3.5 h-3.5" /> Download
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
