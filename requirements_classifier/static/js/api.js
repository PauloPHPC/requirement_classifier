export async function postData(url, data, isJSON = false) {
    const options = {
        method: "POST",
        headers: {},
        body: data,
    };

    if (isJSON) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
        const errorMsg = await response.text();
        throw new Error(errorMsg || "Request Failed");
    }
    return response.json();
}

export async function postForBlob(url, data, isJSON = false) {
  const options = { method: "POST", headers: {}, body: data };
  if (isJSON) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }
  const response = await fetch(url, options);
  if (!response.ok) {
    const errorMsg = await response.text();
    throw new Error(errorMsg || "Request Failed");
  }
  return response.blob();
}