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
} from 'lucide-react';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', active: true },
  { icon: FileSearch, label: 'Verification Queue', badge: '6' },
  { icon: ClipboardCheck, label: 'Reviewed Bids' },
  { icon: Building2, label: 'Vendor Registry' },
  { icon: AlertTriangle, label: 'Flagged Cases', badge: '2' },
  { icon: History, label: 'Audit History' },
];

const bottomItems = [
  { icon: Settings, label: 'Settings' },
  { icon: HelpCircle, label: 'Help & Support' },
  { icon: LogOut, label: 'Sign Out' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-navy-950 text-white flex flex-col h-screen sticky top-0 shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-navy-400 to-navy-600 flex items-center justify-center shadow-lg">
            <ShieldCheck className="w-6 h-6 text-white" strokeWidth={2.2} />
          </div>
          <div>
            <h1 className="font-bold text-[15px] leading-tight tracking-tight">BharatSetu</h1>
            <p className="text-[11px] text-navy-300 font-medium">Officer Console</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto scrollbar-navy">
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-navy-400">
          Procurement
        </p>
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.label}>
              <button
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                  item.active
                    ? 'bg-navy-600 text-white shadow-md'
                    : 'text-navy-200 hover:bg-navy-800 hover:text-white'
                }`}
              >
                <item.icon className="w-[18px] h-[18px] shrink-0" strokeWidth={2} />
                <span className="flex-1 text-left">{item.label}</span>
                {item.badge && (
                  <span
                    className={`text-[11px] font-bold px-1.5 py-0.5 rounded-md ${
                      item.active ? 'bg-white/20' : 'bg-navy-700 text-navy-200'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Bottom */}
      <div className="px-3 py-3 border-t border-white/10">
        <ul className="space-y-1">
          {bottomItems.map((item) => (
            <li key={item.label}>
              <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-navy-200 hover:bg-navy-800 hover:text-white transition-all duration-150">
                <item.icon className="w-[18px] h-[18px] shrink-0" strokeWidth={2} />
                <span>{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Officer card */}
      <div className="px-3 pb-4">
        <div className="bg-navy-800 rounded-xl p-3 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-navy-950 font-bold text-sm shrink-0">
            AK
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">Anil Kumar</p>
            <p className="text-[11px] text-navy-300 truncate">Procurement Officer · L2</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
