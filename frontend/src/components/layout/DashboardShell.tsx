import { ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useSidebar } from '@/context/useSidebar';
import Sidebar from '@/components/Sidebar/Sidebar';
import MobileHeader from './MobileHeader';
import RightRail from './RightRail';

interface DashboardShellProps {
  children: ReactNode;
}

const DashboardShell = ({ children }: DashboardShellProps) => {
  const { isCollapsed } = useSidebar();
  const { pathname } = useLocation();
  const showRightRail = pathname === '/';

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />

      <div
        className={cn(
          'transition-all duration-300',
          isCollapsed ? 'ml-0' : 'ml-64 max-lg:ml-0',
        )}
      >
        <MobileHeader />
        <div className="w-full px-4 py-6 lg:px-[var(--spacing-sides)] lg:py-8">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:gap-[var(--spacing-gap)]">
            <main
              className={cn(
                'col-span-1',
                showRightRail ? 'lg:col-span-9' : 'lg:col-span-12',
              )}
            >
              <div className="space-y-6 pt-4 lg:pt-[var(--content-top-offset)]">
                {children}
              </div>
            </main>
            {showRightRail && (
              <aside className="col-span-3 hidden lg:block">
                <RightRail />
              </aside>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardShell;
