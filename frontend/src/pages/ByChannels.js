import React from 'react';
import { useNavigate } from 'react-router-dom';
import Insights from '../components/Insights';
import './ByChannels.css';

function ByChannels() {
  const navigate = useNavigate();

  const tableData = [
    { source: "Google Ads", costs: "CHF4,046.25", impressions: "1,235,354", clicks: 3903, costPerClick: "CHF1.03", sessions: 3976, conversions: 199, costPerConversion: "CHF20.3" },
    { source: "Meta Ads", costs: "CHF2,546.14", impressions: "2,221,786", clicks: 3129, costPerClick: "CHF0.81", sessions: 2143, conversions: 89, costPerConversion: "CHF28.6" },
    { source: "Microsoft Ads", costs: "CHF903.30", impressions: "605,978", clicks: 699, costPerClick: "CHF1.29", sessions: 640, conversions: 60, costPerConversion: "CHF15.1" },
    { source: "Manually added (via GA4)", costs: "CHF1,000", impressions: "-", clicks: 540, costPerClick: "CHF1.85", sessions: 513, conversions: 45, costPerConversion: "CHF22.8" },
    { source: "Manually added (via GA4)", costs: "CHF412", impressions: "-", clicks: 412, costPerClick: "CHF1.50", sessions: 412, conversions: 18, costPerConversion: "CHF22.8" },
  ];

  const insightsList = [
    "Over the last 6 days there was a conversion growth trend from 15%.",
  ];

  return (
    <div className="page-container">
      <header className="page-header">
        <h1>Performance by Channel</h1>
      </header>
      <div className="export-controls">
        <button className="export-button">Export</button>
      </div>
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
                <td>{row.costs}</td>
                <td>{row.impressions}</td>
                <td>{row.clicks}</td>
                <td>{row.costPerClick}</td>
                <td>{row.sessions}</td>
                <td>{row.conversions}</td>
                <td>{row.costPerConversion}</td>
              </tr>
            ))}
            <tr className="total-row">
              <td>Total</td>
              <td>CHF8,907</td>
              <td>9,5169,27</td>
              <td>8,683</td>
              <td>CHF1.03</td>
              <td>7,684</td>
              <td>411</td>
              <td>CHF21.7</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div className="bottom-section">
        <div className="button-group">
          <button className="cta-button" onClick={() => navigate('/add-data-source')}>
            Add Channel or Costs via Data Source
          </button>
          <button className="cta-button">Add Channel or Costs manually</button>
        </div>
        <div className="insights-section">
          <Insights insightsList={insightsList} />
        </div>
      </div>
    </div>
  );
}

export default ByChannels;
