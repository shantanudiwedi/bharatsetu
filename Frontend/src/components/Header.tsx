import { useState, useEffect, useRef, useMemo } from 'react';
import { Search, Bell, Calendar, ChevronDown, ShieldAlert, Check, CheckCircle2 } from 'lucide-react';
import { fetchNotifications, markNotificationRead, markAllNotificationsRead, fetchUnreadNotificationCount } from '@/services/api';
import { LanguageSelector, translateNotification, useTranslation } from '@/i18n';

interface HeaderProps {
  searchTerm?: string;
  onSearchChange?: (val: string) => void;
  currentUser?: any;
}

export default function Header({ searchTerm = '', onSearchChange, currentUser }: HeaderProps) {
  const { t } = useTranslation();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [now, setNow] = useState(() => new Date());
  const dropdownRef = useRef<HTMLDivElement>(null);

  const loadNotifications = async () => {
    if (!localStorage.getItem('token')) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }
    try {
      const data = await fetchNotifications();
      setNotifications(data);
      const countData = await fetchUnreadNotificationCount();
      setUnreadCount(countData.unread_count || 0);
    } catch (e) {
      console.error('Failed to load notifications');
    }
  };

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 15000); // poll every 15s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const clock = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(clock);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      loadNotifications();
    } catch (e) {
      console.error('Failed to mark read');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      loadNotifications();
    } catch (e) {
      console.error('Failed to mark all read');
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 px-8 py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 sticky top-0 z-20">
      <div>
        <div className="flex items-center gap-2 text-[12px] text-slate-400 font-medium mb-1">
          <span>{t('verificationEngine')}</span>
          <span className="text-slate-300">/</span>
          <span className="text-navy-700">{t('procurementOperations')}</span>
        </div>
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">{currentUser?.role === 'BIDDER' ? t('dashboard') : t('bidVerificationDashboard')}</h2>
          {/* SIMULATED GOVT VERIFICATION BANNER */}
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-700 text-[11px] font-semibold">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            {t('simulatedGovernmentVerification')}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <LanguageSelector />
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            placeholder={`${t('vendor')}, bid ID, GSTIN...`}
            className="w-64 pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-navy-400 focus:border-transparent transition-all"
          />
        </div>

        {/* Date */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600 font-medium">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span>
            {now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
            {' · '}
            {now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        </div>

        {/* Notifications */}
        <div className="relative" ref={dropdownRef}>
          <button 
            className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors"
            onClick={() => { setShowDropdown(!showDropdown); if (!showDropdown) loadNotifications(); }}
          >
            <Bell className="w-5 h-5 text-slate-600" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 flex items-center justify-center text-[10px] font-bold text-white bg-red-500 rounded-full ring-2 ring-white">
                {unreadCount}
              </span>
            )}
          </button>

          {showDropdown && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                <h3 className="font-bold text-slate-800 text-sm">{t('notifications')}</h3>
                {unreadCount > 0 && (
                  <button 
                    onClick={handleMarkAllRead}
                    className="text-[11px] font-medium text-navy-600 hover:text-navy-700 hover:underline"
                  >
                    {t('markAllRead')}
                  </button>
                )}
              </div>
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-slate-500">
                    {t('noNotifications')}
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div 
                      key={n.id} 
                      className={`px-4 py-3 flex gap-3 border-b border-slate-50 last:border-0 ${!n.is_read ? 'bg-navy-50/30' : 'bg-white'}`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                                <p className="text-sm font-semibold text-slate-800 truncate">{translateNotification(n, t).title}</p>
                          <span className="text-[10px] text-slate-400 whitespace-nowrap ml-2">
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 leading-snug">{translateNotification(n, t).message}</p>
                      </div>
                      {!n.is_read && (
                        <button 
                          onClick={() => handleMarkRead(n.id)}
                          className="shrink-0 w-6 h-6 flex items-center justify-center rounded-full hover:bg-slate-100 text-slate-400 hover:text-navy-600 transition-colors"
                          title={t('markAsRead')}
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="w-px h-8 bg-slate-200"></div>

        {/* Session */}
        <div className="flex items-center gap-2 text-sm">
          <div className="text-right hidden sm:block">
            <p className="font-semibold text-slate-700 leading-tight">
              {currentUser?.full_name || ''}
            </p>
            <p className="text-[11px] text-emerald-600 font-medium flex items-center gap-1 justify-end">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse-dot"></span>
              {currentUser?.role === 'BIDDER' ? 'Vendor Portal' : (currentUser?.department || '')}
            </p>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400" />
        </div>
      </div>
    </header>
  );
}
