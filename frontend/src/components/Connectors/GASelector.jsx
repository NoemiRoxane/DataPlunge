import React, { useEffect, useState } from "react";

function GASelector() {
  const [properties, setProperties] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState("");
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      const fetchProperties = async () => {
        try {
          const res = await fetch("http://localhost:5000/ga/properties", {
            method: "GET",
            credentials: "include",
          });
  
          const data = await res.json();
  
          if (data.error) {
            console.error("Fehler beim Abrufen der GA Properties:", data.error);
            return;
          }
  
          if (!Array.isArray(data)) {
            console.error("❌ Properties sind kein Array:", data);
            return;
          }
  
          setProperties(data);
          if (data.length === 1) {
            setSelectedProperty(data[0].property_id);
          }
        } catch (err) {
          console.error("Fehler beim Laden der Properties:", err);
        }
      };
  
      fetchProperties();
    }, 1000); // ⏱️ 1 Sekunde Delay nach Mount
  
    return () => clearTimeout(timer);
  }, []);
  
  
  
  

  const handleFetchMetrics = () => {
    if (!selectedProperty) {
      alert("Bitte zuerst eine Property auswählen.");
      return;
    }

    fetch(`http://localhost:5000/ga/fetch-metrics?property_id=${selectedProperty}`, {
      method: "GET",
      credentials: "include"
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          alert("Fehler beim Abrufen der Metriken");
        } else {
          setMetrics(data);
          console.log("📊 GA Metrics:", data);
        }
      });
  };

  return (
    <div>
    <h2>Google Analytics Properties:</h2>

{properties.length === 0 ? (
  <p>⚠️ Keine Properties geladen.</p>
) : (
  <ul>
    {properties.map((prop) => (
      <li key={prop.property_id}>
        <label>
          <input
            type="checkbox"
            checked={selectedProperty === prop.property_id}
            onChange={() => setSelectedProperty(prop.property_id)}
          />
          {prop.display_name} ({prop.property_id})
        </label>
      </li>
    ))}
  </ul>
)}

    </div>
  );
}

export default GASelector;
