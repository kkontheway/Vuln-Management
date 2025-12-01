import { useState, useEffect, useRef, useCallback } from 'react';
import apiService from '@/services/api';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { formatNumber } from '@/utils/formatters';
import type { SyncDataSource } from '@/types/api';
import ThemeToggle from '@/components/layout/ThemeToggle';

type TimeoutHandle = ReturnType<typeof setTimeout>;
type IntervalHandle = ReturnType<typeof setInterval>;

const getErrorMessage = (err: unknown, fallback: string): string => {
  if (typeof err === 'object' && err !== null) {
    const error = err as { message?: string };
    return error.message ?? fallback;
  }
  return fallback;
};

const Header = () => {
  const [stats, setStats] = useState({
    totalVulns: '-',
    critical: '-',
    high: '-',
    medium: '-',
  });
  const [syncStatus, setSyncStatus] = useState<{
    device_vulnerabilities?: { lastSyncTime: string };
    vulnerability_list?: { lastSyncTime: string };
  }>({});
  const [isSyncing, setIsSyncing] = useState(false);
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [showSnapshotModal, setShowSnapshotModal] = useState(false);
  const [selectedDataSources, setSelectedDataSources] = useState<SyncDataSource[]>(['device_vulnerabilities']);
  const [syncProgress, setSyncProgress] = useState(0);
  const syncPollingIntervalRef = useRef<IntervalHandle | null>(null);
  const syncTimeoutRef = useRef<TimeoutHandle | null>(null);
  const isSyncingRef = useRef(false);
  const { toast } = useToast();

  const loadStats = useCallback(async () => {
    try {
      const [uniqueCount, severityCounts] = await Promise.all([
        apiService.getUniqueCveCount(),
        apiService.getSeverityCounts(),
      ]);

      setStats({
        totalVulns: String(uniqueCount.unique_cve_count || 0),
        critical: String(severityCounts.critical || 0),
        high: String(severityCounts.high || 0),
        medium: String(severityCounts.medium || 0),
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }, []);

  const formatSyncTime = (timeString: string | undefined): string => {
    if (!timeString) return 'Never synced';
    try {
      const syncDate = new Date(timeString);
      return syncDate.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (error) {
      return 'Invalid date';
    }
  };

  const loadSyncStatus = useCallback(async () => {
    try {
      const data = await apiService.getSyncStatus();
      const newStatus: {
        device_vulnerabilities?: { lastSyncTime: string };
        vulnerability_list?: { lastSyncTime: string };
      } = {};
      
      if (data.device_vulnerabilities?.last_sync_time) {
        newStatus.device_vulnerabilities = {
          lastSyncTime: formatSyncTime(data.device_vulnerabilities.last_sync_time),
        };
      } else {
        newStatus.device_vulnerabilities = { lastSyncTime: 'Never synced' };
      }
      
      if (data.vulnerability_list?.last_sync_time) {
        newStatus.vulnerability_list = {
          lastSyncTime: formatSyncTime(data.vulnerability_list.last_sync_time),
        };
      } else {
        newStatus.vulnerability_list = { lastSyncTime: 'Never synced' };
      }
      
      setSyncStatus(newStatus);
    } catch (error) {
      console.error('Failed to load sync status:', error);
      setSyncStatus({
        device_vulnerabilities: { lastSyncTime: 'Error' },
        vulnerability_list: { lastSyncTime: 'Error' },
      });
    }
  }, []);

  useEffect(() => {
    void loadStats();
    void loadSyncStatus();
    const interval = setInterval(() => {
      void loadSyncStatus();
    }, 30000);
    return () => {
      clearInterval(interval);
      if (syncPollingIntervalRef.current) {
        clearInterval(syncPollingIntervalRef.current);
      }
    };
  }, [loadStats, loadSyncStatus]);

  const stopSyncPolling = () => {
    if (syncPollingIntervalRef.current) {
      clearInterval(syncPollingIntervalRef.current);
      syncPollingIntervalRef.current = null;
    }
    if (syncTimeoutRef.current) {
      clearTimeout(syncTimeoutRef.current);
      syncTimeoutRef.current = null;
    }
  };

  const startSyncPolling = () => {
    // Clear any existing polling
    stopSyncPolling();
    
    // Start polling every 2 seconds for real-time progress
    const pollProgress = async () => {
      try {
        const progressData = await apiService.getSyncProgress();
        
        // Update progress from backend
        setSyncProgress(progressData.progress);
        
        // Check if sync is complete
        if (progressData.is_complete || !progressData.is_syncing) {
          if (progressData.is_complete && progressData.stage === 'complete') {
            // Sync completed successfully
            setSyncProgress(100);
            setTimeout(() => {
              setIsSyncing(false);
              isSyncingRef.current = false;
              setSyncProgress(0);
              stopSyncPolling();
              void loadSyncStatus();
              toast({
                title: "Sync completed",
                description: progressData.message || "Data synchronization has been completed successfully.",
              });
            }, 500);
          } else if (progressData.is_complete && progressData.stage === 'error') {
            // Sync failed
            setIsSyncing(false);
            isSyncingRef.current = false;
            setSyncProgress(0);
            stopSyncPolling();
            toast({
              title: "Sync failed",
              description: progressData.message || "Data synchronization failed.",
            });
          } else {
            // Sync stopped but not explicitly completed
            setIsSyncing(false);
            isSyncingRef.current = false;
            setSyncProgress(0);
            stopSyncPolling();
            void loadSyncStatus();
          }
        }
      } catch (error) {
        console.error('Error polling sync progress:', error);
        // On error, fall back to checking sync status
        try {
          const status = await apiService.getSyncStatus();
          if (status.device_vulnerabilities?.last_sync_time) {
            const syncTime = new Date(status.device_vulnerabilities.last_sync_time);
            const now = new Date();
            // If sync time is within last 10 seconds, consider it just completed
            if ((now.getTime() - syncTime.getTime()) < 10000) {
              setSyncProgress(100);
              setTimeout(() => {
                setIsSyncing(false);
                isSyncingRef.current = false;
                setSyncProgress(0);
                stopSyncPolling();
                void loadSyncStatus();
                toast({
                  title: "Sync completed",
                  description: "Data synchronization has been completed successfully.",
                });
              }, 500);
            }
          }
        } catch (statusError) {
          console.error('Error checking sync status:', statusError);
        }
      }
    };

    syncPollingIntervalRef.current = setInterval(() => {
      void pollProgress();
    }, 2000);
  };

  const handleSync = async () => {
    if (selectedDataSources.length === 0) {
      toast({
        title: "No data source selected",
        description: "Please select at least one data source to sync.",
      });
      return;
    }

    setShowSyncModal(false);
    setIsSyncing(true);
    isSyncingRef.current = true;
    setSyncProgress(10);
    
    try {
      await apiService.triggerSync(selectedDataSources);
      
      // Show toast notification
      toast({
        title: "Sync started",
        description: `Syncing ${selectedDataSources.length} data source(s). This may take several minutes.`,
      });
      
      // Start polling for sync completion
      startSyncPolling();
      
      // Set a maximum timeout (30 minutes)
      syncTimeoutRef.current = setTimeout(() => {
        if (isSyncingRef.current) {
          setIsSyncing(false);
          isSyncingRef.current = false;
          setSyncProgress(0);
          stopSyncPolling();
          toast({
            title: "Sync timeout",
            description: "Sync is taking longer than expected. Please check the status manually.",
          });
        }
      }, 30 * 60 * 1000);
      
    } catch (error: unknown) {
      setIsSyncing(false);
      isSyncingRef.current = false;
      setSyncProgress(0);
      stopSyncPolling();
      toast({
        title: "Sync failed",
        description: getErrorMessage(error, "Failed to start data synchronization."),
      });
    }
  };

  const toggleDataSource = (source: SyncDataSource) => {
    setSelectedDataSources(prev => 
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
  };

  const handleCreateSnapshot = async () => {
    setShowSnapshotModal(false);
    try {
      const data = await apiService.createInitialSnapshot();
      if (data.snapshot_id) {
        alert('Snapshot created successfully! Snapshot ID: ' + data.snapshot_id);
      } else {
        throw new Error(data.error || 'Failed to create snapshot');
      }
    } catch (error: unknown) {
      alert('Failed to create snapshot: ' + getErrorMessage(error, 'Unknown error'));
    }
  };

  return (
    <>
      <header className="hidden lg:block fixed top-0 left-64 right-0 z-[999] h-20 bg-glass-bg/70 backdrop-blur-xl border-b border-glass-border shadow-glass">
        <div className="flex h-full items-center justify-between px-6">
          <h1 className="text-xl font-semibold text-text-primary" style={{ letterSpacing: '-0.03em' }}>Vulnerability Management System</h1>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-4">
              <div className="flex flex-col items-end">
                <span className="text-xs text-text-secondary">Total CVEs</span>
                <span className="text-lg font-semibold text-text-primary">{formatNumber(stats.totalVulns)}</span>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-xs text-text-secondary">Critical</span>
                <span className="text-lg font-semibold text-severity-critical">{formatNumber(stats.critical)}</span>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-xs text-text-secondary">High</span>
                <span className="text-lg font-semibold text-severity-high">{formatNumber(stats.high)}</span>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-xs text-text-secondary">Medium</span>
                <span className="text-lg font-semibold text-severity-medium">{formatNumber(stats.medium)}</span>
              </div>
            </div>
            <div className="flex items-center gap-3 border-l border-glass-border pl-6">
              <div className="flex flex-col">
                <span className="text-xs text-text-secondary">Last Sync:</span>
                <span className="text-sm font-medium text-text-primary">
                  {syncStatus.device_vulnerabilities?.lastSyncTime || '-'}
                </span>
              </div>
              {isSyncing && (
                <div className="flex flex-col gap-1 min-w-[200px]">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-secondary">Syncing...</span>
                    <span className="text-xs text-text-tertiary">
                      {syncProgress >= 100 ? 'Complete' : syncProgress >= 90 ? 'Processing...' : `${syncProgress}%`}
                    </span>
                  </div>
                  <Progress value={syncProgress >= 100 ? 100 : syncProgress >= 90 ? undefined : syncProgress} className="h-1.5" />
                </div>
              )}
              <div className="flex gap-2">
                <ThemeToggle />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSnapshotModal(true)}
                >
                  <span>📸</span>
                  <span>Create Snapshot</span>
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setShowSyncModal(true)}
                  disabled={isSyncing}
                >
                  <span>🔄</span>
                  <span>{isSyncing ? 'Syncing...' : 'Sync Data'}</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Sync Data Source Selection Modal */}
      <Dialog open={showSyncModal} onOpenChange={setShowSyncModal}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Select Data Sources to Sync</DialogTitle>
            <DialogDescription>
              Choose which data sources you want to sync. This process may take several minutes depending on the amount of data.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            {/* Device Vulnerabilities Option */}
            <div className="flex items-start space-x-3 p-4 rounded-xl border border-glass-border bg-glass-bg/50 hover:bg-glass-bg/70 transition-colors">
              <Checkbox
                id="device_vulnerabilities"
                checked={selectedDataSources.includes('device_vulnerabilities')}
                onCheckedChange={() => toggleDataSource('device_vulnerabilities')}
                className="mt-1"
              />
              <div className="flex-1 space-y-1">
                <label
                  htmlFor="device_vulnerabilities"
                  className="text-sm font-medium text-text-primary cursor-pointer"
                >
                  Device Vulnerabilities
                </label>
                <p className="text-xs text-text-secondary">
                  Device-level vulnerability details from Microsoft Defender SoftwareVulnerabilitiesByMachine API. Full sync from all devices.
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-primary/10 text-primary">
                    Full Sync
                  </span>
                  <span className="text-xs text-text-tertiary">
                    Last synced: {syncStatus.device_vulnerabilities?.lastSyncTime || 'Never synced'}
                  </span>
                </div>
              </div>
            </div>

          </div>
          {selectedDataSources.length === 0 && (
            <p className="text-sm text-red-500">Please select at least one data source.</p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSyncModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                void handleSync();
              }}
              disabled={selectedDataSources.length === 0}
            >
              Start Sync
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Snapshot Confirmation Modal */}
      <Dialog open={showSnapshotModal} onOpenChange={setShowSnapshotModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Snapshot</DialogTitle>
            <DialogDescription>
              Are you sure you want to create a snapshot of current vulnerability data?
              This will record the current state of all vulnerabilities for historical tracking. This process may take a few minutes.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSnapshotModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                void handleCreateSnapshot();
              }}
            >
              Create Snapshot
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Header;
