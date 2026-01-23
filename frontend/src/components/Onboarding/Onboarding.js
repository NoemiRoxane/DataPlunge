import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../../utils/api';
import './Onboarding.css';

// Data source options
const DATA_SOURCES = [
  {
    id: 'google-ads',
    name: 'Google Ads',
    icon: (
      <svg viewBox="0 0 24 24" width="32" height="32">
        <path fill="#FBBC04" d="M12 11.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9z"/>
        <path fill="#4285F4" d="M5.5 4a2.5 2.5 0 0 0-2.17 3.75l8.5 14.72a2.5 2.5 0 0 0 4.33-2.5l-8.5-14.72A2.5 2.5 0 0 0 5.5 4z"/>
        <path fill="#34A853" d="M18.5 4a2.5 2.5 0 0 1 2.17 3.75l-8.5 14.72a2.5 2.5 0 0 1-4.33-2.5l8.5-14.72A2.5 2.5 0 0 1 18.5 4z"/>
      </svg>
    ),
    connectUrl: '/add-data-source',
  },
  {
    id: 'google-analytics',
    name: 'Google Analytics',
    icon: (
      <svg viewBox="0 0 24 24" width="32" height="32">
        <path fill="#F9AB00" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
      </svg>
    ),
    connectUrl: '/connect/google-analytics',
  },
  {
    id: 'meta',
    name: 'Meta Ads',
    icon: (
      <svg viewBox="0 0 24 24" width="32" height="32">
        <path fill="#1877F2" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
      </svg>
    ),
    connectUrl: '/connect/meta',
  },
];

function Onboarding({ onComplete, onSkip }) {
  const [step, setStep] = useState(1);
  const [selectedSources, setSelectedSources] = useState([]);
  const [existingDatasources, setExistingDatasources] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch existing data sources to show which are already connected
    const fetchExistingDatasources = async () => {
      try {
        const data = await api.get('/user/datasources');
        setExistingDatasources(data.map(ds => ds.source_name.toLowerCase().replace(' ', '-')));
      } catch (err) {
        console.error('Failed to fetch existing data sources:', err);
      }
    };
    fetchExistingDatasources();
  }, []);

  const handleSourceToggle = (sourceId) => {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    );
  };

  const handleNext = () => {
    if (step === 1) {
      if (selectedSources.length > 0) {
        // Navigate to the first selected data source connection page
        const firstSource = DATA_SOURCES.find(ds => ds.id === selectedSources[0]);
        if (firstSource) {
          navigate(firstSource.connectUrl);
        }
      } else {
        // No sources selected, just close onboarding
        onComplete();
      }
    }
  };

  const handleCancel = () => {
    onSkip();
  };

  const isSourceConnected = (sourceId) => {
    return existingDatasources.some(ds => ds.includes(sourceId.split('-')[0]));
  };

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-modal">
        {step === 1 && (
          <>
            <h1 className="onboarding-title">Welcome to Data Plunge!</h1>
            <h2 className="onboarding-subtitle">First Step: Connect Data Sources</h2>
            <p className="onboarding-description">
              Great decision to use Data Plunge. To jump into your data and get useful insight, we first
              need to connect Data Sources. Choose all Data Sources you have data on.
            </p>

            <div className="datasource-options">
              {DATA_SOURCES.map((source) => {
                const isConnected = isSourceConnected(source.id);
                const isSelected = selectedSources.includes(source.id);

                return (
                  <button
                    key={source.id}
                    className={`datasource-option ${isSelected ? 'selected' : ''} ${isConnected ? 'connected' : ''}`}
                    onClick={() => !isConnected && handleSourceToggle(source.id)}
                    disabled={isConnected}
                  >
                    <div className="datasource-icon">{source.icon}</div>
                    <span className="datasource-name">{source.name}</span>
                    {isConnected && <span className="connected-badge">Connected</span>}
                    {isSelected && !isConnected && (
                      <span className="checkmark">&#10003;</span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="onboarding-actions">
              <button className="onboarding-cancel" onClick={handleCancel}>
                Cancel
              </button>
              <button className="onboarding-next" onClick={handleNext}>
                Next &gt;
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default Onboarding;
