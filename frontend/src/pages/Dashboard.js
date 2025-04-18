import React, { useEffect, useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import PerformanceChart from '../components/PerformanceChart';
import Insights from '../components/Insights';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './dashboard.css';
import { useDate } from './DateContext'; // Importiere den useDate Hook

function Dashboard() {
  const { dateRange, setDateRange } = useDate(); // Verwende den DateContext
  const [filteredData, setFilteredData] = useState([]); // Gefilterte Daten
  const [aggregatedData, setAggregatedData] = useState([]); // Aggregierte Daten

  // Setze den aktuellen Monat als Default
  useEffect(() => {
    const today = new Date();
    const firstDay = new Date(Date.UTC(today.getFullYear(), today.getMonth(), 1)); // Erster Tag des Monats (UTC)
    const lastDay = new Date(Date.UTC(today.getFullYear(), today.getMonth() + 1, 0)); // Letzter Tag des Monats (UTC)
    setDateRange({ startDate: firstDay, endDate: lastDay });
    fetchFilteredData(firstDay, lastDay); // Lade Daten für den aktuellen Monat
  }, [setDateRange]);

  const fetchFilteredData = (start = dateRange.startDate, end = dateRange.endDate) => {
    if (!start || !end) {
      console.log('Start or end date is missing.');
      toast.error('Please select both start and end dates.');
      return;
    }

    const normalizedStart = start.toISOString().split('T')[0];
    const normalizedEnd = end.toISOString().split('T')[0];
    const value = `${normalizedStart}|${normalizedEnd}`;

    // Debugging Logs
    console.log('Selected Start Date:', start);
    console.log('Selected End Date:', end);
    console.log('Computed Value for API:', value);

    fetch(`http://127.0.0.1:5000/filter-performance?range=range&value=${value}`)
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
    // Step 1: Generate all dates in the range
    const allDates = [];
    const startDate = new Date(dateRange.startDate);
    const endDate = new Date(dateRange.endDate);
    let currentDate = new Date(startDate);
  
    while (currentDate <= endDate) {
      allDates.push(currentDate.toISOString().split('T')[0]); // Ensure dates are in YYYY-MM-DD format
      currentDate.setDate(currentDate.getDate() + 1); // Increment to the next day
    }
  
    // Step 2: Aggregate existing data
    const aggregated = data.reduce((acc, item) => {
      const formattedDate = new Date(item.date).toISOString().split('T')[0]; // Ensure consistent date format
      const existing = acc.find((d) => d.date === formattedDate);
      if (existing) {
        existing.costs += parseFloat(item.costs) || 0;
        existing.conversions += parseInt(item.conversions, 10) || 0;
        existing.impressions += parseInt(item.impressions, 10) || 0;
        existing.clicks += parseInt(item.clicks, 10) || 0;
        existing.sessions += parseInt(item.sessions, 10) || 0;
      } else {
        acc.push({
          date: formattedDate,
          costs: parseFloat(item.costs) || 0,
          conversions: parseInt(item.conversions, 10) || 0,
          impressions: parseInt(item.impressions, 10) || 0,
          clicks: parseInt(item.clicks, 10) || 0,
          sessions: parseInt(item.sessions, 10) || 0,
        });
      }
      return acc;
    }, []);
  
    // Step 3: Fill missing dates with zero values
    const filledData = allDates.map((date) => {
      const existing = aggregated.find((item) => item.date === date);
      return (
        existing || {
          date,
          costs: 0,
          conversions: 0,
          impressions: 0,
          clicks: 0,
          sessions: 0,
        }
      );
    });
  
    // Step 4: Sort by date (ascending)
    const sortedFilledData = filledData.sort((a, b) => new Date(a.date) - new Date(b.date));
  
    setAggregatedData(sortedFilledData);
  };
  
  
  

  const handleDateChange = (dates) => {
    const [start, end] = dates;
    setDateRange({ startDate: start, endDate: end });
    fetchFilteredData(start, end);
  };

  return (
    <div className="page-container">
      <ToastContainer />
      <header className="page-header">
        <h1>Performance Overall</h1>
        <div className="header-controls">
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <DatePicker
              selected={dateRange.startDate}
              onChange={handleDateChange}
              selectsRange
              startDate={dateRange.startDate}
              endDate={dateRange.endDate}
              placeholderText="Select date range"
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
              ? aggregatedData.reduce((sum, item) => sum + (item.costs || 0), 0).toFixed(2)
              : '0.00'}
          </p>
          <span className="trend positive">+20% month over month</span>
        </div>
        <div className="card">
          <h3>Conversions</h3>
          <p className="value">
            {aggregatedData.length > 0
              ? aggregatedData.reduce((sum, item) => sum + (item.conversions || 0), 0)
              : '0'}
          </p>
          <span className="trend positive">+33% month over month</span>
        </div>
        <div className="card">
          <h3>Cost per Conversion</h3>
          <p className="value">
            {aggregatedData.length > 0 &&
            aggregatedData.reduce((sum, item) => sum + (item.conversions || 0), 0) > 0
              ? (
                  aggregatedData.reduce((sum, item) => sum + (item.costs || 0), 0) /
                  aggregatedData.reduce((sum, item) => sum + (item.conversions || 0), 0)
                ).toFixed(2)
              : '0.00'}
          </p>
          <span className="trend negative">-8% month over month</span>
        </div>
      </section>
      <section className="chart-insights">
        <div className="chart-container">
          <PerformanceChart data={aggregatedData} />
        </div>
        <Insights startDate={dateRange.startDate} endDate={dateRange.endDate} />
      </section>
    </div>
  );
}

export default Dashboard;
