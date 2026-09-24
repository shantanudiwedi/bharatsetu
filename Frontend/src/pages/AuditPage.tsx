import { useEffect, useState } from 'react';
import { History, CheckCircle2, XCircle, Clock3 } from 'lucide-react';
import { fetchAuditEvents } from '@/services/api';
import { translateAuditAction, translateAuditSource, useTranslation } from '@/i18n';

export default function AuditPage({ searchTerm = '' }: { searchTerm?: string }) {
  const { t } = useTranslation();
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    fetchAuditEvents()
      .then(setEvents)
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Immutable System Audit Log</h2>
          <p className="text-xs text-slate-500">Chronological security and compliance event ledger recorded during verification runs</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="grid grid-cols-[120px_1.5fr_2fr_1.5fr_100px] px-6 py-3 bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-400 uppercase">
          <div>Time</div>
          <div>Event Source</div>
          <div>Action Executed</div>
          <div>Vendor Entity</div>
          <div>Status</div>
        </div>

        <div className="divide-y divide-slate-100">
          {events
            .filter(e => 
              !searchTerm || 
              (e.vendor && e.vendor.toLowerCase().includes(searchTerm.toLowerCase())) ||
              (e.source && e.source.toLowerCase().includes(searchTerm.toLowerCase())) ||
              (e.action && e.action.toLowerCase().includes(searchTerm.toLowerCase())) ||
              (e.label && e.label.toLowerCase().includes(searchTerm.toLowerCase()))
            )
            .map((e) => (
            <div key={e.id} className="grid grid-cols-[120px_1.5fr_2fr_1.5fr_100px] px-6 py-3.5 items-center text-xs">
              <div className="font-mono text-slate-400">{e.timestamp}</div>
              <div className="font-semibold text-slate-700">{translateAuditSource(e.source, t)}</div>
              <div className="text-slate-600">{translateAuditAction(e.action || e.label, t)}</div>
              <div className="font-medium text-slate-800">{e.vendor || 'System'}</div>
              <div>
                <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded ${
                  e.status === 'pass' ? 'bg-emerald-50 text-emerald-600' : e.status === 'fail' ? 'bg-red-50 text-red-600' : 'bg-amber-50 text-amber-600'
                }`}>
                  {e.status === 'pass' ? t('pass') : e.status === 'fail' ? t('fail') : t('checking')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
