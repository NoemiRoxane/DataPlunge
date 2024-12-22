import React, { useState } from 'react';

function Insights({ insightsList }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleNext = () => {
    if (currentIndex < insightsList.length - 1) {
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
      <h3 className="insights-header">
        Insights
        <img
          src={require('../pages/AI_stars.png')}
          alt="Icon"
          className="icon"
          width="48"
          height="48"
        />
      </h3>
      <p className="highlight">Great Job:</p>
      <p className="insight-text">{insightsList[currentIndex]}</p>
      <div className="insights-navigation">
        <button onClick={handlePrev} disabled={currentIndex === 0}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
        <span>{`${currentIndex + 1} / ${insightsList.length}`}</span>
        <button onClick={handleNext} disabled={currentIndex === insightsList.length - 1}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default Insights;
