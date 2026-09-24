import { Settings, ShieldCheck, Database, Cpu } from 'lucide-react';
import { useTranslation } from '@/i18n';

export default function SettingsPage() {
  const { t } = useTranslation();
  return (
    <div className="p-6 max-w-3xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
          <Settings className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800">{t('systemConfiguration')}</h2>
          <p className="text-xs text-slate-500">{t('operationalSettings')}</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2 mb-2">
            <ShieldCheck className="w-4 h-4 text-navy-600" />
            {t('governmentVerificationMode')}
          </h3>
          <p className="text-xs text-slate-500 mb-3">
            {t('simulatedVerificationDescription')}
          </p>
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700">
            {t('modeSimulated')}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2 mb-2">
            <Database className="w-4 h-4 text-navy-600" />
            {t('dataStore')}
          </h3>
          <p className="text-xs text-slate-500 mb-3">
            {t('recordsPersisted')}
          </p>
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700">
            Database: SQLite / bharatsetu.db
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2 mb-2">
            <Cpu className="w-4 h-4 text-navy-600" />
            {t('ocrProcessingEngine')}
          </h3>
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700">
            {t('ocrEnabled')}
          </div>
        </div>
      </div>
    </div>
  );
}
