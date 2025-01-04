import React from 'react';

function PerformanceSummary({ data }) {
  // Berechnung der Metriken
  const totalCosts = data.length > 0
    ? data.reduce((sum, item) => sum + item.costs, 0).toFixed(2)
    : 'Loading...';

  const totalConversions = data.length > 0
    ? data.reduce((sum, item) => sum + item.conversions, 0)
    : 'Loading...';

  const costPerConversion = data.length > 0
    ? (
        data.reduce((sum, item) => sum + item.costs, 0) /
        data.reduce((sum, item) => sum + item.conversions, 0)
      ).toFixed(2)
    : 'Loading...';

  const totalImpressions = data.length > 0
    ? data.reduce((sum, item) => sum + (item.impressions || 0), 0)
    : 'Loading...';

  const totalClicks = data.length > 0
    ? data.reduce((sum, item) => sum + (item.clicks || 0), 0)
    : 'Loading...';

  const totalSessions = data.length > 0
    ? data.reduce((sum, item) => sum + (item.sessions || 0), 0)
    : 'Loading...';

  const costPerClick = data.length > 0
    ? (
        data.reduce((sum, item) => sum + item.costs, 0) /
        data.reduce((sum, item) => sum + (item.clicks || 1), 0)
      ).toFixed(2)
    : 'Loading...';

  return (
    <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '20px' }}>
      <div>
        <h3>Costs</h3>
        <p>${totalCosts}</p>
      </div>
      <div>
        <h3>Conversions</h3>
        <p>{totalConversions}</p>
      </div>
      <div>
        <h3>Cost per Conversion</h3>
        <p>${costPerConversion}</p>
      </div>
      <div>
        <h3>Impressions</h3>
        <p>{totalImpressions}</p>
      </div>
      <div>
        <h3>Clicks</h3>
        <p>{totalClicks}</p>
      </div>
      <div>
        <h3>Sessions</h3>
        <p>{totalSessions}</p>
      </div>
      <div>
        <h3>Cost per Click</h3>
        <p>${costPerClick}</p>
      </div>
    </div>
  );
}
console.log('PerformanceSummary data:', data);


export default PerformanceSummary;
