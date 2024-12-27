import React, { useEffect, useState } from 'react';
import './Insights.css';

function Insights({ apiUrl }) {
  const [insights, setInsights] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error('Failed to fetch insights');
        }
        const data = await response.json();
        setInsights(data);
      } catch (error) {
        console.error('Error fetching insights:', error);
        setInsights(['Failed to load insights. Please try again later.']);
      }
    };

    fetchInsights();
  }, [apiUrl]);

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
          src={require('./AI_stars.png')}
          alt="AI Icon"
          className="icon"
          width="48"
          height="48"
        />
      </div>
      {insights.length > 0 ? (
        <>
          <p className="highlight">Great Job:</p>
          <p className="insight-text">{insights[currentIndex]}</p>
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
