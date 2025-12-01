import { useEffect, useState } from 'react';
import { Menu, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSidebar } from '@/context/useSidebar';
import ThemeToggle from './ThemeToggle';

const formatTime = (date: Date) =>
  date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });

const formatDate = (date: Date) =>
  date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });

const MobileHeader = () => {
  const { toggleSidebar } = useSidebar();
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 60_000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="lg:hidden sticky top-0 z-30 border-b border-border/60 bg-background/95 backdrop-blur">
      <div className="flex items-center justify-between px-4 py-3">
        <Button
          size="icon"
          variant="ghost"
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
        >
          <Menu className="size-5" />
        </Button>

        <div className="text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-[0.3em]">
            VictrexSecOps
          </p>
          <p className="text-sm font-semibold">{formatTime(now)}</p>
          <p className="text-xs text-muted-foreground">{formatDate(now)}</p>
        </div>

        <div className="flex items-center gap-2">
          <Button size="icon" variant="ghost" aria-label="Notifications">
            <Bell className="size-5" />
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </div>
  );
};

export default MobileHeader;
