import { useEffect, useState } from 'react';
import { fetchTenders } from '@/services/api';
import { formatINR } from '@/utils/formatINR';

export default function BidderTendersPage({ searchTerm = '', onOpenBid }: { searchTerm?: string, onOpenBid: (tender: any) => void }) {
  const [tenders, setTenders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const formatCurrency = (value: number) => formatINR(value);

  useEffect(() => {
    fetchTenders()
      .then(setTenders)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-800">Tender Finder</h2>
        <p className="text-xs text-slate-500">Find and apply to available government tenders.</p>
      </div>

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
                  <span className="text-[11px] font-mono text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded">{t.tender_id}</span>
                  <h4 className="text-base font-bold text-slate-800 mt-1">{t.title}</h4>
                </div>
                <span className="text-xs font-semibold px-2 py-1 bg-emerald-50 text-emerald-600 rounded-md">ACTIVE</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 mb-4 bg-slate-50 p-3 rounded-lg">
                <div><span className="font-semibold">Category:</span> {t.category}</div>
                <div><span className="font-semibold">Deadline:</span> {t.bid_deadline}</div>
                <div><span className="font-semibold">Estimated Value:</span> {formatCurrency(estimatedValue)}</div>
                <div><span className="font-semibold">Min Experience:</span> {t.minimum_experience_years} Years</div>
              </div>

              <div className="text-xs mb-4">
                <p className="font-bold text-slate-700 mb-2">Required Documents:</p>
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
              </div>
              
              <button 
                onClick={() => onOpenBid(t)}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold transition-all"
              >
                Apply for Tender
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
