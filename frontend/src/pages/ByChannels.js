import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Insights from '../components/Insights';
import './ByChannels.css';

function ByChannels() {
  const navigate = useNavigate();
  const [tableData, setTableData] = useState([]);
  const [insightsApiUrl] = useState('http://127.0.0.1:5000/insights');

  useEffect(() => {
    // Aggregated API-Endpoint verwenden
    fetch('http://127.0.0.1:5000/aggregated-performance')
      .then((response) => response.json())
      .then((data) => setTableData(data))
      .catch((error) => console.error('Error fetching table data:', error));
  }, []);

  return (
    <div className="page-container">
      <header className="page-header">
        <h1>Performance by Channel</h1>
        <div className="header-controls">
          <input type="date" className="date-picker" />
          <button className="export-button">Export</button>
        </div>
      </header>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Traffic Source</th>
              <th>Costs</th>
              <th>Impressions</th>
              <th>Clicks</th>
              <th>Cost per Click</th>
              <th>Sessions</th>
              <th>Conversions</th>
              <th>Cost per Conversion</th>
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, index) => (
              <tr key={index}>
                <td>{row.source}</td>
                <td>{row.costs ? row.costs.toFixed(2) : '--'}</td>
                <td>{row.impressions ?? '--'}</td>
                <td>{row.clicks ?? '--'}</td>
                <td>{row.cost_per_click ? row.cost_per_click.toFixed(2) : '--'}</td>
                <td>{row.sessions ?? '--'}</td>
                <td>{row.conversions ?? '--'}</td>
                <td>{row.cost_per_conversion ? row.cost_per_conversion.toFixed(2) : '--'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="bottom-section">
        <div className="button-group">
          <button
            className="cta-button"
            onClick={() => navigate('/add-data-source')}
          >
            Add Channel or Costs via Data Source
          </button>
          <button className="cta-button">Add Channel or Costs manually</button>
        </div>
        <div className="insights-section">
          <Insights apiUrl={insightsApiUrl} />
        </div>
      </div>
    </div>
  );
}

export default ByChannels;
