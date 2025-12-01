import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { useSidebar } from '@/context/useSidebar';

interface NavItem {
  path: string;
  icon: string;
  label: string;
}

const Sidebar = () => {
  const { isCollapsed, toggleSidebar } = useSidebar();
  const [configExpanded, setConfigExpanded] = useState(false);
  const location = useLocation();

  const openSidebar = () => {
    toggleSidebar();
  };

  const toggleConfigMenu = () => {
    setConfigExpanded(!configExpanded);
  };

  const navItems: NavItem[] = [
    { path: '/', icon: '📈', label: 'Dashboard' },
    { path: '/vulnerabilities', icon: '🔍', label: 'Vulnerabilities' },
    { path: '/threat-intelligence', icon: '🛡️', label: 'Threat Intelligence' },
    { path: '/servicenow', icon: '🎫', label: 'ServiceNow' },
    { path: '/ai-chat', icon: '🤖', label: 'VictrexSecOps AI' },
    { path: '/tools', icon: '🛠️', label: 'Tools' },
  ];

  const configItems: NavItem[] = [
    { path: '/servicenow-config', icon: '⚙️', label: 'ServiceNow Config' },
    { path: '/chat-config', icon: '⚙️', label: 'AI Chat Config' },
  ];

  // Check if any config item is active
  const isConfigActive = configItems.some(item => location.pathname === item.path);

  // Auto-expand config menu if a config page is active
  useEffect(() => {
    if (isConfigActive) {
      setConfigExpanded(true);
    }
  }, [isConfigActive]);

  return (
    <>
      {isCollapsed && (
        <button
          className="fixed left-4 top-4 z-[998] flex h-10 w-10 items-center justify-center rounded-2xl bg-glass-bg border border-glass-border text-text-primary shadow-glass backdrop-blur-lg hover:bg-glass-hover transition-all"
          onClick={openSidebar}
        >
          <span>☰</span>
        </button>
      )}

      <div className={cn(
        "fixed left-0 top-0 h-full w-64 bg-glass-bg/70 backdrop-blur-xl border-r border-glass-border shadow-glass transition-all duration-300 z-[1000]",
        isCollapsed && "-translate-x-full"
      )}>
        <div className="flex h-16 items-center justify-between border-b border-glass-border px-6">
          <h2 className="text-lg font-semibold text-text-primary" style={{ letterSpacing: '-0.03em' }}>Vuln Management</h2>
          <button
            className="flex h-8 w-8 items-center justify-center rounded hover:bg-glass-hover transition-colors"
            onClick={toggleSidebar}
          >
            ☰
          </button>
        </div>
        <nav className="flex flex-col gap-1 p-4">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all",
                location.pathname === item.path
                  ? "bg-glass-hover text-text-primary shadow-sm"
                  : "text-text-secondary hover:bg-glass-hover hover:text-text-primary"
              )}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}

          {/* Config Submenu */}
          <div className="mt-2">
            <div
              className={cn(
                "flex items-center justify-between rounded-xl px-4 py-3 text-sm font-medium transition-all cursor-pointer",
                isConfigActive
                  ? "bg-glass-hover text-text-primary shadow-sm"
                  : "text-text-secondary hover:bg-glass-hover hover:text-text-primary"
              )}
              onClick={toggleConfigMenu}
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">⚙️</span>
                <span>Config</span>
              </div>
              <span className="text-xs opacity-70">{configExpanded ? '▼' : '▶'}</span>
            </div>
            {configExpanded && (
              <div className="ml-4 mt-1 border-l-2 border-glass-border pl-4">
                {configItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium transition-all",
                      location.pathname === item.path
                        ? "bg-glass-hover text-text-primary shadow-sm"
                        : "text-text-secondary hover:bg-glass-hover hover:text-text-primary"
                    )}
                  >
                    <span className="text-base">{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </nav>
      </div>
    </>
  );
};

export default Sidebar;
