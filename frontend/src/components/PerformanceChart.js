import React from 'react';
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Tooltip);

function PerformanceChart({ data }) {
  const chartData = {
    labels: data.map((item) => item.date),
    datasets: [
      {
        label: 'Conversions',
        type: 'bar',
        data: data.map((item) => item.conversions),
        backgroundColor: 'rgba(0, 113, 188, 0.8)', // Blau
        borderColor: 'rgba(0, 75, 141, 1)', // Dunkleres Blau
        borderWidth: 1,
        barPercentage: 0.6,
        categoryPercentage: 0.8,
      },
      {
        label: 'Costs',
        type: 'line',
        data: data.map((item) => item.costs),
        borderColor: '#004b8d', // Dunkelblau für die Linie
        borderWidth: 2,
        pointBackgroundColor: '#004b8d',
        pointBorderColor: '#004b8d',
        tension: 0.4, // Glättung der Linie
        yAxisID: 'y2',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      tooltip: {
        backgroundColor: '#004b8d',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
      },
    },
    scales: {
      x: {
        ticks: {
          font: {
            size: 12,
          },
        },
        grid: {
          display: false,
        },
      },
      y: {
        type: 'linear',
        position: 'left',
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        title: {
          display: true,
          text: 'Conversions',
        },
      },
      y2: {
        type: 'linear',
        position: 'right',
        grid: {
          drawOnChartArea: false, // Gitterlinien für die zweite Achse deaktivieren
        },
        title: {
          display: true,
          text: 'Costs',
        },
      },
    },
  };

  return (
    <div style={{ width: '100%', height: '450px' }}>
      {data.length > 0 ? <Bar data={chartData} options={chartOptions} /> : <p>Loading chart...</p>}
    </div>
  );
}

export default PerformanceChart;
