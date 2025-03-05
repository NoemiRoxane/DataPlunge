import React, { createContext, useContext, useState, useEffect } from 'react';

const DateContext = createContext();

export const DateProvider = ({ children }) => {
  const [dateRange, setDateRange] = useState(() => {
    const savedDateRange = localStorage.getItem("dateRange");
    if (savedDateRange) {
      const parsedDateRange = JSON.parse(savedDateRange);
      return {
        startDate: new Date(parsedDateRange.startDate),
        endDate: new Date(parsedDateRange.endDate),
      };
    }

    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    
    return { startDate: firstDay, endDate: lastDay };
  });

  useEffect(() => {
    if (dateRange.startDate && dateRange.endDate) {
      localStorage.setItem("dateRange", JSON.stringify({
        startDate: dateRange.startDate.toISOString(),
        endDate: dateRange.endDate.toISOString(),
      }));
    }
  }, [dateRange]);

  return (
    <DateContext.Provider value={{ dateRange, setDateRange }}>
      {children}
    </DateContext.Provider>
  );
};

export const useDate = () => useContext(DateContext);
