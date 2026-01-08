import React, { useEffect, useState } from "react";
import "./GAConnector.css"; // Optional: dein Stylesheet

function GAConnector({ gaReady, browserUser }) {
  const [step, setStep] = useState(gaReady ? 2 : 1);
  const [properties, setProperties] = useState([]);
  const [selectedProperties, setSelectedProperties] = useState([]);



  // Step 2 triggern nach Google Login
  useEffect(() => {
    if (gaReady) {
      setStep(2);
      fetch("http://localhost:5000/ga/properties", { credentials: "include" })
        .then((res) => res.json())
        .then((data) => Array.isArray(data) && setProperties(data));
    }
  }, [gaReady]);

  const handleLogin = () => {
    sessionStorage.setItem("selectedSource", "Google Analytics");
    window.location.href = "http://localhost:5000/ga/login";
  };

  const handleSelect = (propertyId) => {
    setSelectedProperties((prev) =>
      prev.includes(propertyId)
        ? prev.filter((id) => id !== propertyId)
        : [...prev, propertyId]
    );
  };

  const handleConnect = () => {
    console.log("✅ Verbinde GA Properties:", selectedProperties);
    setStep(3);
  };

  const StepIndicator = () => (
    <div className="step-indicator">
      <span className={step >= 1 ? "active" : ""}>1</span>
      <span className={step >= 2 ? "active" : ""}>2</span>
      <span className={step >= 3 ? "active" : ""}>3</span>
    </div>
  );

  return (
    <div className="ga-wizard">
      <h1 style={{ fontFamily: "Inter", fontSize: "28px", fontWeight: 600, color: "#0f2746" }}>
        <img src="https://www.gstatic.com/analytics-suite/header/suite/v2/ic_analytics.svg" alt="GA" style={{ width: "32px", marginRight: "10px", verticalAlign: "middle" }} />
        Connect Google Analytics
      </h1>

      <p className="step-labels">Credentials &gt; Choose Account &gt; Connection</p>
      <StepIndicator />

      {step === 1 && (
        <div className="step step-1">
          <div className="credential-container">
            <div className="credential-card">
              <h3>My Credentials</h3>
              {browserUser ? (
                <div className="credential">
                  <div className="initials">
                    {browserUser.name?.[0] ?? "?"}
                  </div>
                  <div>
                    <strong>{browserUser.name}</strong>
                    <div>{browserUser.email}</div>
                  </div>
                </div>
              ) : (
                <div className="credential">
                  <p>No Google account detected.</p>
                </div>
              )}

              <a href="#">Manage my credentials</a>
            </div>

            <div className="credential-card">
              <h3>Add New Credentials</h3>
              <button onClick={handleLogin} className="google-button">
                <img src="https://developers.google.com/identity/images/g-logo.png" alt="G" />
                Continue with Google
              </button>
            </div>
          </div>

          <div className="nav-buttons">
            <button className="outline" disabled>&lt; Previous</button>
            <button className="primary" onClick={() => setStep(2)}>Next &gt;</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="step step-2">
          <h2>Choose Account</h2>
          <div className="checkbox-list">
            {properties.map((p) => (
              <label key={p.property_id}>
                <input
                  type="checkbox"
                  checked={selectedProperties.includes(p.property_id)}
                  onChange={() => handleSelect(p.property_id)}
                />
                {p.display_name} – GA4 {p.property_id}
              </label>
            ))}
          </div>

          <div className="nav-buttons">
            <button className="outline" onClick={() => setStep(1)}>&lt; Previous</button>
            <button
              className="primary"
              disabled={selectedProperties.length === 0}
              onClick={handleConnect}
            >
              Connect Data Sources &gt;
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="step step-3">
          <h2>🎉 Congrats!</h2>
          <p>We are now connecting your data</p>
          <div className="illustration">📈</div>
          <p>As it might take a while, we propose:</p>
          <ul>
            <li><a href="/add-data-source">Connect another data source →</a></li>
            <li><a href="#">Have a breather →</a></li>
            <li><a href="#">Watch beautiful underwater video →</a></li>
          </ul>

          <div className="nav-buttons">
            <button className="outline" onClick={() => setStep(2)}>&lt; Previous</button>
            <button className="primary" disabled>Connect Data Sources</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default GAConnector;
