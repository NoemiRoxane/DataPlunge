import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import Insights from '../components/Insights';
import './ByChannels.css';
import { useDate } from './DateContext'; // Importiere den useDate Hook

function ByChannels() {
  const navigate = useNavigate();
  const { dateRange, setDateRange } = useDate(); // Zugriff auf den DateContext
  const [tableData, setTableData] = useState([]);

  useEffect(() => {
    if (dateRange.startDate && dateRange.endDate) {
      const start = dateRange.startDate.toISOString().split('T')[0];
      const end = dateRange.endDate.toISOString().split('T')[0];

      console.log(`Fetching data for range: ${start} to ${end}`); // Debugging Log

      fetch(`http://127.0.0.1:5000/aggregated-performance?start_date=${start}&end_date=${end}`)
        .then(response => {
          console.log(`Response status: ${response.status}`);
          if (!response.ok) {
            throw new Error('Failed to fetch data');
          }
          return response.json();
        })
        .then(data => {
          console.log('Received data:', data); // Debugging Log
          if (Array.isArray(data) && data.length > 0) {
            setTableData(data);
          } else {
            console.warn('No data available for the selected range.');
            setTableData([]); // Leere Tabelle, falls keine Daten zurückkommen
          }
        })
        .catch(error => {
          console.error('Error fetching channel data:', error);
          setTableData([]); // Leere Tabelle bei Fehler
        });
    }
  }, [dateRange.startDate, dateRange.endDate]);

  const handleDateChange = (dates) => {
    const [start, end] = dates;
    setDateRange({ startDate: start, endDate: end });
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <h1>Performance by Channel</h1>
        <div className="header-controls" style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
          <DatePicker
            selected={dateRange.startDate}
            onChange={handleDateChange}
            selectsRange
            startDate={dateRange.startDate}
            endDate={dateRange.endDate}
            placeholderText="Select date range"
            isClearable
          />
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
            {tableData.length > 0 ? (
              tableData.map((row, index) => (
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
              ))
            ) : (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center' }}>
                  No data available for the selected date range.
                </td>
              </tr>
            )}
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
          <Insights startDate={dateRange.startDate} endDate={dateRange.endDate} />
        </div>
      </div>
    </div>
  );
}

export default ByChannels;
