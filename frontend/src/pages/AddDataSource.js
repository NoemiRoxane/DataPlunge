import React from 'react';
import './AddDataSource.css';

const dataSources = [
  { name: "Google Ads", icon: "🟢" },
  { name: "Microsoft Advertising", icon: "🟢" },
];

function AddDataSource() {
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
            <button className="connect-button">Connect Now</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AddDataSource;
