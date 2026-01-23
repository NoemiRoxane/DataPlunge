import React, { useEffect, useState } from "react";
import DataTable from "react-data-table-component";
import { toast, ToastContainer } from "react-toastify";
import { FaFilter, FaDownload } from "react-icons/fa";
import { useDate } from "../../context/DateContext";
import * as api from "../../utils/api";
import "react-toastify/dist/ReactToastify.css";
import "./ByCampaigns.css";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

const ByCampaigns = () => {
    const { dateRange, setDateRange } = useDate(); // ✅ Get Date Context
    const [campaigns, setCampaigns] = useState([]);
    const [filterText, setFilterText] = useState("");
    const [filteredData, setFilteredData] = useState([]);

    // ✅ Fetch campaigns whenever date range changes
    useEffect(() => {
        if (dateRange.startDate && dateRange.endDate) {
            const start = dateRange.startDate.toISOString().split("T")[0];
            const end = dateRange.endDate.toISOString().split("T")[0];

            console.log(`📡 Fetching campaigns from: ${start} to ${end}`);

            api.get(`/get-campaigns?start_date=${start}&end_date=${end}`)
                .then((data) => {
                    console.log("✅ API Response:", data);
                    setCampaigns(data); // Store API data
                    setFilteredData(data); // Initial display data
                })
                .catch((error) => {
                    console.error("❌ Error fetching campaigns:", error);
                    toast.error("Error loading campaign data.");
                    setCampaigns([]);
                    setFilteredData([]);
                });
        }
    }, [dateRange]); 

    // ✅ Filter campaigns by Date + Text
    useEffect(() => {
      if (!campaigns.length) return;
  
      const filtered = campaigns.filter((item) =>
          item.campaign_name.toLowerCase().includes(filterText.toLowerCase()) ||
          item.traffic_source.toLowerCase().includes(filterText.toLowerCase())
      );
  
      setFilteredData(filtered);
  }, [campaigns, filterText]);
  

    // ✅ Handle Date Change
    const handleDateChange = (dates) => {
        const [start, end] = dates;
        setDateRange({ startDate: start, endDate: end });
    };

    // ✅ Define Table Columns
    const columns = [
        { name: "Traffic Source", selector: (row) => row.traffic_source, sortable: true },
        { name: "Campaign", selector: (row) => row.campaign_name, sortable: true, wrap: true, minWidth: "260px" },
        { name: "Costs", selector: (row) => `CHF${(parseFloat(row.costs) || 0).toFixed(2)}`, sortable: true },
        { name: "Impressions", selector: (row) => row.impressions ?? 0, sortable: true },
        { name: "Clicks", selector: (row) => row.clicks ?? 0, sortable: true },
        { name: "CPC", selector: (row) => `CHF${(parseFloat(row.cost_per_click) || 0).toFixed(2)}`, sortable: true },
        { name: "Sessions", selector: (row) => row.sessions ?? 0, sortable: true },
        { name: "Conversions", selector: (row) => row.conversions ?? 0, sortable: true },
        { name: "Cost per Conversion", selector: (row) => `CHF${(parseFloat(row.cost_per_conversion) || 0).toFixed(2)}`, sortable: true },
    ];

    // ✅ Compute Total Row (with safety check)
    const totalRow = Array.isArray(filteredData) && filteredData.length > 0 ? {
        traffic_source: "Total",
        campaign_name: "",
        costs: filteredData.reduce((sum, row) => sum + (parseFloat(row.costs) || 0), 0),
        impressions: filteredData.reduce((sum, row) => sum + (parseInt(row.impressions) || 0), 0),
        clicks: filteredData.reduce((sum, row) => sum + (parseInt(row.clicks) || 0), 0),
        cost_per_click: (filteredData.reduce((sum, row) => sum + (parseFloat(row.cost_per_click) || 0), 0) / filteredData.length) || 0,
        conversions: filteredData.reduce((sum, row) => sum + (parseFloat(row.conversions) || 0), 0),
        cost_per_conversion: (filteredData.reduce((sum, row) => sum + (parseFloat(row.cost_per_conversion) || 0), 0) / filteredData.length) || 0,
    } : null;

    return (
        <div className="page-container">
            <ToastContainer />
            <header className="page-header">
                <h1>Performance by Campaigns</h1>
                <div className="header-controls" style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    <DatePicker
                        selected={dateRange.startDate}
                        onChange={handleDateChange}
                        selectsRange
                        startDate={dateRange.startDate}
                        endDate={dateRange.endDate}
                        placeholderText="Select date range"
                        isClearable
                    />
                </div>
            </header>

            <DataTable
                columns={columns}
                data={totalRow ? [...filteredData, totalRow] : filteredData}
                pagination
                highlightOnHover
                responsive
                striped
            />
        </div>
    );
};

export default ByCampaigns;
