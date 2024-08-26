import React from "react";
import "bootstrap/dist/css/bootstrap.css";
import Tabs from "react-bootstrap/Tabs";
import Tab from "react-bootstrap/Tab";
import Output from "./output";

export default function TabsRoot() {
  return (
    <div style={{ display: "block", width: 700, padding: 30 }}>
      <Tabs defaultActiveKey="first" justify>
        <Tab eventKey="first" title="Main">
          <Output>
            Hii, I am 1st tab content
          </Output>
        </Tab>
        <Tab eventKey="second" title="Second">
          <Output>
            Hii, I am 2nd tab content
          </Output>
        </Tab>
      </Tabs>
    </div>
  );
}
