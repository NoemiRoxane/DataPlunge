import React, { useEffect, useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import PerformanceChart from '../components/PerformanceChart';
import Insights from '../components/Insights';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './dashboard.css';

function Dashboard() {
  const [filteredData, setFilteredData] = useState([]); // Gefilterte Daten
  const [aggregatedData, setAggregatedData] = useState([]); // Aggregierte Daten
  const [startDate, setStartDate] = useState(null); // Startdatum
  const [endDate, setEndDate] = useState(null); // Enddatum

  // Setze den aktuellen Monat als Default
  useEffect(() => {
    const today = new Date();
    const firstDay = new Date(Date.UTC(today.getFullYear(), today.getMonth(), 1)); // Erster Tag des Monats (UTC)
    const lastDay = new Date(Date.UTC(today.getFullYear(), today.getMonth() + 1, 0)); // Letzter Tag des Monats (UTC)
    setStartDate(firstDay);
    setEndDate(lastDay);
    fetchFilteredData(firstDay, lastDay); // Lade Daten für den aktuellen Monat
  }, []);

  const fetchFilteredData = (start = startDate, end = endDate) => {
    if (!start) {
        console.log('Start date is missing.');
        toast.error('Please select at least a start date.');
        return;
    }

    // Lokale Zeit auf UTC normalisieren, mit Fallback für das Enddatum
    const normalizedStart = new Date(Date.UTC(start.getFullYear(), start.getMonth(), start.getDate()));
    const normalizedEnd = end
        ? new Date(Date.UTC(end.getFullYear(), end.getMonth(), end.getDate()))
        : null;

    let range = 'day';
    let value = normalizedStart.toISOString().split('T')[0];

    // Wenn ein Enddatum angegeben ist oder das Startdatum als Enddatum verwendet wird
    if (end || !end) {
        range = 'range';
        value = `${normalizedStart.toISOString().split('T')[0]}|${(normalizedEnd || normalizedStart).toISOString().split('T')[0]}`;
    }

    // Debugging Logs
    console.log('---- Debug Logs ----');
    console.log('Selected Start Date:', start);
    console.log('Normalized Start Date:', normalizedStart);
    console.log('Selected End Date:', end || 'No end date provided, using start date as end date');
    console.log('Normalized End Date:', normalizedEnd || normalizedStart);
    console.log('Computed Range:', range);
    console.log('Computed Value for API:', value);

    fetch(`http://127.0.0.1:5000/filter-performance?range=${range}&value=${value}`)
        .then((response) => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error('No data found for the selected range.');
            }
            return response.json();
        })
        .then((data) => {
            console.log('Data received from backend:', data);
            if (data.length === 0) {
                console.log('No data found for the selected range (empty array).');
                throw new Error('No data found for the selected range.');
            }
            setFilteredData(data);
            aggregateData(data);
            toast.dismiss();
        })
        .catch((error) => {
            console.error('Error occurred:', error.message);
            setFilteredData([]);
            setAggregatedData([]);
            toast.error(error.message, {
                position: 'top-right',
                autoClose: 5000,
                hideProgressBar: true,
                closeOnClick: true,
                pauseOnHover: true,
                draggable: true,
                progress: undefined,
                theme: 'colored',
            });
        });
};



  // Funktion zur Aggregation der Daten
  const aggregateData = (data) => {
    const aggregated = data.reduce((acc, item) => {
      const existing = acc.find((d) => d.date === item.date);
      if (existing) {
        existing.costs += item.costs;
        existing.conversions += item.conversions;
        existing.impressions = (existing.impressions || 0) + (item.impressions || 0);
        existing.clicks = (existing.clicks || 0) + (item.clicks || 0);
        existing.sessions = (existing.sessions || 0) + (item.sessions || 0);
      } else {
        acc.push({ ...item });
      }
      return acc;
    }, []);
    setAggregatedData(aggregated);
  };

  return (
    <div className="page-container">
      <ToastContainer />
      <header className="page-header">
        <h1>Performance Overall</h1>
        <div className="header-controls">
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <DatePicker
              selected={startDate}
              onChange={(date) => {
                  if (date) {
                      const correctedDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
                      console.log('Selected Start Date (corrected to UTC):', correctedDate);
                      setStartDate(correctedDate);
                  } else {
                      console.log('Start date cleared');
                      setStartDate(null);
                  }
              }}
              selectsStart
              startDate={startDate}
              endDate={endDate}
              placeholderText="Start Date"
          />
          <DatePicker
              selected={endDate}
              onChange={(date) => {
                  if (date) {
                      const correctedDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
                      console.log('Selected End Date (corrected to UTC):', correctedDate);
                      setEndDate(correctedDate);
                  } else {
                      console.log('End date cleared, using start date as end date');
                      setEndDate(null);
                  }
              }}
              selectsEnd
              startDate={startDate}
              endDate={endDate}
              placeholderText="End Date (optional)"
              isClearable
          />

            <button className="ok-button" onClick={() => fetchFilteredData()}>
              OK
            </button>
          </div>
        </div>
      </header>
      <section className="summary-cards">
        <div className="card">
          <h3>Costs</h3>
          <p className="value">
            ${aggregatedData.length > 0
              ? aggregatedData.reduce((sum, item) => sum + item.costs, 0).toFixed(2)
              : 'Loading...'}
          </p>
          <span className="trend positive">+20% month over month</span>
        </div>
        <div className="card">
          <h3>Conversions</h3>
          <p className="value">
            {aggregatedData.length > 0
              ? aggregatedData.reduce((sum, item) => sum + item.conversions, 0)
              : 'Loading...'}
          </p>
          <span className="trend positive">+33% month over month</span>
        </div>
        <div className="card">
          <h3>Cost per Conversion</h3>
          <p className="value">
            {aggregatedData.length > 0
              ? (
                  aggregatedData.reduce((sum, item) => sum + item.costs, 0) /
                  aggregatedData.reduce((sum, item) => sum + item.conversions, 0)
                ).toFixed(2)
              : 'Loading...'}
          </p>
          <span className="trend negative">-8% month over month</span>
        </div>
      </section>
      <section className="chart-insights">
        <div className="chart-container">
          <PerformanceChart data={aggregatedData} />
        </div>
        <Insights apiUrl="http://127.0.0.1:5000/insights" />
      </section>
    </div>
  );
}

export default Dashboard;
