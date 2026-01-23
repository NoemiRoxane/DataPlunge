import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './UserMenu.css';

function UserMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuth();
  const menuRef = useRef(null);
  const navigate = useNavigate();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const handleLogout = () => {
    logout();
  };

  const handleDataSources = () => {
    setIsOpen(false);
    navigate('/data-sources');
  };

  const handleSetupWizard = () => {
    setIsOpen(false);
    navigate('/?setup=true');
  };

  // Get user initials for avatar
  const getInitials = () => {
    if (!user) return '?';
    if (user.full_name) {
      const names = user.full_name.split(' ');
      return names.map(n => n[0]).join('').substring(0, 2).toUpperCase();
    }
    return user.email.substring(0, 2).toUpperCase();
  };

  if (!user) return null;

  return (
    <div className="user-menu" ref={menuRef}>
      <button className="user-menu-button" onClick={toggleMenu}>
        <div className="user-avatar">{getInitials()}</div>
        <span className="user-name">{user.full_name || user.email}</span>
        <svg
          className={`dropdown-icon ${isOpen ? 'open' : ''}`}
          width="12"
          height="12"
          viewBox="0 0 12 12"
        >
          <path d="M6 9L1 4h10z" fill="currentColor" />
        </svg>
      </button>

      {isOpen && (
        <div className="user-menu-dropdown">
          <div className="user-menu-header">
            <div className="user-menu-email">{user.email}</div>
          </div>
          <div className="user-menu-divider"></div>
          <button className="user-menu-item" onClick={handleSetupWizard}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1v6M8 15v-6M1 8h6M15 8h-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Setup Wizard
          </button>
          <button className="user-menu-item" onClick={handleDataSources}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Manage Data Sources
          </button>
          <div className="user-menu-divider"></div>
          <button className="user-menu-item logout" onClick={handleLogout}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3M11 11l3-3-3-3M14 8H6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Logout
          </button>
        </div>
      )}
    </div>
  );
}

export default UserMenu;
