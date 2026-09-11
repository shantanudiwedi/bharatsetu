import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import MetricsBar from '@/components/MetricsBar';
import VerificationTable from '@/components/VerificationTable';
import AuditFeed from '@/components/AuditFeed';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <Header />
        <main className="flex-1 p-8">
          <div className="flex gap-6">
            <div className="flex-1 min-w-0">
              <MetricsBar />
              <VerificationTable />
            </div>
            <div className="hidden xl:block w-[340px] shrink-0">
              <AuditFeed />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
