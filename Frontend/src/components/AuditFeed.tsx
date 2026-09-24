import { useEffect, useState } from 'react';
import { Activity, CheckCircle2, XCircle, Clock3 } from 'lucide-react';
import { fetchAuditEvents } from '@/services/api';
import { translateAuditAction, translateAuditSource, useTranslation } from '@/i18n';

const statusMap = {
  pass: { icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-50' },
  fail: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50' },
  checking: { icon: Clock3, color: 'text-amber-500', bg: 'bg-amber-50' },
};

export default function AuditFeed() {
  const { t } = useTranslation();
  const [feed, setFeed] = useState<any[]>([]);

  const loadFeed = () => {
    fetchAuditEvents()
      .then((data) => setFeed(data))
      .catch(() => {
        setFeed([]);
      });
  };

  useEffect(() => {
    loadFeed();
    const interval = setInterval(loadFeed, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col h-fit lg:sticky lg:top-[88px]">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-navy-50 flex items-center justify-center">
            <Activity className="w-4 h-4 text-navy-600" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">{t('liveAuditFeed')}</h3>
            <p className="text-[11px] text-slate-400">{t('realTimeChecks')}</p>
          </div>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-600">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse-dot"></span>
          {t('live')}
        </span>
      </div>

      {/* Feed */}
      <div className="overflow-y-auto max-h-[640px] scrollbar-navy">
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[27px] top-4 bottom-4 w-px bg-slate-100"></div>

          <div className="py-2">
            {feed.length === 0 ? (
              <div className="px-5 py-8 text-sm text-slate-500">{t('noAuditEvents')}</div>
            ) : (
              feed.map((entry, idx) => {
                const s = statusMap[entry.status as keyof typeof statusMap] || statusMap.pass;
                return (
                  <div key={entry.id || idx} className="relative flex items-start gap-3 px-5 py-3 hover:bg-slate-50 transition-colors">
                    <div className={`w-8 h-8 rounded-full ${s.bg} flex items-center justify-center shrink-0 z-10 ring-2 ring-white`}>
                      <s.icon className={`w-4 h-4 ${s.color}`} strokeWidth={2.5} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[12px] font-semibold text-slate-700 truncate">{translateAuditSource(entry.source, t)}</p>
                        <span className="text-[10px] text-slate-400 font-mono shrink-0">{entry.timestamp}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 leading-snug mt-0.5 truncate">{translateAuditAction(entry.action || entry.label, t)}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5 truncate">{entry.vendor}</p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-slate-200 bg-slate-50">
        <p className="text-[11px] text-slate-400 text-center">
          {t('showingLatestEvents')} · <span className="text-navy-600 font-semibold cursor-pointer hover:underline">{t('viewFullAuditTrail')}</span>
        </p>
      </div>
    </div>
  );
}
