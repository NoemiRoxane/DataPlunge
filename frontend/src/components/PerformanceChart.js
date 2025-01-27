import React from 'react';
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Title, Filler } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Tooltip, Title, Filler);

function PerformanceChart({ data }) {
  // Aggregiere die Daten nach Datum
  const aggregatedData = data.reduce((acc, item) => {
    const existing = acc.find((d) => d.date === item.date);
    if (existing) {
      existing.costs += item.costs;
      existing.conversions += item.conversions;
    } else {
      acc.push({
        date: item.date,
        costs: item.costs,
        conversions: item.conversions,
      });
    }
    return acc;
  }, []);

  // Dynamische Labels basierend auf der Filterauswahl
  const chartData = {
    labels: aggregatedData.map((item) => new Date(item.date).toLocaleDateString('en-US')), // Adjust locale as needed
    datasets: [
      {
        label: 'Costs',
        type: 'line',
        data: aggregatedData.map((item) => item.costs),
        borderColor: '#0385B7',
        borderWidth: 2,
        pointBackgroundColor: '#0385B7',
        fill: true,
        backgroundColor: 'rgba(147, 196, 214, 0.4)',
        yAxisID: 'y2',
      },
      {
        label: 'Conversions',
        type: 'bar',
        data: aggregatedData.map((item) => item.conversions),
        backgroundColor: '#00427F',
        borderRadius: 6,
        barPercentage: 0.6,
        categoryPercentage: 0.8,
      },
    ],
  };
  

  

  // Optionen bleiben gleich, aber der Titel wird dynamisch angepasst
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          font: {
            size: 14,
          },
        },
      },
      tooltip: {
        backgroundColor: '#01497c',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
      },
      title: {
        display: true,
        text: `Overall Performance (${data.length > 0 ? 'Filtered Data' : 'Monthly'})`,
        font: {
          size: 24,
          family: 'Fraunces, serif',
          weight: '600',
        },
        color: '#013a63',
        padding: {
          top: 10,
          bottom: 30,
        },
        align: 'start',
      },
    },
    layout: {
      padding: {
        left: 50,
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
          color: '#615E83',
          font: {
            size: 14,
            family: 'Inter',
          },
        },
      },
      y2: {
        type: 'linear',
        position: 'right',
        grid: {
          drawOnChartArea: false,
        },
        title: {
          display: true,
          text: 'Cost per Conversion',
          color: '#615E83',
          font: {
            size: 14,
            family: 'Inter',
          },
        },
      },
    },
  };

  return (
    <div style={{ width: '100%', height: '450px' }}>
      {aggregatedData.length > 0 ? <Bar data={chartData} options={chartOptions} /> : <p>Loading chart...</p>}
    </div>
  );
}

export default PerformanceChart;
