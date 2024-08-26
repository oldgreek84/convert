import React, { useEffect, useState } from "react";
import "./App.css";
import FileUploadSingle from "./components/fileUploader";
// import FileUploader from './components/fileUploader';
import Output from "./components/output";
// import TabsRoot from "./components/tabs";
import "bootstrap/dist/css/bootstrap.css";
import Tabs from "react-bootstrap/Tabs";
import Tab from "react-bootstrap/Tab";
import { processData } from "./utils/api-client";
// import axios from "axios";

function App() {
  const [isProcessing, setProcessing] = useState(false);
  const [progressOut, setProgressOut] = useState("");
  const [activeTab, setActiveTab] = useState("process");
  const [result, setResult] = useState("");

  const handleStartProcessing = async () => {
    console.log("----> Start");
    setProcessing(true);

    // TODO
    const job_id = "some id";
    const converResult = await processData(job_id, (message) => {
      setProgressOut((prev) => prev + message);
    });
    console.log("-----> res", converResult);
    if (converResult) {
      setResult(converResult);
    }

    setActiveTab("result");
    setProcessing(false);
    console.log("----> END ", isProcessing);
  };

  return (
    <div className="App">
      <h3 className="container h3 display-1">Converter</h3>
      <FileUploadSingle
        handleProcessing={handleStartProcessing}
        isProcessing={isProcessing}
      ></FileUploadSingle>
      <Tabs activeKey={activeTab} justify onSelect={(k) => setActiveTab(k)}>
        <Tab eventKey="process" title="Main">
          <Output>{progressOut}</Output>
        </Tab>
        <Tab eventKey="result" title="Second">
          <Output>{result}</Output>
        </Tab>
      </Tabs>
    </div>
  );
}

export default App;
