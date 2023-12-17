export async function processData(videoId, callback) {
  callback("Processing data...\n");
  await downloadAudio(videoId, callback);

  return "result";
}

export async function downloadAudio(videoId, onProgress) {
  console.log("-----> ST< 2 ", videoId);
  let reader = null;
  const url = "http://localhost:8000/stream";
  const response = await fetch(url, {
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Content-type": "application/json",
    },
  });
  console.log(response);
  reader = response.body?.getReader();

  if (reader) {
    return streamResponse(reader, onProgress);
  } else {
    return false;
  }
}

async function streamResponse(reader, onProgress) {
  return new Promise((resolve) => {
    const decoder = new TextDecoder();
    let result = "";
    const readChunk = ({ done, value }) => {
      if (done) {
        resolve(result);
        return;
      }

      const output = decoder.decode(value);
      result += output;
      onProgress(output);

      reader.read().then(readChunk);
    };
    reader.read().then(readChunk);
  });
}
