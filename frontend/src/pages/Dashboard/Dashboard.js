import React, { useEffect, useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { useSearchParams } from 'react-router-dom';
import Insights from "../../components/Insights/Insights";
import PerformanceChart from "../../components/Performance/PerformanceChart";
import Onboarding from "../../components/Onboarding/Onboarding";
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './dashboard.css';
import { useDate } from '../../context/DateContext';
import { useAuth } from '../../context/AuthContext';
import * as api from '../../utils/api';

// Helper to get user-specific onboarding key
const getOnboardingKey = (userId) => `dataplunge_onboarding_dismissed_${userId}`;


function Dashboard() {
  const { dateRange, setDateRange } = useDate(); // Verwende den DateContext
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [filteredData, setFilteredData] = useState([]); // Gefilterte Daten
  const [aggregatedData, setAggregatedData] = useState([]); // Aggregierte Daten
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);

  // Check URL param for setup wizard trigger (separate effect for immediate response)
  useEffect(() => {
    const openSetup = searchParams.get('setup');
    if (openSetup === 'true') {
      setShowOnboarding(true);
      setOnboardingChecked(true);
      // Clear the param from URL
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('setup');
      setSearchParams(newParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  // Check if user has any data sources and if onboarding was dismissed (initial load only)
  useEffect(() => {
    const checkOnboarding = async () => {
      if (!user) return;

      // Skip if already showing onboarding (from URL param)
      if (showOnboarding) {
        setOnboardingChecked(true);
        return;
      }

      // Check if user has dismissed onboarding before
      const onboardingKey = getOnboardingKey(user.id);
      const wasDismissed = localStorage.getItem(onboardingKey) === 'true';

      if (wasDismissed) {
        setShowOnboarding(false);
        setOnboardingChecked(true);
        return;
      }

      // Check if user has any data sources
      try {
        const datasources = await api.get('/user/datasources');
        // Show onboarding only if user has no data sources AND hasn't dismissed it
        setShowOnboarding(datasources.length === 0);
      } catch (err) {
        console.error('Failed to check data sources:', err);
        setShowOnboarding(false);
      } finally {
        setOnboardingChecked(true);
      }
    };
    checkOnboarding();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Handle onboarding dismissal
  const handleOnboardingDismiss = () => {
    if (user) {
      const onboardingKey = getOnboardingKey(user.id);
      localStorage.setItem(onboardingKey, 'true');
    }
    setShowOnboarding(false);
  };

// Setze beim allerersten Aufruf den aktuellen Monat, danach bleibt das gewählte Datum erhalten
useEffect(() => {
  const savedDateRange = localStorage.getItem("dateRange");
  if (savedDateRange) {
    // Falls der User schon einen Zeitraum gewählt hat, diesen verwenden
    const parsedDateRange = JSON.parse(savedDateRange);
    setDateRange({
      startDate: new Date(parsedDateRange.startDate),
      endDate: new Date(parsedDateRange.endDate),
    });
  } else {
    // Falls es keinen gespeicherten Zeitraum gibt (erster Aufruf), den aktuellen Monat setzen
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    setDateRange({ startDate: firstDay, endDate: lastDay });

    // Direkt in localStorage speichern, damit es erhalten bleibt
    localStorage.setItem("dateRange", JSON.stringify({
      startDate: firstDay.toISOString(),
      endDate: lastDay.toISOString(),
    }));
  }
}, []); // `[]` sorgt dafür, dass es nur beim ersten Rendern ausgeführt wird



  
  // New effect to trigger fetch AFTER state is updated
  useEffect(() => {
    if (dateRange.startDate && dateRange.endDate) {
      fetchFilteredData(dateRange.startDate, dateRange.endDate);
    }
  }, [dateRange]); // This runs after dateRange is set

  const fetchFilteredData = (start, end) => {
    if (!start || !end) {
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

    api.get(`/filter-performance?range=range&value=${value}`)
      .then((response) => {
        console.log('Response status:', response.status);
        if (!response.ok) {
          throw new Error('No data found for the selected range.');
        }
        return response.json();
      })
      .then((data) => {
       // console.log('Data received from backend:', data);
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
          source: item.source || 'Unknown',
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
  };

  
  
  

  return (
    <div className="page-container">
      <ToastContainer />
      {onboardingChecked && showOnboarding && (
        <Onboarding
          onComplete={handleOnboardingDismiss}
          onSkip={handleOnboardingDismiss}
        />
      )}
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
        </div>
        <div className="card">
          <h3>Sessions</h3>
          <p className="value">
            {aggregatedData.length > 0
              ? aggregatedData.reduce((sum, item) => sum + (item.sessions || 0), 0)
              : "0"}
          </p>
        </div>
        <div className="card">
          <h3>Conversions</h3>
          <p className="value">
            {aggregatedData.length > 0
              ? aggregatedData.reduce((sum, item) => sum + (item.conversions || 0), 0)
              : '0'}
          </p>
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
