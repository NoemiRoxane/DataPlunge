import React, { useEffect, useState } from "react";
import MetaConnector from "../../components/Connectors/MetaConnector";

function MetaConnectionPage() {
  const [metaReady, setMetaReady] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("meta_ready") === "true") {
      setMetaReady(true);
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, []);

  return (
    <div className="page-container">
      <MetaConnector metaReady={metaReady} />
    </div>
  );
}

export default MetaConnectionPage;
