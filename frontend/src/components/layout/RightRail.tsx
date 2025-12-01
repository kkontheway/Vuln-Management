import { useMemo, useEffect, useState } from 'react';

const RightRail = () => {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(interval);
  }, []);

  const formatted = useMemo(() => {
    return {
      time: now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      date: now.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
      }),
    };
  }, [now]);

  return (
    <div className="space-y-4 lg:mt-[var(--content-top-offset)]">
      <section className="rounded-2xl border border-border/40 bg-pop/40 p-4 backdrop-blur">
        <p className="text-xs text-muted-foreground uppercase tracking-[0.3em]">
          System Clock
        </p>
        <p className="mt-2 text-4xl font-display">{formatted.time}</p>
        <p className="text-sm text-muted-foreground">{formatted.date}</p>
      </section>

      <section className="rounded-2xl border border-border/40 bg-pop/40 p-4 backdrop-blur space-y-3">
        <header>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            Upcoming
          </p>
          <p className="font-semibold">Notifications</p>
        </header>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p>• Mock notification feed</p>
          <p>• Placeholder for security alerts</p>
          <p>• Placeholder for chat activity</p>
        </div>
      </section>

      <section className="rounded-2xl border border-border/40 bg-pop/40 p-4 backdrop-blur">
        <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
          Chat
        </p>
        <p className="text-sm text-muted-foreground mt-2">
          Chat widgets will live here in the next phase.
        </p>
      </section>
    </div>
  );
};

export default RightRail;
