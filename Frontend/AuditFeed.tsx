import { Activity, CheckCircle2, XCircle, Clock3 } from 'lucide-react';
import { liveAuditFeed } from '@/data/records';

const statusMap = {
  pass: { icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-50', label: 'Pass' },
  fail: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50', label: 'Fail' },
  checking: { icon: Clock3, color: 'text-amber-500', bg: 'bg-amber-50', label: 'Checking' },
};

export default function AuditFeed() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col h-fit lg:sticky lg:top-[88px]">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-navy-50 flex items-center justify-center">
            <Activity className="w-4 h-4 text-navy-600" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">Live Audit Feed</h3>
            <p className="text-[11px] text-slate-400">Real-time system checks</p>
          </div>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-600">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse-dot"></span>
          Live
        </span>
      </div>

      {/* Feed */}
      <div className="overflow-y-auto max-h-[640px] scrollbar-navy">
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[27px] top-4 bottom-4 w-px bg-slate-100"></div>

          <div className="py-2">
            {liveAuditFeed.map((entry) => {
              const s = statusMap[entry.status];
              return (
                <div key={entry.id} className="relative flex items-start gap-3 px-5 py-3 hover:bg-slate-50 transition-colors">
                  <div className={`w-8 h-8 rounded-full ${s.bg} flex items-center justify-center shrink-0 z-10 ring-2 ring-white`}>
                    <s.icon className={`w-4 h-4 ${s.color}`} strokeWidth={2.5} />
                  </div>
                  <div className="flex-1 min-w-0 animate-slide-in">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-[12px] font-semibold text-slate-700 truncate">{entry.source}</p>
                      <span className="text-[10px] text-slate-400 font-mono shrink-0">{entry.time}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-snug mt-0.5 truncate">{entry.action}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5 truncate">{entry.vendor}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-slate-200 bg-slate-50">
        <p className="text-[11px] text-slate-400 text-center">
          Showing last 10 events · <span className="text-navy-600 font-semibold cursor-pointer hover:underline">View all</span>
        </p>
      </div>
    </div>
  );
}
