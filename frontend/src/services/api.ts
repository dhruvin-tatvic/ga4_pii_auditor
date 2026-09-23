import { AuditPayload, AuditResponse } from '../types/audit';

export async function triggerSingleAudit(payload: AuditPayload): Promise<AuditResponse> {
  try {
    const response = await fetch('/api/audit/single', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error triggering audit:', error);
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

export async function fetchClientList(): Promise<Array<{
  client_name: string;
  property_id: string;
  property_access: string;
  send_to: string;
  send_to_cc?: string;
}>> {
  try {
    const response = await fetch('/api/client-list');
    const data = await response.json();
    if (data.status !== 'success') {
      return [];
    }
    return data.clients || [];
  } catch (error) {
    console.error('Error fetching client list:', error);
    return [];
  }
}
