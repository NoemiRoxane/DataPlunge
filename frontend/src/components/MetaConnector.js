import React, { useEffect, useState } from "react";
import "./GAConnector.css"; // Wiederverwende dein bestehendes Styling

function MetaConnector({ metaReady }) {
  const [step, setStep] = useState(metaReady ? 2 : 1);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState("");

  useEffect(() => {
    if (metaReady) {
      setStep(2);
      fetch("http://localhost:5000/meta/adaccounts", { credentials: "include" })
        .then((res) => res.json())
        .then((data) => {
          console.log("📡 Accounts im Frontend:", data);
          if (Array.isArray(data)) setAccounts(data);
        })
        .catch((err) => console.error("❌ Fehler beim Laden der Accounts:", err));
    }
  }, [metaReady]);

  const handleLogin = () => {
    window.location.href = "http://localhost:5000/meta/login";
  };

  const handleConnect = () => {
    console.log("✅ Verbinde Account:", selectedAccount);

    fetch("http://localhost:5000/meta/select-account", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: selectedAccount }),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("🎉 Account gespeichert:", data);
        setStep(3);
      })
      .catch((err) => console.error("❌ Fehler beim Speichern des Accounts:", err));
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
      <img
        src="/meta_logo.png"
        alt="Meta"
        style={{ width: "32px", marginRight: "10px", verticalAlign: "middle" }}
        />
        Connect Meta (Facebook Ads)
      </h1>

      <p className="step-labels">Credentials &gt; Choose Account &gt; Connection</p>
      <StepIndicator />

      {step === 1 && (
        <div className="step step-1">
          <div className="credential-container">
            <div className="credential-card">
              <h3>Add Meta Credentials</h3>
              <button onClick={handleLogin} className="google-button">
              <img
                src="/fb_logo.jpg"
                alt="FB"
                style={{ width: "28px", marginRight: "10px", verticalAlign: "middle" }}
        />
                Continue with Facebook
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
          <h2>Choose Ad Account</h2>
          <div className="checkbox-list">
            {accounts.length === 0 ? (
              <p>⚠️ Keine Ad Accounts gefunden oder noch nicht geladen.</p>
            ) : (
              accounts.map((acc) => (
                <label key={acc.id}>
                  <input
                    type="radio"
                    checked={selectedAccount === acc.id}
                    onChange={() => setSelectedAccount(acc.id)}
                  />
                  {acc.name} – {acc.id} {acc.account_status !== 1 && "(Inactive/Disabled)"}
                </label>
              ))
            )}
          </div>

          <div className="nav-buttons">
            <button className="outline" onClick={() => setStep(1)}>&lt; Previous</button>
            <button
              className="primary"
              disabled={!selectedAccount}
              onClick={handleConnect}
            >
              Connect Data Source &gt;
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

export default MetaConnector;
