import { useEffect, useState } from 'react';
import { Building2, Search, CheckCircle2, ShieldAlert } from 'lucide-react';
import { fetchVendors } from '@/services/api';

export default function VendorsPage({ searchTerm = '' }: { searchTerm?: string }) {
  const [vendors, setVendors] = useState<any[]>([]);

  useEffect(() => {
    fetchVendors()
      .then(setVendors)
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Vendor Compliance Registry</h2>
          <p className="text-xs text-slate-500">Official vendor profiles, GSTIN/PAN records, and past verification history</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr_1fr] px-6 py-3 bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-400 uppercase">
          <div>Vendor Legal Name</div>
          <div>GSTIN</div>
          <div>PAN</div>
          <div>Udyam No.</div>
          <div>Address / Location</div>
        </div>

        <div className="divide-y divide-slate-100">
          {vendors
            .filter(v => 
              !searchTerm || 
              v.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
              (v.gstin && v.gstin.toLowerCase().includes(searchTerm.toLowerCase())) ||
              (v.pan && v.pan.toLowerCase().includes(searchTerm.toLowerCase())) ||
              (v.udyam && v.udyam.toLowerCase().includes(searchTerm.toLowerCase()))
            )
            .map((v) => (
            <div key={v.id} className="grid grid-cols-[1.5fr_1fr_1fr_1fr_1fr] px-6 py-4 items-center text-xs">
              <div className="font-bold text-slate-800 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-navy-600 shrink-0" />
                <span>{v.name}</span>
              </div>
              <div className="font-mono text-slate-600">{v.gstin || 'N/A'}</div>
              <div className="font-mono text-slate-600">{v.pan || 'N/A'}</div>
              <div className="font-mono text-slate-600">{v.udyam || 'N/A'}</div>
              <div className="text-slate-500 truncate">{v.address || 'Registered Address'}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
