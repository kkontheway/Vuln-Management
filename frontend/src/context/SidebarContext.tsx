import { useState, useEffect, ReactNode } from 'react';
import { SidebarContext } from './sidebar-context-value';

interface SidebarProviderProps {
  children: ReactNode;
}

const readSidebarState = (): boolean => {
  if (typeof window === 'undefined') {
    return false;
  }
  const saved = window.localStorage.getItem('sidebarCollapsed');
  return saved === 'true';
};

export const SidebarProvider = ({ children }: SidebarProviderProps) => {
  // 从localStorage读取初始状态，默认为false（展开）
  const [isCollapsed, setIsCollapsedState] = useState<boolean>(readSidebarState);

  // 保存状态到localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('sidebarCollapsed', JSON.stringify(isCollapsed));
    }
  }, [isCollapsed]);

  const setIsCollapsed = (collapsed: boolean) => {
    setIsCollapsedState(collapsed);
  };

  const toggleSidebar = () => {
    setIsCollapsedState((prev) => !prev);
  };

  return (
    <SidebarContext.Provider value={{ isCollapsed, setIsCollapsed, toggleSidebar }}>
      {children}
    </SidebarContext.Provider>
  );
};

export default SidebarProvider;
