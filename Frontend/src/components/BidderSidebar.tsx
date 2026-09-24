import {
  ShieldCheck,
  LayoutDashboard,
  FileSearch,
  ClipboardCheck,
  Building2,
  AlertTriangle,
  History,
  Settings,
  HelpCircle,
  LogOut,
  PlusCircle,
  FileText,
  Bell
} from 'lucide-react';
import { useTranslation } from '@/i18n';

interface SidebarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  onOpenNewBid: () => void;
  currentUser: any;
}

const navItems = [
  { id: 'dashboard', icon: LayoutDashboard, key: 'dashboard' },
  { id: 'tenders', icon: FileSearch, key: 'tenderFinder' },
  { id: 'bids', icon: ClipboardCheck, key: 'myBids' },
  { id: 'documents', icon: FileText, key: 'myDocuments' },
  { id: 'alerts', icon: AlertTriangle, key: 'complianceAlerts' },
];

const bottomItems = [
  { id: 'support', icon: HelpCircle, key: 'aiSupport' },
  { id: 'settings', icon: Settings, key: 'settings' },
];

export default function BidderSidebar({ currentTab, onTabChange, onOpenNewBid, currentUser }: SidebarProps) {
  const { t } = useTranslation();
  const translatedLabels: Record<string, string> = {
    dashboard: t('dashboard'),
    support: t('help'),
    tenders: t('tenderFinder'),
    bids: t('myBids'),
    documents: t('myDocuments'),
    alerts: t('complianceAlerts'),
    settings: t('settings'),
    logout: t('logout'),
  };
  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col h-screen sticky top-0 shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center shadow-lg">
            <Building2 className="w-6 h-6 text-white" strokeWidth={2.2} />
          </div>
          <div>
            <h1 className="font-bold text-[15px] leading-tight tracking-tight">BharatSetu</h1>
            <p className="text-[11px] text-indigo-300 font-medium">{t('bidderPortal')}</p>
          </div>
        </div>
      </div>

      {/* New Bid Action */}
      <div className="px-3 pt-4 pb-2">
        <button
          onClick={onOpenNewBid}
          className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-md"
        >
          <PlusCircle className="w-4 h-4" />
          <span>{t('uploadDocuments')} / Bid</span>
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-2 overflow-y-auto scrollbar-navy">
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          {t('vendorModules')}
        </p>
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                    isActive
                      ? 'bg-slate-800 text-white shadow-md border border-slate-700'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <item.icon className="w-[18px] h-[18px] shrink-0" strokeWidth={2} />
                  <span className="flex-1 text-left">{translatedLabels[item.id] || item.key}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Bottom */}
      <div className="px-3 py-3 border-t border-white/10">
        <ul className="space-y-1">
          {bottomItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onTabChange(item.id)}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-all duration-150"
              >
                <item.icon className="w-[18px] h-[18px] shrink-0" strokeWidth={2} />
                <span>{translatedLabels[item.id] || item.key}</span>
              </button>
            </li>
          ))}
          <li>
            <button
                onClick={() => onTabChange('logout')}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-red-500/20 hover:text-red-400 transition-all duration-150"
              >
                <LogOut className="w-[18px] h-[18px] shrink-0" strokeWidth={2} />
                <span>{t('logout')}</span>
            </button>
          </li>
        </ul>
      </div>

      {/* User card */}
      <div className="px-3 pb-4">
        <div className="bg-slate-800 rounded-xl p-3 flex items-center gap-3 border border-slate-700">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
            {currentUser?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">{currentUser?.full_name || t('vendor')}</p>
            <p className="text-[11px] text-slate-400 truncate">{currentUser?.department || t('vendor')}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
