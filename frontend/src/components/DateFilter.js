import React from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { useDate } from '../context/DateContext';

const DateFilter = ({ fetchFilteredData }) => {
  const { dateRange, setDateRange } = useDate();

  const handleDateChange = (dates) => {
    const [start, end] = dates;
    if (start && end) {
      setDateRange({ startDate: start, endDate: end });
      fetchFilteredData(start, end);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <DatePicker
        selected={dateRange.startDate}
        onChange={handleDateChange}
        selectsRange
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        placeholderText="Select date range"
        isClearable
      />
      <button className="ok-button" onClick={() => fetchFilteredData(dateRange.startDate, dateRange.endDate)}>
        OK
      </button>
    </div>
  );
};

export default DateFilter;
