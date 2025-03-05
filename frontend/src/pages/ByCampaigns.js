import React, { useEffect, useState } from "react";
import DataTable from "react-data-table-component";
import { toast, ToastContainer } from "react-toastify";
import { FaFilter, FaDownload } from "react-icons/fa"; // Icons für UI
import { useDate } from "../context/DateContext"; 
import "react-toastify/dist/ReactToastify.css";
import "./ByCampaigns.css";

const ByCampaigns = () => {
    const { dateRange } = useDate(); // ✅ Holt sich das Datum direkt aus `DateContext`
    const [campaigns, setCampaigns] = useState([]);
    const [filterText, setFilterText] = useState("");
    const [filteredData, setFilteredData] = useState([]);

    useEffect(() => {
        if (dateRange.startDate && dateRange.endDate) {
          const start = dateRange.startDate.toISOString().split("T")[0];
          const end = dateRange.endDate.toISOString().split("T")[0];
    
          fetch(`http://127.0.0.1:5000/get-campaigns?start_date=${start}&end_date=${end}`)
            .then((response) => response.json())
            .then((data) => {
              setCampaigns(data);
              setFilteredData(data);
            })
            .catch((error) => {
              console.error("Error fetching campaigns:", error);
              toast.error("Error loading campaign data.");
            });
        }
      }, [dateRange]);

  // 🔍 Kampagnen filtern
  useEffect(() => {
    const filtered = campaigns.filter(
      (item) =>
        item.campaign_name.toLowerCase().includes(filterText.toLowerCase()) ||
        item.traffic_source.toLowerCase().includes(filterText.toLowerCase())
    );
    setFilteredData(filtered);
  }, [filterText, campaigns]);

  // 📅 Datumsauswahl-Filter
  const filterByDate = () => {
    if (!dateRange.start || !dateRange.end) return;
    const filtered = campaigns.filter(
      (item) => item.date >= dateRange.start && item.date <= dateRange.end
    );
    setFilteredData(filtered);
  };

  // 📤 CSV-Export
  const exportCSV = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      ["Traffic Source,Campaign,Costs,Impressions,Clicks,CPC,Sessions,Cost per Session,Conversions,Cost per Conversion"]
        .concat(
          filteredData.map((row) =>
            [
              row.traffic_source,
              row.campaign_name,
              row.costs.toFixed(2),
              row.impressions,
              row.clicks,
              row.cost_per_click.toFixed(2),
              row.sessions,
              row.cost_per_session.toFixed(2),
              row.conversions,
              row.cost_per_conversion.toFixed(2),
            ].join(",")
          )
        )
        .join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "campaign_performance.csv");
    document.body.appendChild(link);
    link.click();
  };

  // 🏷️ Tabelle mit Kampagnen-Daten definieren
  const columns = [
    {
      name: "Traffic Source",
      selector: (row) => row.traffic_source,
      sortable: true,
    },
    {
      name: "Campaign",
      selector: (row) => row.campaign_name,
      sortable: true,
      wrap: true,
      minWidth: "260px",
    },
    {
      name: "Costs",
      selector: (row) => `CHF${(parseFloat(row.costs) || 0).toFixed(2)}`,
      sortable: true,
    },
    {
      name: "Impressions",
      selector: (row) => row.impressions ?? 0,
      sortable: true,
    },
    {
      name: "Clicks",
      selector: (row) => row.clicks ?? 0,
      sortable: true,
    },
    {
      name: "CPC",
      selector: (row) => `CHF${(parseFloat(row.cost_per_click) || 0).toFixed(2)}`,
      sortable: true,
    },
    {
      name: "Sessions",
      selector: (row) => row.sessions ?? 0,
      sortable: true,
    },
    {
      name: "Cost per Session",
      selector: (row) => `CHF${(parseFloat(row.cost_per_session) || 0).toFixed(2)}`,
      sortable: true,
    },
    {
      name: "Conversions",
      selector: (row) => row.conversions ?? 0,
      sortable: true,
    },
    {
      name: "Cost per Conversion",
      selector: (row) => `CHF${(parseFloat(row.cost_per_conversion) || 0).toFixed(2)}`,
      sortable: true,
    },
  ];
  

  // 📊 Berechnung der Summenzeile
  const totalRow = {
    traffic_source: "Total",
    campaign_name: "",
    costs: filteredData.reduce((sum, row) => sum + row.costs, 0),
    impressions: filteredData.reduce((sum, row) => sum + row.impressions, 0),
    clicks: filteredData.reduce((sum, row) => sum + row.clicks, 0),
    cost_per_click: (filteredData.reduce((sum, row) => sum + row.cost_per_click, 0) / filteredData.length) || 0,
    sessions: filteredData.reduce((sum, row) => sum + row.sessions, 0),
    cost_per_session: (filteredData.reduce((sum, row) => sum + row.cost_per_session, 0) / filteredData.length) || 0,
    conversions: filteredData.reduce((sum, row) => sum + row.conversions, 0),
    cost_per_conversion: (filteredData.reduce((sum, row) => sum + row.cost_per_conversion, 0) / filteredData.length) || 0,
  };

  return (
    <div className="page-container">
      <ToastContainer />
      <header className="page-header">
        <h1>Performance by Campaigns</h1>
        <div className="filters">
          <button onClick={exportCSV} className="export-button">
            <FaDownload /> Export
          </button>
        </div>
      </header>

      <DataTable
        columns={columns}
        data={[...filteredData, totalRow]}
        pagination
        highlightOnHover
        responsive
        striped
      />
    </div>
  );
};

export default ByCampaigns;