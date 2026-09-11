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

    // Check if response is OK before parsing
    if (!response.ok) {
      const contentType = response.headers.get('content-type');
      let errorMessage = `HTTP ${response.status}`;
      
      if (contentType?.includes('application/json')) {
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.statusText}`;
        }
      } else {
        errorMessage = `Server error: ${response.statusText}`;
      }
      
      return {
        status: 'error',
        message: errorMessage,
      };
    }

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
