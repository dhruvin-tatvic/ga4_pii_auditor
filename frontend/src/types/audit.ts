export interface AuditPayload {
  client_name: string;
  property_id: string;
  property_access: string;
  start_date: string;
  end_date: string;
  send_to: string;
  send_to_cc: string;
  custom_dimensions?: string[];
}

export interface AuditResponse {
  status: 'success' | 'error';
  message: string;
}
