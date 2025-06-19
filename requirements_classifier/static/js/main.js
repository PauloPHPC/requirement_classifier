import { tableHead, generateTable } from './tableFunctions.js';

let extracted_requirements = [];
let uploadedFileName = "";
let pdfPath = "";

document.getElementById("uploadBtn").addEventListener("click", async function () {

  const fileInput = document.getElementById("pdfInput");
  const spinner = document.getElementById("spinner");
  const uploadBtn = document.getElementById("uploadBtn");

  if (!fileInput.files[0]) {
    alert("Please select a PDF file first.");
    return;
  }

  uploadBtn.disabled = true
  uploadBtn.innerText = "Sending..."

  let formData = new FormData();
  formData.append("pdf_file", fileInput.files[0]);

  uploadedFileName = fileInput.files[0].name;

  console.log(formData);
  spinner.style.display = "block";
  try {
    let response = await fetch("/process_pdf/", {
      method: "POST",
      body: formData
    });

    if (!response.ok) throw new Error("Error processing PDF file.");

    //let table = document.getElementById("resultsTable");

    let rawData = await response.json();
    console.log(rawData)
    pdfPath = rawData.pdf_path;

    extracted_requirements = [];

    rawData.results.forEach(req => {
      extracted_requirements.push({
        "Text": req.requirement,
        "AI Classification": req.type,
        "Confidence": req.confidence,
        original_text: req.original_text,
        match_score: req.match_score,
        page: req.page
      });
    });


    redrawTable();


 
  } catch (error) {
    alert("Error sending PDF file to server.");
    console.error(error);
  } finally {
    spinner.style.display = "none"
    uploadBtn.disabled = false;
    uploadBtn.innerText = "Send";
  }
});

document.getElementById("saveBtn").addEventListener("click", async function () {
  let table = document.getElementById("resultsTable");
  let rows = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr");

  let updatedRequirements = [];

  for (let i = 0; i < rows.length; i++) {
    let row = rows[i];
    let cells = row.getElementsByTagName("td");

    const base= extracted_requirements[i];

    let requirements = {
      text: base.Text,
      classification_ai: base["AI Classification"],
      confidence_ai: base.Confidence,
      classification_user: cells[3].getElementsByTagName("select")[0].value,
      project: uploadedFileName,
      original_text: base.original_text,
      match_score: base.match_score,
      page: base.page,
    };

    updatedRequirements.push(requirements);
  }

  console.log(updatedRequirements);


  try {
    let response = await fetch("/save_requirements/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        requirements: updatedRequirements,
        pdf_path: pdfPath,
       }),
    });

    const message = await response.json();
    alert(message.message || "Error while saving requirements.");

    const fixedPath = "/" + message.highlighted_pdf_path.replace(/\\/g, "/");

    if (message.highlighted_pdf_path) {
      const link = document.createElement("a");
      link.href = fixedPath;
      link.download = "highlighted_requirements.pdf";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

  } catch (error) {
    alert("Saving requirements failed", console.error(error));
  }

});

function redrawTable() {
  let table = document.getElementById("resultsTable");

  table.innerHTML = ""

  const visibleData = extracted_requirements.map(req => ({
    "Text": req.Text,
    "AI Classification": req["AI Classification"],
    "Confidence": req.Confidence
  }));

  tableHead(table, visibleData)
  generateTable(table, visibleData)

}

function getCSRFToken() {
  return document.cookie.split("; ").find(row => row.startsWith("csrftoken="))?.split("=")[1];
}