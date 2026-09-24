import { useEffect, useState } from 'react';
import { ClipboardList, CheckCircle2, Clock, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import { fetchDashboardMetrics, DashboardMetrics } from '@/services/api';
import { useTranslation } from '@/i18n';

const colorMap: Record<string, { bg: string; text: string; ring: string }> = {
  navy: { bg: 'bg-navy-50', text: 'text-navy-700', ring: 'ring-navy-100' },
  emerald: { bg: 'bg-emerald-50', text: 'text-emerald-600', ring: 'ring-emerald-100' },
  amber: { bg: 'bg-amber-50', text: 'text-amber-600', ring: 'ring-amber-100' },
  red: { bg: 'bg-red-50', text: 'text-red-600', ring: 'ring-red-100' },
};

export default function MetricsBar() {
  const { t } = useTranslation();
  const [data, setData] = useState<DashboardMetrics | null>(null);

  useEffect(() => {
    fetchDashboardMetrics()
      .then(setData)
      .catch(() => {
        setData(null);
      });
  }, []);

  const metrics = data
    ? [
        {
          label: t('pendingReview'),
          value: String(data.pending_review_count),
          sub: t('awaitingOfficerDecision'),
          icon: ClipboardList,
          color: 'navy',
          trend: null,
        },
        {
          label: t('approvedBids'),
          value: String(data.approved_today_count),
          sub: t('complianceVerified'),
          icon: CheckCircle2,
          color: 'emerald',
          trend: { dir: 'up', val: '+3' },
        },
        {
          label: t('averageVerificationTime'),
          value: data.avg_verification_time,
          sub: t('endToEndProcessing'),
          icon: Clock,
          color: 'amber',
          trend: { dir: 'down', val: '-8s' },
        },
        {
          label: t('flaggedCases'),
          value: String(data.flagged_cases_count),
          sub: t('requireEscalation'),
          icon: AlertTriangle,
          color: 'red',
          trend: null,
        },
      ]
    : [];

  if (!data) {
    return (
      <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        {t('metricsUnavailable')}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {metrics.map((m) => {
        const c = colorMap[m.color];
        return (
          <div
            key={m.label}
            className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md hover:border-slate-300 transition-all duration-200 group"
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`w-11 h-11 rounded-lg ${c.bg} ${c.text} flex items-center justify-center ring-1 ${c.ring}`}>
                <m.icon className="w-[22px] h-[22px]" strokeWidth={2} />
              </div>
              {m.trend && (
                <span
                  className={`flex items-center gap-0.5 text-xs font-semibold px-2 py-1 rounded-md ${
                    m.trend.dir === 'up' ? 'bg-emerald-50 text-emerald-600' : 'bg-navy-50 text-navy-600'
                  }`}
                >
                  {m.trend.dir === 'up' ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {m.trend.val}
                </span>
              )}
            </div>
            <p className="text-[13px] text-slate-400 font-medium mb-1">{m.label}</p>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-bold text-slate-800 tracking-tight">{m.value}</p>
            </div>
            <p className="text-[12px] text-slate-400 mt-1">{m.sub}</p>
          </div>
        );
      })}
    </div>
  );
}
