import React, { useEffect, useState } from 'react';
import PerformanceChart from '../components/PerformanceChart';
import Insights from '../components/Insights';
import './dashboard.css';

function Dashboard() {
  const [monthlyData, setMonthlyData] = useState([]);

  useEffect(() => {
    // Fetch data from the monthly_performance endpoint
    fetch('http://127.0.0.1:5000/monthly-performance')
      .then((response) => response.json())
      .then((data) => setMonthlyData(data))
      .catch((error) => console.error('Error fetching monthly performance data:', error));
  }, []);

  return (
    <div className="page-container">
      <header className="page-header">
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
            ${monthlyData.length > 0
              ? monthlyData.reduce((sum, item) => sum + item.costs, 0).toFixed(2)
              : 'Loading...'}
          </p>
          <span className="trend positive">+20% month over month</span>
        </div>
        <div className="card">
          <h3>Conversions</h3>
          <p className="value">
            {monthlyData.length > 0
              ? monthlyData.reduce((sum, item) => sum + item.conversions, 0)
              : 'Loading...'}
          </p>
          <span className="trend positive">+33% month over month</span>
        </div>
        <div className="card">
          <h3>Cost per Conversion</h3>
          <p className="value">
            {monthlyData.length > 0
              ? (
                  monthlyData.reduce((sum, item) => sum + item.costs, 0) /
                  monthlyData.reduce((sum, item) => sum + item.conversions, 0)
                ).toFixed(2)
              : 'Loading...'}
          </p>
          <span className="trend negative">-8% month over month</span>
        </div>
      </section>
      <section className="chart-insights">
        <div className="chart-container">
          <PerformanceChart data={monthlyData} />
        </div>
        <Insights apiUrl="http://127.0.0.1:5000/insights" />
      </section>
    </div>
  );
}

export default Dashboard;
