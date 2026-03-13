// Shared TypeScript type definitions

export interface Item {
  id: string;
  name: string;
  description: string;
  project: string;
}

export interface Session {
  id: string;
  patient_id: string;
  status: 'active' | 'completed' | 'escalated';
  intent_detected: string;
  transcript: string[];
  escalation_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  provider: string;
  date_time: string;
  reason: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  created_at: string;
}

export interface PrescriptionRefill {
  id: string;
  patient_id: string;
  medication: string;
  pharmacy: string;
  status: 'pending' | 'approved' | 'denied';
  created_at: string;
}
