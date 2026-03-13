const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Healthcare API
export const api = {
  listSessions: (status?: string) =>
    request<any[]>(status ? `/sessions?status=${status}` : '/sessions'),
  getSession: (id: string) => request<any>(`/sessions/${id}`),
  createSession: (data: { patient_id: string; intent?: string }) =>
    request<any>('/sessions', { method: 'POST', body: JSON.stringify(data) }),
  endSession: (id: string) =>
    request<any>(`/sessions/${id}/end`, { method: 'POST' }),
  escalateSession: (id: string, reason?: string) =>
    request<any>(`/sessions/${id}/escalate?reason=${encodeURIComponent(reason || '')}`, { method: 'POST' }),

  listAppointments: (patientId?: string) =>
    request<any[]>(patientId ? `/appointments?patient_id=${patientId}` : '/appointments'),
  bookAppointment: (data: { patient_id: string; provider: string; date_time: string; reason?: string }) =>
    request<any>('/appointments', { method: 'POST', body: JSON.stringify(data) }),

  listRefills: (patientId?: string) =>
    request<any[]>(patientId ? `/prescriptions/refills?patient_id=${patientId}` : '/prescriptions/refills'),
  requestRefill: (data: { patient_id: string; medication: string; pharmacy?: string }) =>
    request<any>('/prescriptions/refills', { method: 'POST', body: JSON.stringify(data) }),

  listItems: () => request<any[]>('/items'),
};
