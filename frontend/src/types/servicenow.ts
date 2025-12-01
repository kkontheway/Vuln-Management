// ServiceNow Types

export interface ServiceNowTicket {
  sys_id: string;
  number: string;
  short_description: string;
  description?: string;
  state: string;
  priority: string;
  category?: string;
  assigned_to?: string;
  opened_at: string;
  updated_at: string;
}

export interface ServiceNowTicketCreate {
  table?: string;
  short_description: string;
  description?: string;
  category?: string;
  priority?: string;
  urgency?: string;
  impact?: string;
}

export interface ServiceNowTicketResponse {
  ticket: ServiceNowTicket;
  ticket_number?: string;
  sys_id?: string;
}

export interface ServiceNowTicketsResponse {
  tickets: ServiceNowTicket[];
  total: number;
}

export interface ServiceNowNote {
  type: string;
  value: string;
  timestamp?: string;
}

export interface ServiceNowNotesResponse {
  notes: ServiceNowNote[];
  total: number;
}

export interface ServiceNowNoteAdd {
  note: string;
  table?: string;
}
