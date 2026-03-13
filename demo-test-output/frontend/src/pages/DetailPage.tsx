import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) api.getSession(id).then(setSession).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;
  if (!session) return <p className="text-center py-12 text-red-500">Session not found</p>;

  const handleEnd = async () => {
    const updated = await api.endSession(session.id);
    setSession(updated);
  };

  const handleEscalate = async () => {
    const updated = await api.escalateSession(session.id, 'Escalated from dashboard');
    setSession(updated);
  };

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/')} className="text-blue-600 hover:underline text-sm">&larr; Back</button>
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold">Session {session.id.slice(0,8)}</h1>
          <StatusBadge status={session.status} />
        </div>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div><dt className="text-gray-500">Patient ID</dt><dd className="font-medium">{session.patient_id}</dd></div>
          <div><dt className="text-gray-500">Intent</dt><dd className="font-medium">{session.intent_detected || '—'}</dd></div>
          <div><dt className="text-gray-500">Created</dt><dd>{new Date(session.created_at).toLocaleString()}</dd></div>
          <div><dt className="text-gray-500">Updated</dt><dd>{new Date(session.updated_at).toLocaleString()}</dd></div>
        </dl>
        {session.status === 'active' && (
          <div className="mt-6 flex gap-3">
            <button onClick={handleEnd} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">End Session</button>
            <button onClick={handleEscalate} className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700">Escalate</button>
          </div>
        )}
      </div>
    </div>
  );
}
