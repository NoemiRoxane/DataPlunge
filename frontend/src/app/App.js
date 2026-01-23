import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { DateProvider } from '../context/DateContext';
import ProtectedRoute from '../components/ProtectedRoute';
import UserMenu from '../components/UserMenu/UserMenu';
import Dashboard from "../pages/Dashboard/Dashboard";
import ByChannels from "../pages/ByChannels/ByChannels";
import ByCampaigns from "../pages/ByCampaigns/ByCampaigns";
import AddDataSource from "../pages/AddDataSource/AddDataSource";
import GAConnectionPage from "../pages/Connect/GAConnectionPage";
import MetaConnectionPage from "../pages/Connect/MetaConnectionPage";
import DataSourcesManager from "../pages/DataSources/DataSourcesManager";
import Login from "../pages/Auth/Login";
import Register from "../pages/Auth/Register";
import AuthCallback from "../pages/Auth/AuthCallback";
//import "../styles/styles.css";

// Layout component for authenticated pages
function AppLayout({ children }) {
  return (
    <div className="app-container">
      <header className="top-header">
        <div className="header-title">
          <span className="header-title-data">Data</span>
          <span style={{ marginLeft: '8px' }} className="header-title-plunge">Plunge</span>
        </div>
        <UserMenu />
      </header>

      <div className="content-wrapper">
        <aside className="sidebar">
          <ul className="sidebar-menu">
            <li className="bold">
              <NavLink to="/" className={({ isActive }) => isActive ? 'active-link' : ''}>
                Performance (Overall)
              </NavLink>
            </li>
            <li>
              <NavLink to="/channels" className={({ isActive }) => isActive ? 'active-link' : ''}>
                by Channels
              </NavLink>
            </li>
            <li>
              <NavLink to="/campaigns" className={({ isActive }) => isActive ? 'active-link' : ''}>
                by Campaigns
              </NavLink>
            </li>
            <li className="bold">
              <NavLink to="/data-sources" className={({ isActive }) => isActive ? 'active-link' : ''}>
                Data Sources
              </NavLink>
            </li>
            <li>
              <NavLink to="/add-data-source" className={({ isActive }) => isActive ? 'active-link' : ''}>
                Add Data Source
              </NavLink>
            </li>
          </ul>
        </aside>

        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/auth/callback" element={<AuthCallback />} />

          {/* Protected routes */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <DateProvider>
                  <AppLayout>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/channels" element={<ByChannels />} />
                      <Route path="/campaigns" element={<ByCampaigns />} />
                      <Route path="/data-sources" element={<DataSourcesManager />} />
                      <Route path="/add-data-source" element={<AddDataSource />} />
                      <Route path="/connect/google-analytics" element={<GAConnectionPage />} />
                      <Route path="/connect/meta" element={<MetaConnectionPage />} />
                    </Routes>
                  </AppLayout>
                </DateProvider>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
