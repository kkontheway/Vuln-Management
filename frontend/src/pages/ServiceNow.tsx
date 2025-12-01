import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import apiService from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { ServiceNowTicket, ServiceNowNote } from '@/types/servicenow';
import { formatDate } from '@/utils/formatters';
import { cn } from '@/lib/utils';
import { getErrorMessage } from '@/utils/error';

const ServiceNow = () => {
  const [tickets, setTickets] = useState<ServiceNowTicket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<ServiceNowTicket | null>(null);
  const [notes, setNotes] = useState<ServiceNowNote[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showNotesPanel, setShowNotesPanel] = useState(false);
  const [formData, setFormData] = useState({
    short_description: '',
    description: '',
    category: '',
    priority: '3',
    urgency: '3',
    impact: '3',
  });

  const loadTickets = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getServiceNowTickets();
      setTickets(data.tickets || []);
    } catch (error) {
      console.error('Failed to load tickets:', error);
      const errorMessage = getErrorMessage(error, 'Failed to load tickets');
      if (errorMessage.includes('not configured')) {
        alert('ServiceNow is not configured. Please configure it in ServiceNow Config page first.');
      } else {
        alert('Failed to load tickets: ' + errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTickets();
  }, [loadTickets]);

  const loadTicketNotes = async (ticketId: string) => {
    try {
      const data = await apiService.getServiceNowTicketNotes(ticketId);
      setNotes(data.notes || []);
    } catch (error) {
      console.error('Failed to load notes:', error);
      alert('Failed to load notes: ' + getErrorMessage(error, 'Unable to load notes'));
    }
  };

  const handleCreateTicket = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      setLoading(true);
      const data = await apiService.createServiceNowTicket(formData);
      alert('Ticket created successfully! Ticket Number: ' + data.ticket_number);
      setShowCreateForm(false);
      setFormData({
        short_description: '',
        description: '',
        category: '',
        priority: '3',
        urgency: '3',
        impact: '3',
      });
      await loadTickets();
    } catch (error) {
      alert('Failed to create ticket: ' + getErrorMessage(error, 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddNote = async (ticketId: string, noteText: string) => {
    try {
      await apiService.addServiceNowTicketNote(ticketId, noteText);
      alert('Note added successfully!');
      await loadTicketNotes(ticketId);
    } catch (error) {
      alert('Failed to add note: ' + getErrorMessage(error, 'Unknown error'));
    }
  };

  const handleViewNotes = async (ticket: ServiceNowTicket) => {
    setSelectedTicket(ticket);
    setShowNotesPanel(true);
    await loadTicketNotes(ticket.sys_id);
  };

  const getPriorityBadge = (priority: string) => {
    const priorityMap: Record<string, { label: string; className: string }> = {
      '1': { label: 'Critical', className: 'bg-severity-critical/20 text-severity-critical' },
      '2': { label: 'High', className: 'bg-severity-high/20 text-severity-high' },
      '3': { label: 'Medium', className: 'bg-severity-medium/20 text-severity-medium' },
      '4': { label: 'Low', className: 'bg-severity-low/20 text-severity-low' },
    };
    const p = priorityMap[priority] || { label: 'Unknown', className: 'bg-glass-hover text-text-secondary' };
    return <span className={cn('px-2 py-1 rounded text-xs font-medium', p.className)}>{p.label}</span>;
  };

  return (
    <div className="space-y-6">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-text-primary">ServiceNow Integration</h1>
          <div className="flex gap-3">
            <Button variant="outline" asChild>
              <Link to="/servicenow-config">⚙️ Configure</Link>
            </Button>
            <Button onClick={() => setShowCreateForm(true)}>
              ➕ Create Ticket
            </Button>
          </div>
        </div>

        {/* Create Ticket Form Modal */}
        <Dialog open={showCreateForm} onOpenChange={setShowCreateForm}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create ServiceNow Ticket</DialogTitle>
              <DialogDescription>
                Fill in the details to create a new ServiceNow ticket
              </DialogDescription>
            </DialogHeader>
            <form
              onSubmit={(event) => {
                void handleCreateTicket(event);
              }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Short Description *</label>
                <Input
                  value={formData.short_description}
                  onChange={(e) => setFormData({ ...formData, short_description: e.target.value })}
                  required
                  placeholder="Brief description of the issue"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Description</label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={5}
                  placeholder="Detailed description of the issue"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Category</label>
                <Input
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="e.g., Security, Network, Application"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-secondary">Priority</label>
                  <Select value={formData.priority} onValueChange={(value) => setFormData({ ...formData, priority: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 - Critical</SelectItem>
                      <SelectItem value="2">2 - High</SelectItem>
                      <SelectItem value="3">3 - Medium</SelectItem>
                      <SelectItem value="4">4 - Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-secondary">Urgency</label>
                  <Select value={formData.urgency} onValueChange={(value) => setFormData({ ...formData, urgency: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 - Critical</SelectItem>
                      <SelectItem value="2">2 - High</SelectItem>
                      <SelectItem value="3">3 - Medium</SelectItem>
                      <SelectItem value="4">4 - Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-secondary">Impact</label>
                  <Select value={formData.impact} onValueChange={(value) => setFormData({ ...formData, impact: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 - Critical</SelectItem>
                      <SelectItem value="2">2 - High</SelectItem>
                      <SelectItem value="3">3 - Medium</SelectItem>
                      <SelectItem value="4">4 - Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Ticket'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Tickets List */}
        <Card className="glass-panel">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Tickets</CardTitle>
                  <Button
                    variant="outline"
                    onClick={() => {
                      void loadTickets();
                    }}
                    disabled={loading}
                  >
                    🔄 Refresh
                  </Button>
                </div>
          </CardHeader>
          <CardContent>
            {loading && tickets.length === 0 ? (
              <div className="text-center py-8 text-text-secondary">Loading tickets...</div>
            ) : tickets.length === 0 ? (
              <div className="text-center py-8 text-text-secondary">
                No tickets found. Create your first ticket to get started.
              </div>
            ) : (
              <div className="rounded-md border border-glass-border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Number</TableHead>
                      <TableHead>Short Description</TableHead>
                      <TableHead>State</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tickets.map((ticket) => (
                      <TableRow key={ticket.sys_id}>
                        <TableCell><strong>{ticket.number || ticket.sys_id}</strong></TableCell>
                        <TableCell>{ticket.short_description || '-'}</TableCell>
                        <TableCell>{ticket.state || '-'}</TableCell>
                        <TableCell>{getPriorityBadge(ticket.priority)}</TableCell>
                        <TableCell>{formatDate(ticket.opened_at)}</TableCell>
                        <TableCell>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              void handleViewNotes(ticket);
                            }}
                          >
                            View Notes
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Notes Panel Modal */}
        <Dialog open={showNotesPanel} onOpenChange={setShowNotesPanel}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Ticket Notes: {selectedTicket?.number || selectedTicket?.sys_id}</DialogTitle>
              <DialogDescription>
                View and add notes for this ticket
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Notes ({notes.length})</h3>
                {notes.length === 0 ? (
                  <div className="text-center py-8 text-text-secondary">
                    No notes found for this ticket.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {notes.map((note, index) => (
                      <div key={index} className="border border-glass-border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-text-secondary">{note.type || 'Note'}</span>
                          <span className="text-xs text-text-tertiary">{formatDate(note.timestamp)}</span>
                        </div>
                        <div className="text-text-primary">{note.value || '-'}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div>
                <h3 className="text-lg font-semibold mb-4">Add Note</h3>
                <NoteForm
                  ticketId={selectedTicket?.sys_id || ''}
                  onAddNote={handleAddNote}
                />
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// Note Form Component
interface NoteFormProps {
  ticketId: string;
  onAddNote: (ticketId: string, noteText: string) => Promise<void>;
}

const NoteForm = ({ ticketId, onAddNote }: NoteFormProps) => {
  const [noteText, setNoteText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!noteText.trim()) {
      alert('Please enter a note');
      return;
    }
    try {
      setIsSubmitting(true);
      await onAddNote(ticketId, noteText);
      setNoteText('');
    } catch (error) {
      console.error('Failed to add note:', error);
      alert(getErrorMessage(error, 'Failed to add note'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={(event) => {
        void handleSubmit(event);
      }}
      className="space-y-4"
    >
      <Textarea
        value={noteText}
        onChange={(e) => setNoteText(e.target.value)}
        placeholder="Enter your note here..."
        rows={4}
        required
      />
      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Adding...' : 'Add Note'}
        </Button>
      </div>
    </form>
  );
};

export default ServiceNow;
