import React, { useState, useEffect } from 'react';
import './AddDataSource.css';
import GASelector from "../components/GASelector";
import GAConnector from "../components/GAConnector";


const dataSources = [
  { name: "Google Ads", icon: "🟢" },
  { name: "Microsoft Advertising", icon: "🟢" },
  { name: "Facebook Ads", icon: "🔵" },
  { name: "Google Analytics", icon: "📊" },
  { name: "Meta", icon: "🔗" },
];

// ✅ Alle Plattformen, die OAuth 2.0 verwenden
const oauthSources = [
  "Google Ads",
  "Microsoft Advertising",
  "Facebook Ads",
  "Google Analytics",
  "LinkedIn",
  "TikTok",
  "Snapchat",
];

function AddDataSource() {
  const [selectedSource, setSelectedSource] = useState(null);
  const [gaReady, setGaReady] = useState(false);

  const handleConnect = (source) => {
    const sourcePath = source.name.toLowerCase().replace(/\s+/g, "-");

    if (source.name === "Google Ads") {
      window.location.href = "http://localhost:5000/google-ads/login";
      setTimeout(() => {
        fetch("http://localhost:5000/google-ads/fetch-campaigns")
          .then((res) => res.json())
          .then((data) => {
            console.log("📊 Google Campaign Data:", data);
            if (data.error) {
              alert("Google Ads error: " + data.error);
            } else {
              alert("Google campaign data fetched!");
            }
          })
          .catch((err) => alert("Error fetching Google campaigns: " + err));
      }, 5000);
    }

    else if (source.name === "Microsoft Advertising") {
      window.location.href = "http://localhost:5000/microsoft-advertising/login";
      setTimeout(() => {
        fetch("http://localhost:5000/microsoft-ads/fetch-campaigns")
          .then((res) => res.json())
          .then((data) => {
            console.log("📊 Microsoft Campaign Data:", data);
            if (data.error) {
              alert("Microsoft Ads error: " + data.error);
            } else {
              alert("Microsoft campaign data fetched!");
            }
          })
          .catch((err) => alert("Error fetching Microsoft campaigns: " + err));
      }, 5000);
    }

    else if (source.name === "Google Analytics") {
      window.location.href = "/connect/google-analytics";
    }
    
    
    else if (source.name === "Facebook Ads" || source.name === "Meta") {
      window.location.href = "http://localhost:5000/meta/login";
    
      // ⏳ Warte ein paar Sekunden, damit der Login-Redirect durchläuft
      setTimeout(() => {
        fetch("http://localhost:5000/meta/adaccounts", {
          credentials: "include"
        })
          .then((res) => res.json())
          .then((data) => {
            console.log("📊 Meta Ad Accounts:", data);
            if (data.error) {
              alert("Meta error: " + data.error);
            } else {
              alert("✅ Meta ad accounts fetched!");
            }
          })
          .catch((err) => alert("❌ Error fetching Meta ad accounts: " + err));
      }, 5000);
    }
    
    
    
    
    

    else {
      fetch("http://localhost:5000/add-data-source", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: source.name }),
      })
        .then((response) => response.json())
        .then((data) => alert(`Successfully connected: ${source.name}`))
        .catch((error) => alert("Failed to connect data source"));
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ready = params.get("meta_ready");
  
    if (ready === "true") {
      fetch("http://localhost:5000/meta/adaccounts", {
        credentials: "include"
      })
        .then((res) => res.json())
        .then((data) => {
          console.log("📊 Meta Ad Accounts:", data);
          if (data.error) {
            alert("Meta error: " + data.error);
          } else {
            alert("✅ Meta ad accounts fetched!");
          }
        })
        .catch((err) => alert("❌ Error fetching Meta ad accounts: " + err));
  
      // URL clean halten
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);
  
  
  
  

  return (
    <div className="page-container">
      <header className="page-header">
        <h1>Connect Data Source</h1>
      </header>

      <div className="data-source-grid">
        {dataSources.map((source, index) => (
          <div key={index} className="data-source-card">
            <span className="data-source-icon">{source.icon}</span>
            <h3>{source.name}</h3>
            <button
              className="connect-button"
              onClick={() => handleConnect(source)}
            >
              Connect Now
            </button>
          </div>
        ))}
      </div>

     



    </div>
  );
}

export default AddDataSource;
