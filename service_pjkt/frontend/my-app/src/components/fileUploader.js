import { useState } from "react";
import axios from "axios";

function FileUploadSingle({ isProcessing, handleProcessing }) {
  const [file, setFile] = useState();

  const handleSubmit = (e) => {
    e.preventDefault();

    console.log("------ F: ", e.target.exampleFormControlSelect1.value)
    console.log("------ F: ", file)
    if (!file) {
      return;
    }

    const url = "http://localhost:8000/uploadfile/"
    // const url = "http://192.168.31.176:8000/uploadfile/"

    let formData = new FormData()
    formData.append("file", file)
    console.log("------ FATA: ", formData)

    handleProcessing();
  };

  const handleFileChange = (e) => {
    console.log("----- ONCH", e);
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  // const handleUploadClick = () => {
  //   console.log("------", file)
  //   if (!file) {
  //     return;
  //   }
  //
  //   const url = "http://localhost:8000/uploadfile/"
  //   // const url = "http://192.168.31.176:8000/uploadfile/"
  //
  //   let formData = new FormData()
  //   formData.append("file", file)
  //
  //   axios.post(url, formData, {
  //     headers: {
  //       "Content-Type": "multipart/form-data",
  //     }
  //   }).then((res) => setFile(console.log("Success")))
  //     .catch((err) => alert(err))
  // };

  return (
    <div className="container px-3 py-4 mt-5">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <div className="flex flex-1 container mb16">
            <div className="form-group">
              <label htmlFor="exampleFormControlSelect1">Select type</label>
              <select className="form-control" id="exampleFormControlSelect1">
                <option>txt</option>
                <option>fb2</option>
                <option>pdf</option>
                <option>mobi</option>
              </select>
            </div>
            <div className="form-group mt-3 mb-5">
              <input
                className="form-control"
                type="file"
                onChange={handleFileChange}
              />
              <div className="mx-3">
                {file && `${file.name} - ${file.type}`}
              </div>
              <button
                className="btn btn-primary mt-3"
                type="submit"
                disabled={isProcessing}
              >
                {isProcessing ? "Processing.." : "Start"}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

export default FileUploadSingle;
