import React, { useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";
import GAConnector from "../../components/Connectors/GAConnector";



const GOOGLE_CLIENT_ID = "DEINE_GOOGLE_CLIENT_ID_HIER"; // ⬅️ ersetzt durch echte Client-ID

function GAConnectionPage() {
  const [gaReady, setGaReady] = useState(false);
  const [googleUser, setGoogleUser] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("ga_ready") === "true") {
      setGaReady(true);
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, []);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
      });

      // ➕ zeigt automatisch eingeloggten Account
      window.google.accounts.id.prompt();
    };
    document.body.appendChild(script);
  }, []);

  const handleCredentialResponse = (response) => {
    try {
      const decoded = jwtDecode(response.credential);   
      setGoogleUser({
        name: decoded.name,
        email: decoded.email,
        picture: decoded.picture,
      });
    } catch (error) {
      console.error("❌ Fehler beim Dekodieren des JWT:", error);
    }
  };

  return (
    <div className="page-container">
      <GAConnector gaReady={gaReady} browserUser={googleUser} />
    </div>
  );
}

export default GAConnectionPage;
