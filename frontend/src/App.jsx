import './index.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './components/ToastContainer';
import ProtectedRoute from './components/ProtectedRoute';
import Auth from './pages/Auth';
import Dashboard from './pages/Dashboard';
import Calendar from './pages/Calendar';
import Tasks from './pages/Tasks';
import Reminders from './pages/Reminders';
import MainLayout from './layout/MainLayout';

function App() {
  return (
    <Router>
      <AuthProvider>
        <ToastProvider>
          <Routes>
          {/* Public Route - Login/Signup */}
          <Route path="/login" element={<Auth />} />

          {/* Protected Routes - Require Authentication */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/calendar" element={<Calendar />} />
                    <Route path="/tasks" element={<Tasks />} />
                    <Route path="/reminders" element={<Reminders />} />
                  </Routes>
                </MainLayout>
              </ProtectedRoute>
            }
          />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;