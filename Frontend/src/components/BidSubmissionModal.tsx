import { useEffect, useRef, useState } from 'react';
import { X, Building, CheckCircle2, Circle } from 'lucide-react';
import { createBidApi, fetchTenders, uploadBidDocument, triggerBidVerification } from '@/services/api';
import { useTranslation } from '@/i18n';

interface BidSubmissionModalProps {
  isOpen: boolean;
  selectedTender?: any | null;
  onClose: () => void;
  onSuccess: () => void;
}

interface SelectedDocument {
  file: File;
  status: 'selected';
}

interface TenderRequirement {
  id?: string;
  document_type: string;
  is_mandatory?: boolean;
  description?: string;
}

export default function BidSubmissionModal({ isOpen, selectedTender, onClose, onSuccess }: BidSubmissionModalProps) {
  const [vendorName, setVendorName] = useState('');
  const [category, setCategory] = useState('');
  const [bidAmount, setBidAmount] = useState('');
  const [gstin, setGstin] = useState('');
  const [pan, setPan] = useState('');
  const [udyam, setUdyam] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState<Record<string, SelectedDocument>>({});
  const [submitting, setSubmitting] = useState(false);
  const [progressStep, setProgressStep] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [categoriesFailed, setCategoriesFailed] = useState(false);
  const [tenderRequirements, setTenderRequirements] = useState<TenderRequirement[]>([]);
  const [resolvedTender, setResolvedTender] = useState<any | null>(null);
  const [tenderLoading, setTenderLoading] = useState(false);
  const fileInputs = useRef<Record<string, HTMLInputElement | null>>({});
  const { t } = useTranslation();
  const requirements: TenderRequirement[] = tenderRequirements
    .filter((requirement: TenderRequirement) => requirement?.document_type)
    .map((requirement: TenderRequirement) => ({
      ...requirement,
      document_type: requirement.document_type.trim().toUpperCase(),
    }));

  const documentLabel = (documentType: string) => {
    const labels: Record<string, string> = {
      PAN: 'PAN',
      GST: 'GST Registration',
      UDYAM: 'Udyam / MSME Registration',
      EPFO: 'EPFO',
      ESIC: 'ESIC',
      ITR: 'ITR / Financial Document',
      FINANCIAL: 'ITR / Financial Document',
      EXPERIENCE: 'Experience Certificate',
    };
    return labels[documentType] || documentType.replace(/_/g, ' ');
  };

  useEffect(() => {
    setResolvedTender(selectedTender || null);
    setCategory(selectedTender?.category || '');
    setSelectedDocuments({});
    fileInputs.current = {};
    setTenderRequirements([]);
  }, [selectedTender]);

  useEffect(() => {
    if (!isOpen || !selectedTender) return;
    let cancelled = false;
    setTenderLoading(true);
    setCategoriesLoading(true);
    setCategoriesFailed(false);
    fetchTenders()
      .then((tenders) => {
        if (cancelled) return;
      const selectedTenderKeys = [
        selectedTender.id,
        selectedTender.tender_id,
        selectedTender.tenderReference,
      ].filter(Boolean).map(String);
      const matchedTender = tenders.find((tender: any) =>
        selectedTenderKeys.includes(String(tender.id))
        || selectedTenderKeys.includes(String(tender.tender_id))
      );
      const tender = matchedTender || selectedTender;
      setResolvedTender(tender);
      setCategory(tender.category || '');
      setTenderRequirements(tender.requirements || []);
      setCategories(Array.from(new Set(
          tenders
            .map((tender: any) => String(tender.category || '').trim())
            .filter(Boolean)
        )));
      })
      .catch(() => {
        if (!cancelled) {
          setResolvedTender(selectedTender);
          setCategory(selectedTender.category || '');
          setTenderRequirements(selectedTender.requirements || []);
          setCategories([]);
          setCategoriesFailed(true);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setCategoriesLoading(false);
          setTenderLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, selectedTender]);

  if (!isOpen) return null;

  const validate = () => {
    const name = vendorName.trim().replace(/\s+/g, ' ');
    if (name.length < 2 || name.length > 150 || !/[A-Za-z0-9]/.test(name) || !/^[A-Za-z0-9\s&.,'()\-]+$/.test(name)) {
      return 'Enter a valid vendor/entity name.';
    }
    if (tenderLoading) {
      return 'Loading tender requirements...';
    }
    if (!category || (resolvedTender?.category || '').toLowerCase() !== category.toLowerCase()) {
      return 'Select the category configured for this tender.';
    }
    const amount = Number(bidAmount.replace(/[₹,\s]/g, ''));
    if (!Number.isFinite(amount) || amount <= 0 || amount > 1_000_000_000_000) {
      return 'Bid amount must be a finite number greater than ₹0.';
    }
    const normalizedPan = pan.replace(/\s/g, '').toUpperCase();
    if (normalizedPan && !/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(normalizedPan)) {
      return 'Invalid PAN format. Expected 10 characters (AAAAA9999A).';
    }
    const normalizedGstin = gstin.replace(/\s/g, '').toUpperCase();
    if (normalizedGstin && !/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$/.test(normalizedGstin)) {
      return 'GSTIN must contain exactly 15 valid characters.';
    }
    if (normalizedGstin && normalizedPan && normalizedGstin.slice(2, 12) !== normalizedPan) {
      return "GSTIN's embedded PAN does not match entered PAN.";
    }
    if (udyam && !/^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$/.test(udyam.trim().toUpperCase())) {
      return 'Invalid Udyam number. Expected UDYAM-XX-00-0000000.';
    }
    const missingRequirement = requirements.find(
      (requirement) => requirement.is_mandatory !== false && !selectedDocuments[requirement.document_type]
    );
    if (missingRequirement) {
      return `Required document missing: ${documentLabel(missingRequirement.document_type)}`;
    }
    return null;
  };
  const validationError = validate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (validationError) {
      alert(validationError);
      return;
    }

    setSubmitting(true);
    try {
      setProgressStep('Creating Bid Entry in Database...');
      if (!resolvedTender?.id && !resolvedTender?.tender_id && !resolvedTender?.tenderReference) {
        throw new Error('Select a tender before submitting a bid.');
      }
      const tenderId = resolvedTender.tender_id || resolvedTender.id || resolvedTender.tenderReference;
      const bid = await createBidApi({
        tender_id: tenderId,
        vendor_name: vendorName.trim().replace(/\s+/g, ' '),
        category,
        bid_amount: bidAmount,
        gstin: gstin.toUpperCase(),
        pan: pan.toUpperCase(),
        udyam: udyam.toUpperCase()
      });

      const documentsToUpload = Object.entries(selectedDocuments);
      if (documentsToUpload.length > 0) {
        for (let i = 0; i < documentsToUpload.length; i++) {
          const [documentType, selectedDocument] = documentsToUpload[i];
          setProgressStep(`Uploading & Extracting Document ${i + 1}/${documentsToUpload.length}...`);
          await uploadBidDocument(bid.id, selectedDocument.file, documentType);
        }
      }

      setProgressStep('Running Compliance & Risk Engine Verification...');
      await triggerBidVerification(bid.id);

      setProgressStep('Completed!');
      setTimeout(() => {
        setSubmitting(false);
        onSuccess();
        onClose();
      }, 500);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Error submitting bid');
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 animate-fade-in relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-navy-50 text-navy-700 flex items-center justify-center font-bold">
            <Building className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800">Submit New Vendor Bid</h3>
            <p className="text-xs text-slate-500">Tender: {resolvedTender ? `${resolvedTender.title} (${resolvedTender.tender_id || resolvedTender.id || resolvedTender.tenderReference || 'Selected tender'})` : 'Select a tender to continue'}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Vendor Entity Name</label>
            <input
              type="text"
              required
              value={vendorName}
              onChange={(e) => setVendorName(e.target.value)}
              placeholder="e.g. Shree Lakshmi Industries Pvt Ltd"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-navy-400"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Procurement Category</label>
              <select
                value={category}
                disabled={Boolean(resolvedTender?.category)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-navy-400"
              >
                <option value="">{categoriesLoading ? t('loadingCategories') : t('selectTenderCategory')}</option>
                {(resolvedTender?.category ? [resolvedTender.category] : categories).map((categoryOption) => (
                  <option key={categoryOption} value={categoryOption}>{categoryOption}</option>
                ))}
                {!categoriesLoading && (categoriesFailed || (!resolvedTender?.category && categories.length === 0)) && (
                  <option value="" disabled>{t('noProcurementCategories')}</option>
                )}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Bid Amount (INR)</label>
              <input
                type="text"
                value={bidAmount}
                onChange={(e) => setBidAmount(e.target.value)}
                placeholder="Enter bid amount in INR"
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-navy-400"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">GSTIN</label>
              <input
                type="text"
                value={gstin}
                onChange={(e) => setGstin(e.target.value.toUpperCase())}
                placeholder="Enter GSTIN"
                className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">PAN Number</label>
              <input
                type="text"
                value={pan}
                onChange={(e) => setPan(e.target.value.toUpperCase())}
                placeholder="Enter PAN"
                className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Udyam MSME No.</label>
              <input
                type="text"
                value={udyam}
                onChange={(e) => setUdyam(e.target.value.toUpperCase())}
                placeholder="Enter Udyam number"
                className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Required Documents</label>
            {tenderLoading && (
              <p className="mt-2 text-xs text-slate-500">Loading tender requirements...</p>
            )}
            {!tenderLoading && requirements.length > 0 && (
              <div className="mt-3 rounded-xl border border-slate-200 divide-y divide-slate-100">
                <div className="px-3 py-2 flex items-center justify-between bg-slate-50">
                  <span className="text-xs font-bold text-slate-700">Document checklist</span>
                  <span className="text-xs font-semibold text-slate-500">
                    {Object.keys(selectedDocuments).length} / {requirements.length} uploaded
                  </span>
                </div>
                {requirements.map((requirement) => {
                  const documentType = requirement.document_type;
                  const selectedDocument = selectedDocuments[documentType];
                  return (
                    <div key={requirement.id || documentType} className="px-3 py-3 flex items-center gap-3">
                      {selectedDocument ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" aria-hidden="true" />
                      ) : (
                        <Circle className="w-5 h-5 text-slate-300 shrink-0" aria-hidden="true" />
                      )}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-slate-700">{documentLabel(documentType)}</p>
                          <span className={`text-[10px] font-bold uppercase ${requirement.is_mandatory === false ? 'text-slate-500' : 'text-amber-700'}`}>
                            {requirement.is_mandatory === false ? 'Optional' : 'Required'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 truncate">
                          {selectedDocument ? `${selectedDocument.file.name} - Uploaded, Pending Verification` : 'Not uploaded'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => fileInputs.current[documentType]?.click()}
                        className="shrink-0 px-3 py-1.5 text-xs font-semibold text-navy-700 bg-navy-50 rounded-lg hover:bg-navy-100"
                      >
                        {selectedDocument ? 'Replace' : `Choose ${documentLabel(documentType)} File`}
                      </button>
                      <input
                        ref={(input) => {
                          fileInputs.current[documentType] = input;
                        }}
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                        className="sr-only"
                        onChange={(event) => {
                          const file = event.currentTarget.files?.[0];
                          if (!file) return;
                          setSelectedDocuments((current) => ({
                            ...current,
                            [documentType]: { file, status: 'selected' },
                          }));
                          event.currentTarget.value = '';
                        }}
                      />
                    </div>
                  );
                })}
              </div>
            )}
            {!tenderLoading && requirements.length === 0 && resolvedTender && (
              <div className="mt-3 p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800">
                No document requirements are configured for this tender.
              </div>
            )}
          </div>

          {submitting && (
            <div className="p-3 bg-navy-50 border border-navy-200 rounded-lg text-xs text-navy-700 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-navy-600 animate-spin" />
              <span>{progressStep}</span>
            </div>
          )}

          <div className="pt-3 flex justify-end gap-2 border-t border-slate-100">
            {validationError && (
              <p className="mr-auto text-xs font-semibold text-red-600" role="alert">{validationError}</p>
            )}
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !!validationError}
              className="px-5 py-2 text-xs font-semibold text-white bg-navy-700 rounded-lg hover:bg-navy-800 disabled:opacity-50 shadow-sm"
            >
              {submitting ? 'Processing...' : 'Submit & Run Verification'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
