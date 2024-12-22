import React from 'react';
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Title, Filler } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Tooltip, Title, Filler);

function PerformanceChart({ data }) {
  const chartData = {
    labels: data.map((item) => item.date),
    datasets: [
      {
        label: 'Costs',
        type: 'line',
        data: data.map((item) => item.costs),
        borderColor: 'rgba(0,0,0,0)', // Unsichtbare Linie
        borderWidth: 0, // Keine Linie
        pointBackgroundColor: '#0385B7', // Innere Punkt-Füllfarbe (Blau)
        pointBorderColor: '#FFFFFF', // Äußere Punkt-Umrandung (Weiß)
        pointBorderWidth: 3, // Dicke der äußeren Umrandung
        pointRadius: 8, // Punktgröße
        pointHoverRadius: 10, // Größere Punkte beim Hover
        fill: true,
        backgroundColor: 'rgba(147, 196, 214, 0.4)', // Halbtransparente Füllung
        tension: 0.4, // Glättung der Linie (hat keinen Effekt mehr, da die Linie unsichtbar ist)
        yAxisID: 'y2',
      },
      {
        label: 'Conversions',
        type: 'bar',
        data: data.map((item) => item.conversions),
        backgroundColor: '#00427F', // Füllfarbe der Balken
        borderRadius: 6, // Abgerundete Ecken für Balken
        borderSkipped: false,
        barPercentage: 0.6,
        categoryPercentage: 0.8,
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
        text: 'Overall Performance',
        font: {
          size: 24,
          family: 'Fraunces, serif',
          weight: '600',
        },
        color: '#013a63',
        padding: {
          top: 10, // Weniger Abstand zum oberen Rand
          bottom: 30, // Reduzierter Abstand zur Grafik
        },
        align: 'start', // Titel linkbündig ausrichten
      },
    },
    layout: {
      padding: {
        left: 50, // Verschiebt die Grafik nach rechts, damit der Titel bündig mit der ersten Zahl ist
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
          drawOnChartArea: false, // Gitterlinien für die zweite Achse deaktivieren
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
      {data.length > 0 ? <Bar data={chartData} options={chartOptions} /> : <p>Loading chart...</p>}
    </div>
  );
}

export default PerformanceChart;
