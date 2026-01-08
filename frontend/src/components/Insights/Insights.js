import React, { useEffect, useState } from 'react';
import './Insights.css';

function Insights({ startDate, endDate }) {
  const [insights, setInsights] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const fetchInsights = async () => {
      if (!startDate || !endDate) {
        console.log('Start or end date not set.');
        setInsights([{ message: 'Please select both start and end dates.' }]);
        return;
      }

      const start = startDate.toISOString().split('T')[0];
      const end = endDate.toISOString().split('T')[0];
      const url = `http://127.0.0.1:5000/insights?start_date=${start}&end_date=${end}`;
      console.log('Fetching insights from:', url); // Log the URL to verify it's correct

      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch insights');
        }
        const data = await response.json();
        console.log("Fetched insights:", data); // Log the data to see what's being loaded
        if (data.length === 0) {
          setInsights([{ message: 'No insights available.' }]);
        } else {
          setInsights(data);
        }
      } catch (error) {
        console.error('Error fetching insights:', error);
        setInsights([{ message: 'Failed to load insights. Please try again later.' }]);
      }
    };

    fetchInsights();
  }, [startDate, endDate]); // Dependency array to trigger re-fetch

  const handleNext = () => {
    if (currentIndex < insights.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  return (
    <div className="insights-container">
      <div className="insights-header">
        <h3>Insights – Supported by AI</h3>
        <img
          src="/pictures/AI_stars.png"
          alt="AI Icon"
          className="icon"
          width="48"
          height="48"
        />
      </div>
      {insights.length > 0 ? (
        <>
          <p className="highlight">Great Job:</p>
          <p className="insight-text">{insights[currentIndex].message}</p>
          <div className="insights-navigation">
            <button onClick={handlePrev} disabled={currentIndex === 0}>
              &lt;
            </button>
            <span>{`${currentIndex + 1} / ${insights.length}`}</span>
            <button onClick={handleNext} disabled={currentIndex === insights.length - 1}>
              &gt;
            </button>
          </div>
        </>
      ) : (
        <p className="insight-text">No insights available.</p>
      )}
    </div>
  );
}

export default Insights;
