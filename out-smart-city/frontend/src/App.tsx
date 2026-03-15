import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DetailPage from './pages/DetailPage';
import ChatPage from './pages/ChatPage';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/detail/:id" element={<DetailPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </Layout>
  );
}
