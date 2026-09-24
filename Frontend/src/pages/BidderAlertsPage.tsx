import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { ShieldAlert, AlertTriangle, Info } from 'lucide-react';
import { useTranslation } from '@/i18n';

export default function BidderAlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    api.get('/bidder/alerts')
      .then(res => setAlerts(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6">{t('loadingAlerts')}</div>;

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-slate-800 mb-6">{t('smartComplianceAlerts')}</h2>
      
      {alerts.length === 0 ? (
        <div className="bg-emerald-50 border border-emerald-200 p-6 rounded-xl flex items-center gap-3">
          <Info className="text-emerald-600 w-6 h-6" />
          <p className="text-emerald-800 font-medium">{t('allDocumentsCompliant')}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert: any) => (
            <div key={alert.id} className="bg-white border border-red-200 shadow-sm p-4 rounded-xl flex gap-4">
              <div className="mt-1 bg-red-50 text-red-600 p-2 rounded-lg shrink-0">
                {alert.severity === 'high' ? <ShieldAlert className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
              </div>
              <div>
                <h4 className="font-bold uppercase text-xs mb-1 tracking-wider text-red-600">
                  {alert.type}
                </h4>
                <p className="text-sm text-slate-600">{alert.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
