import React from 'react';

function PerformanceSummary({ data }) {
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
    </div>
  );
}

export default PerformanceSummary;
