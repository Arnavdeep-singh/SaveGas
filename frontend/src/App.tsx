import React, { useState, useEffect } from "react";

function App() {
  const [status, setStatus] = useState("Connecting...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/health")
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "ok") {
          setStatus("Backend connected");
        }
      })
      .catch(() => {
        setStatus("Backend connection failed");
      });
  }, []);

  return <h1>{status}</h1>;
}

export default App;
