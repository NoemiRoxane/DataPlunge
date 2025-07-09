import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { DateProvider } from './context/DateContext';
import Dashboard from './pages/Dashboard';
import ByChannels from './pages/ByChannels';
import ByCampaigns from './pages/ByCampaigns';
import AddDataSource from './pages/AddDataSource';
import GAConnectionPage from './pages/GAConnectionPage'; // ✅ neue GA-Onboarding-Seite
import MetaConnectionPage from './pages/MetaConnectionPage';
import './styles.css';

function App() {
  return (
    <Router>
      <DateProvider>
        <div className="app-container">
          <header className="top-header">
            <div className="header-title">
              <span className="header-title-data">Data</span>
              <span style={{ marginLeft: '8px' }} className="header-title-plunge">Plunge</span>
            </div>
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
                  <NavLink to="/data-overall" className={({ isActive }) => isActive ? 'active-link' : ''}>
                    Data
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/add-data-source" className={({ isActive }) => isActive ? 'active-link' : ''}>
                    Add Data Source
                  </NavLink>
                </li>
                <li>
                  <NavLink to="/add-data-manually" className={({ isActive }) => isActive ? 'active-link' : ''}>
                    Add Data manually
                  </NavLink>
                </li>
              </ul>
            </aside>

            <main className="main-content">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/channels" element={<ByChannels />} />
                <Route path="/campaigns" element={<ByCampaigns />} />
                <Route path="/add-data-source" element={<AddDataSource />} />
                <Route path="/add-data-manually" element={<div>Add Data Manually Page</div>} />
                
                {/* ✅ Neue dedizierte Seite für GA-Onboarding */}
                <Route path="/connect/google-analytics" element={<GAConnectionPage />} />
                <Route path="/connect/meta" element={<MetaConnectionPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </DateProvider>
    </Router>
  );
}

export default App;
