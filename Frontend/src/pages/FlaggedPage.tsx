import { useEffect, useState } from 'react';
import { AlertTriangle, ShieldX, UserCog } from 'lucide-react';
import { fetchBids, BidRecord } from '@/services/api';

export default function FlaggedPage({ searchTerm = '' }: { searchTerm?: string }) {
  const [bids, setBids] = useState<BidRecord[]>([]);

  useEffect(() => {
    fetchBids({ status_filter: 'FLAGGED', search: searchTerm })
      .then(setBids)
      .catch((e) => console.error(e));
  }, [searchTerm]);

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800">Flagged High Risk Cases</h2>
          <p className="text-xs text-slate-500">Dedicated investigation portal for bidders with address mismatches, missing mandatory documents, or failed government checks</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {bids.map((b) => (
          <div key={b.id} className="bg-white rounded-xl border border-red-200 p-5 shadow-sm">
            <div className="flex items-start justify-between mb-3">
              <div>
                <span className="text-[11px] font-mono text-red-600 font-bold bg-red-50 px-2 py-0.5 rounded">{b.id}</span>
                <h4 className="text-base font-bold text-slate-800 mt-1">{b.vendorName}</h4>
              </div>
              <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 rounded-full">
                <ShieldX className="w-3.5 h-3.5" />
                Score: {b.risk_score} HIGH
              </span>
            </div>

            <p className="text-xs text-slate-600 mb-3 bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="font-bold">Primary Findings:</span> {b.aiSummary}
            </p>

            <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
              <span className="text-slate-400">Bid Amount: <strong className="text-slate-700">{b.bidAmount}</strong></span>
              <span className="text-amber-700 font-semibold flex items-center gap-1">
                <UserCog className="w-3.5 h-3.5" />
                Senior Officer Review Assigned
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
