import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import './styles.css';

function App() {
  return (
    <Router>
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
                <NavLink
                  to="/"
                  className={({ isActive }) => isActive ? 'active-link' : ''}
                >
                  Performance (Overall)
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/channels"
                  className={({ isActive }) => isActive ? 'active-link' : ''}
                >
                  by Channels
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/campaigns"
                  className={({ isActive }) => isActive ? 'active-link' : ''}
                >
                  by Campaigns
                </NavLink>
              </li>
              <li className="bold">
                <NavLink
                  to="/add-data-source"
                  className={({ isActive }) => isActive ? 'active-link' : ''}
                >
                  Data
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/add-data-manually"
                  className={({ isActive }) => isActive ? 'active-link' : ''}
                >
                  Add Data manually
                </NavLink>
              </li>
            </ul>
          </aside>
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
