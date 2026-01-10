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
        setCurrentIndex(0); // ✅ reset
        return;
      }
  
      try {
        const response = await fetch(
          `http://127.0.0.1:5000/insights?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`
        );
  
        const data = await response.json();
  
        if (Array.isArray(data)) {
          setInsights(data.length ? data : [{ message: 'No insights available.' }]);
        } else if (data?.error) {
          setInsights([{ message: data.error }]);
        } else {
          setInsights([{ message: 'Unexpected insights response.' }]);
        }
  
        setCurrentIndex(0); // ✅ WICHTIG: immer resetten bei neuen Insights
      } catch (error) {
        console.error('Error fetching insights:', error);
        setInsights([{ message: 'Failed to load insights.' }]);
        setCurrentIndex(0); // ✅ auch hier
      }
    };
  
    fetchInsights();
  }, [startDate, endDate]);
  

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
