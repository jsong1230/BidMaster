import Sidebar from '@/components/layout/Sidebar';
import { ToastContainer } from '@/components/ui/Toast';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-neutral-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
}
