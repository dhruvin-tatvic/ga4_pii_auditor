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
