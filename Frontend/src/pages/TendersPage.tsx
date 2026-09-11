import { useEffect, useState } from 'react';
import { FileText, Plus, Pencil } from 'lucide-react';
import { fetchTenders, createTenderApi, updateTenderDeadlineApi } from '@/services/api';
import { formatINR } from '@/utils/formatINR';

export default function TendersPage({ searchTerm = '' }: { searchTerm?: string }) {
  const [tenders, setTenders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState('');
  const [tenderId, setTenderId] = useState('');
  const [category, setCategory] = useState('Industrial Machinery');
  const [turnover, setTurnover] = useState('50000000');
  const [expYears, setExpYears] = useState('3');
  const [bidDeadline, setBidDeadline] = useState('2026-11-30');
  const [editingTender, setEditingTender] = useState<any | null>(null);
  const [savingDeadline, setSavingDeadline] = useState(false);

  const formatCurrency = (value: number) => formatINR(value);

  const loadTenders = () => {
    setLoading(true);
    fetchTenders()
      .then(setTenders)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTenders();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTenderApi({
        tender_id: tenderId || `CPCL-2026-${Math.floor(Math.random()*100)}`,
        title,
        department: 'CPCL Procurement Wing',
        category,
        bid_deadline: bidDeadline,
        minimum_turnover_inr: parseFloat(turnover),
        minimum_experience_years: parseInt(expYears),
        requirements: [
          { document_type: 'GST', is_mandatory: true, description: 'Active GSTIN' },
          { document_type: 'PAN', is_mandatory: true, description: 'PAN Card' },
          { document_type: 'UDYAM', is_mandatory: true, description: 'Udyam Registration' },
          { document_type: 'EPFO', is_mandatory: true, description: 'EPFO Registration' }
        ]
      });
      setShowModal(false);
      loadTenders();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Error creating tender');
    }
  };

  const handleDeadlineSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTender) return;
    setSavingDeadline(true);
    try {
      await updateTenderDeadlineApi(editingTender.id, editingTender.bid_deadline);
      setEditingTender(null);
      loadTenders();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Error updating tender deadline');
    } finally {
      setSavingDeadline(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Tender Management & Requirement Rules</h2>
          <p className="text-xs text-slate-500">Configure tender-specific eligibility rules and mandatory document requirements</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-navy-700 hover:bg-navy-800 text-white rounded-lg text-xs font-bold shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Create New Tender
        </button>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border">
            <h3 className="text-base font-bold text-slate-800 mb-4">Create Procurement Tender</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-xs font-bold uppercase mb-1 text-slate-700">Tender ID</label>
                <input
                  type="text"
                  required
                  value={tenderId}
                  onChange={(e) => setTenderId(e.target.value)}
                  placeholder="CPCL-2026-IND-99"
                  className="w-full p-2 text-sm bg-slate-50 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1 text-slate-700">Tender Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Procurement of Valves and Pumps"
                  className="w-full p-2 text-sm bg-slate-50 border rounded-lg"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold uppercase mb-1 text-slate-700">Category</label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full p-2 text-sm bg-slate-50 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase mb-1 text-slate-700">Min Turnover (INR)</label>
                  <input
                    type="number"
                    value={turnover}
                    onChange={(e) => setTurnover(e.target.value)}
                    className="w-full p-2 text-sm bg-slate-50 border rounded-lg"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1 text-slate-700">Bid Deadline</label>
                <input
                  type="date"
                  required
                  value={bidDeadline}
                  onChange={(e) => setBidDeadline(e.target.value)}
                  className="w-full p-2 text-sm bg-slate-50 border rounded-lg"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-xs text-slate-600 bg-slate-100 rounded-lg">Cancel</button>
                <button type="submit" className="px-4 py-2 text-xs font-bold text-white bg-navy-700 rounded-lg">Create Tender</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tenders
          .filter(t => 
            !searchTerm || 
            t.tender_id.toLowerCase().includes(searchTerm.toLowerCase()) || 
            t.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
            t.category.toLowerCase().includes(searchTerm.toLowerCase())
          )
          .map((t) => {
          const requirementChips = (t.requirements || []).filter((req: any) => req.is_mandatory).slice(0, 8);
          const estimatedValue = Number(t.estimated_value ?? 0);
          return (
            <div key={t.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="text-[11px] font-mono text-navy-600 font-bold bg-navy-50 px-2 py-0.5 rounded">{t.tender_id}</span>
                  <h4 className="text-base font-bold text-slate-800 mt-1">{t.title}</h4>
                </div>
                <span className="text-xs font-semibold px-2 py-1 bg-emerald-50 text-emerald-600 rounded-md">ACTIVE</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 mb-4 bg-slate-50 p-3 rounded-lg">
                <div><span className="font-semibold">Category:</span> {t.category}</div>
                <div className="flex items-center gap-1">
                  <span><span className="font-semibold">Deadline:</span> {t.bid_deadline}</span>
                  <button type="button" title={`Edit deadline for ${t.tender_id}`} onClick={() => setEditingTender({ ...t })} className="text-indigo-600 hover:text-indigo-800">
                    <Pencil className="w-3 h-3" />
                  </button>
                </div>
                <div><span className="font-semibold">Estimated Value:</span> {formatCurrency(estimatedValue)}</div>
                <div><span className="font-semibold">Min Experience:</span> {t.minimum_experience_years} Years</div>
              </div>

              <div className="text-xs">
                <p className="font-bold text-slate-700 mb-2">Mandatory Requirement Rules:</p>
                <div className="flex flex-wrap gap-1.5">
                  {requirementChips.length > 0 ? (
                    requirementChips.map((req: any) => (
                      <span key={req.id || req.document_type} className="px-2 py-0.5 bg-slate-100 text-slate-700 font-semibold rounded">
                        {req.document_type}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500">No mandatory requirements defined.</span>
                  )}
                </div>

                {editingTender && (
                  <div className="fixed inset-0 bg-slate-900/60 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl max-w-sm w-full p-6 shadow-xl border">
                      <h3 className="text-base font-bold text-slate-800 mb-1">Edit Tender Date</h3>
                      <p className="text-xs text-slate-500 mb-4">{editingTender.tender_id} · {editingTender.title}</p>
                      <form onSubmit={handleDeadlineSave} className="space-y-4">
                        <div>
                          <label className="block text-xs font-bold uppercase mb-1 text-slate-700">Bid Deadline</label>
                          <input type="date" required value={editingTender.bid_deadline || ''} onChange={(e) => setEditingTender({ ...editingTender, bid_deadline: e.target.value })} className="w-full p-2 text-sm bg-slate-50 border rounded-lg" />
                        </div>
                        <div className="flex justify-end gap-2">
                          <button type="button" onClick={() => setEditingTender(null)} className="px-4 py-2 text-xs text-slate-600 bg-slate-100 rounded-lg">Cancel</button>
                          <button disabled={savingDeadline} type="submit" className="px-4 py-2 text-xs font-bold text-white bg-navy-700 rounded-lg">{savingDeadline ? 'Saving...' : 'Save Date'}</button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
