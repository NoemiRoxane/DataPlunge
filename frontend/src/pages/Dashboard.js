import React, { useEffect, useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import PerformanceChart from '../components/PerformanceChart';
import Insights from '../components/Insights';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './dashboard.css';

// Funktion zur lokalen Formatierung des Datums (YYYY-MM-DD)
const formatDateToLocal = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0'); // Monate beginnen bei 0
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`; // Format: YYYY-MM-DD
};

function Dashboard() {
  const [filteredData, setFilteredData] = useState([]); // Gefilterte Daten
  const [aggregatedData, setAggregatedData] = useState([]); // Aggregierte Daten
  const [startDate, setStartDate] = useState(null); // Startdatum
  const [endDate, setEndDate] = useState(null); // Enddatum

  // Funktion zur Überwachung von filteredData
  useEffect(() => {
    console.log('Filtered Data:', filteredData); // Debug-Ausgabe für gefilterte Daten
  }, [filteredData]);

  // Funktion, um gefilterte Daten zu holen
  const fetchFilteredData = () => {
    if (!startDate) {
      toast.error('Please select at least a start date.');
      return;
    }

    const range = startDate && endDate ? 'range' : 'day';
    const value = startDate && endDate
      ? `${formatDateToLocal(startDate)}|${formatDateToLocal(endDate)}`
      : formatDateToLocal(startDate);

    console.log('Requesting data for range:', range, 'value:', value);

    fetch(`http://127.0.0.1:5000/filter-performance?range=${range}&value=${value}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('No data found for the selected range.');
        }
        return response.json();
      })
      .then((data) => {
        console.log('Received data:', data);
        if (data.length === 0) {
          throw new Error('No data found for the selected range.');
        }
        setFilteredData(data);
        aggregateData(data);
        toast.dismiss();
      })
      .catch((error) => {
        setFilteredData([]);
        setAggregatedData([]);
        console.error(error.message);
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
          {/* Zeitfensterauswahl */}
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <DatePicker
              selected={startDate}
              onChange={(date) => setStartDate(date)}
              selectsStart
              startDate={startDate}
              endDate={endDate}
              placeholderText="Start Date"
            />
            <DatePicker
              selected={endDate}
              onChange={(date) => setEndDate(date)}
              selectsEnd
              startDate={startDate}
              endDate={endDate}
              placeholderText="End Date (optional)"
              isClearable
            />
            <button className="ok-button" onClick={fetchFilteredData}>
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
