import { useEffect, useState } from 'react';
import { X, Upload, Building, FileText, CheckCircle2 } from 'lucide-react';
import { createBidApi, uploadBidDocument, triggerBidVerification } from '@/services/api';

interface BidSubmissionModalProps {
  isOpen: boolean;
  selectedTender?: any | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function BidSubmissionModal({ isOpen, selectedTender, onClose, onSuccess }: BidSubmissionModalProps) {
  const [vendorName, setVendorName] = useState('');
  const [category, setCategory] = useState('');
  const [bidAmount, setBidAmount] = useState('');
  const [gstin, setGstin] = useState('');
  const [pan, setPan] = useState('');
  const [udyam, setUdyam] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [progressStep, setProgressStep] = useState<string>('');

  useEffect(() => {
    setCategory(selectedTender?.category || '');
  }, [selectedTender]);

  if (!isOpen) return null;

  const validate = () => {
    const name = vendorName.trim().replace(/\s+/g, ' ');
    if (name.length < 2 || name.length > 150 || !/[A-Za-z0-9]/.test(name) || !/^[A-Za-z0-9\s&.,'()\-]+$/.test(name)) {
      return 'Enter a valid vendor/entity name.';
    }
    if (!category || (selectedTender?.category || '').toLowerCase() !== category.toLowerCase()) {
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
      if (!selectedTender?.id && !selectedTender?.tender_id && !selectedTender?.tenderReference) {
        throw new Error('Select a tender before submitting a bid.');
      }
      const tenderId = selectedTender.tender_id || selectedTender.id || selectedTender.tenderReference;
      const bid = await createBidApi({
        tender_id: tenderId,
        vendor_name: vendorName.trim().replace(/\s+/g, ' '),
        category,
        bid_amount: bidAmount,
        gstin: gstin.toUpperCase(),
        pan: pan.toUpperCase(),
        udyam: udyam.toUpperCase()
      });

      if (files.length > 0) {
        for (let i = 0; i < files.length; i++) {
          setProgressStep(`Uploading & Extracting Document ${i + 1}/${files.length}...`);
          await uploadBidDocument(bid.id, files[i]);
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
            <p className="text-xs text-slate-500">Tender: {selectedTender ? `${selectedTender.title} (${selectedTender.tender_id || selectedTender.id || selectedTender.tenderReference || 'Selected tender'})` : 'Select a tender to continue'}</p>
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
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-navy-400"
              >
                <option value="">Select tender category</option>
                {selectedTender?.category && <option value={selectedTender.category}>{selectedTender.category}</option>}
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
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Upload Compliance Documents</label>
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-4 text-center hover:bg-slate-50 transition-colors">
              <Upload className="w-6 h-6 text-slate-400 mx-auto mb-2" />
              <p className="text-xs text-slate-600 font-medium">Drag & drop files or click to browse</p>
              <p className="text-[11px] text-slate-400 mt-1">Supported: PDF, PNG, JPG (GST, PAN, Udyam, EPFO certificates)</p>
              <input
                type="file"
                multiple
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => {
                  if (e.target.files) {
                    setFiles(Array.from(e.target.files));
                  }
                }}
                className="mt-2 text-xs text-slate-500"
              />
            </div>
            {files.length > 0 && (
              <div className="mt-2 text-xs text-emerald-600 font-semibold flex items-center gap-1">
                <FileText className="w-3.5 h-3.5" />
                {files.length} document(s) selected
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
