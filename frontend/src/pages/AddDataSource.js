import React from 'react';
import './AddDataSource.css';

const dataSources = [
  { name: "Google Ads", icon: "🟢" },
  { name: "Microsoft Advertising", icon: "🟢" },
  { name: "Facebook Ads", icon: "🔵" },
  { name: "Google Analytics", icon: "📊" },
  { name: "LinkedIn", icon: "🔗" },
  { name: "Pinterest", icon: "📌" },
  { name: "Reddit", icon: "👽" },
  { name: "Snapchat", icon: "👻" },
  { name: "TikTok", icon: "🎵" },
  { name: "X Ads", icon: "❌" },
];

function AddDataSource() {
  const handleConnect = async (source) => {
    try {
      const response = await fetch('http://localhost:5000/add-data-source', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: source.name }),
      });
      const data = await response.json();
      if (response.ok) {
        alert(`Successfully connected: ${source.name}`);
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error('Error connecting data source:', error);
      alert('Failed to connect data source');
    }
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <h1>Connect Data Source</h1>
      </header>
      <div className="data-source-grid">
        {dataSources.map((source, index) => (
          <div key={index} className="data-source-card">
            <span className="data-source-icon">{source.icon}</span>
            <h3>{source.name}</h3>
            <button
              className="connect-button"
              onClick={() => handleConnect(source)}
            >
              Connect Now
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AddDataSource;
