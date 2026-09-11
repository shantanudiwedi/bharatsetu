import { Search, Bell, Calendar, ChevronDown } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-20">
      <div>
        <div className="flex items-center gap-2 text-[12px] text-slate-400 font-medium mb-1">
          <span>Verification</span>
          <span className="text-slate-300">/</span>
          <span className="text-navy-700">Procurement Queue</span>
        </div>
        <h2 className="text-xl font-bold text-slate-800 tracking-tight">Bid Verification Dashboard</h2>
      </div>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search vendor, bid ID, GSTIN..."
            className="w-64 pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-navy-400 focus:border-transparent transition-all"
          />
        </div>

        {/* Date */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600 font-medium">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span>30 Aug 2026</span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors">
          <Bell className="w-5 h-5 text-slate-600" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white"></span>
        </button>

        {/* Divider */}
        <div className="w-px h-8 bg-slate-200"></div>

        {/* Session */}
        <div className="flex items-center gap-2 text-sm">
          <div className="text-right hidden sm:block">
            <p className="font-semibold text-slate-700 leading-tight">Session Active</p>
            <p className="text-[11px] text-emerald-600 font-medium flex items-center gap-1 justify-end">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse-dot"></span>
              Secure Channel
            </p>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400" />
        </div>
      </div>
    </header>
  );
}
