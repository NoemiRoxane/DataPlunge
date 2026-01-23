import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../../utils/api';
import './DataSourcesManager.css';

function DataSourcesManager() {
  const [datasources, setDatasources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchDataSources();
  }, []);

  const fetchDataSources = async () => {
    try {
      const data = await api.get('/user/datasources');
      setDatasources(data);
    } catch (err) {
      console.error('Failed to fetch data sources:', err);
      setError('Failed to load data sources');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async (datasourceId, sourceName) => {
    if (!window.confirm(`Are you sure you want to disconnect ${sourceName}? This will delete all associated campaigns and performance data.`)) {
      return;
    }

    try {
      await api.del(`/user/datasources/${datasourceId}`);
      setDatasources(datasources.filter(ds => ds.id !== datasourceId));
    } catch (err) {
      console.error('Failed to disconnect data source:', err);
      alert('Failed to disconnect data source. Please try again.');
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'connected':
        return 'status-connected';
      case 'expired':
        return 'status-expired';
      case 'error':
        return 'status-error';
      default:
        return 'status-unknown';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="datasources-container">
        <h1>Data Sources</h1>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="datasources-container">
      <div className="datasources-header">
        <h1>Data Sources</h1>
        <button
          className="add-datasource-button"
          onClick={() => navigate('/add-data-source')}
        >
          + Add New Data Source
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {datasources.length === 0 ? (
        <div className="empty-state">
          <h3>No Data Sources Connected</h3>
          <p>Connect your first data source to start tracking your campaign performance.</p>
          <button
            className="add-datasource-button-large"
            onClick={() => navigate('/add-data-source')}
          >
            + Add Data Source
          </button>
        </div>
      ) : (
        <div className="datasources-grid">
          {datasources.map((ds) => (
            <div key={ds.id} className="datasource-card">
              <div className="datasource-card-header">
                <h3>{ds.source_name}</h3>
                <span className={`status-badge ${getStatusBadgeClass(ds.status)}`}>
                  {ds.status}
                </span>
              </div>

              <div className="datasource-card-body">
                <div className="datasource-info">
                  <div className="info-row">
                    <span className="info-label">Connected:</span>
                    <span className="info-value">{formatDate(ds.created_at)}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Last Sync:</span>
                    <span className="info-value">{formatDate(ds.last_sync)}</span>
                  </div>
                </div>
              </div>

              <div className="datasource-card-footer">
                <button
                  className="disconnect-button"
                  onClick={() => handleDisconnect(ds.id, ds.source_name)}
                >
                  Disconnect
                </button>
                {ds.status === 'expired' && (
                  <button
                    className="reconnect-button"
                    onClick={() => navigate('/add-data-source')}
                  >
                    Reconnect
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DataSourcesManager;
