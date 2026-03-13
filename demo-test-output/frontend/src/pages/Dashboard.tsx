import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [refills, setRefills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.listSessions(), api.listAppointments(), api.listRefills()])
      .then(([s, a, r]) => { setSessions(s); setAppointments(a); setRefills(r); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Healthcare Voice Agent Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Active Sessions</p>
          <p className="text-3xl font-bold text-blue-700">{sessions.filter(s => s.status === 'active').length}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Upcoming Appointments</p>
          <p className="text-3xl font-bold text-green-700">{appointments.filter(a => a.status === 'scheduled').length}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Pending Refills</p>
          <p className="text-3xl font-bold text-orange-600">{refills.filter(r => r.status === 'pending').length}</p>
        </div>
      </div>

      {/* Sessions table */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Recent Sessions</h2>
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Intent</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sessions.map(s => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm"><Link to={`/detail/${s.id}`} className="text-blue-600 hover:underline">{s.id.slice(0,8)}</Link></td>
                  <td className="px-4 py-3 text-sm">{s.patient_id}</td>
                  <td className="px-4 py-3 text-sm">{s.intent_detected}</td>
                  <td className="px-4 py-3"><StatusBadge status={s.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Appointments */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Appointments</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {appointments.map(a => (
            <div key={a.id} className="bg-white rounded-xl shadow p-4">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium">{a.provider}</p>
                  <p className="text-sm text-gray-500">{a.reason}</p>
                </div>
                <StatusBadge status={a.status} />
              </div>
              <p className="text-xs text-gray-400 mt-2">{new Date(a.date_time).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
