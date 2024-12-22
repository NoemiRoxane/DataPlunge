import React, { useEffect, useState } from 'react';
import PerformanceChart from '../components/PerformanceChart';
import Insights from '../components/Insights';
import './dashboard.css';

function Dashboard() {
  const [data, setData] = useState([]);
  const [insightsList, setInsightsList] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/performance')
      .then((response) => response.json())
      .then((data) => {
        setData(data);
        const insights = calculateInsights(data);
        setInsightsList(insights);
      })
      .catch((error) => console.error('Error fetching data:', error));
  }, []);

  const calculateInsights = (data) => {
    if (data.length === 0) return ['Not enough data to calculate insights.'];
    const insights = [];

    const growth =
      ((data[data.length - 1].conversions - data[0].conversions) / data[0].conversions) *
      100;
    insights.push(
      `Over the last ${data.length} days, conversions grew by ${growth.toFixed(2)}%.`
    );

    return insights;
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Performance Overall</h1>
        <div className="header-controls">
          <input type="date" className="date-picker" />
          <button className="export-button">Export</button>
        </div>
      </header>
      <section className="summary-cards">
        <div className="card">
          <h3>Costs</h3>
          <p className="value">
            ${data.length > 0
              ? data.reduce((sum, item) => sum + item.costs, 0).toFixed(2)
              : 'Loading...'}
          </p>
          <span className="trend positive">+20% month over month</span>
        </div>
        <div className="card">
          <h3>Conversions</h3>
          <p className="value">
            {data.length > 0
              ? data.reduce((sum, item) => sum + item.conversions, 0)
              : 'Loading...'}
          </p>
          <span className="trend positive">+33% month over month</span>
        </div>
        <div className="card">
          <h3>Cost per Conversion</h3>
          <p className="value">
            {data.length > 0
              ? (
                  data.reduce((sum, item) => sum + item.costs, 0) /
                  data.reduce((sum, item) => sum + item.conversions, 0)
                ).toFixed(2)
              : 'Loading...'}
          </p>
          <span className="trend negative">-8% month over month</span>
        </div>
      </section>
      <section className="chart-insights">
        <div className="chart-container">
          <PerformanceChart data={data} />
        </div>
        <div className="insights-container">
          <Insights insightsList={insightsList} />
        </div>
      </section>
    </div>
  );
}

export default Dashboard;