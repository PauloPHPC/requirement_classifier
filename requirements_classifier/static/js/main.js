// import { tableHead, generateTable } from './tableFunctions.js';
import { buildRequirementsTable } from "./tableFunctions.js";
import { postData, postForBlob } from "./api.js";

// let extracted_requirements = [];
window.extracted_requirements = [];
let uploadedFileName = "";
let pdfPath = "";

// MARK: DOM ELEMENTS

const fileInput = document.getElementById("pdfInput");
const uploadBtn = document.getElementById("uploadBtn");
const saveBtn = document.getElementById("saveBtn");
const classResult = document.getElementById("classResult");
const resultsTable = document.getElementById("resultsTable");
const spinner = document.getElementById("spinner");
const exportCsvBtn = document.getElementById("exportCsvBtn");

// Change the input name from Choose PDF to the files name
fileInput.addEventListener("change", () => {
  const label = document.querySelector("label[for='pdfInput']");
  label.textContent = fileInput.files[0]?.name || "Choose PDF";
});

// MARK: Upload Button
// Send to backend the pdf file and gets back its response.
uploadBtn.addEventListener("click", async () => {
  if (!fileInput.files[0]) return alert("Please select a PDF file first.");
  
  toggleLoading(true, "Analyzing...");

  uploadedFileName = fileInput.files[0].name;

  try {
    const formData = new FormData();
    formData.append("pdf_file", fileInput.files[0]);
    const response = await postData("/process_pdf/", formData);

    pdfPath = response.pdf_path;
    window.extracted_requirements = response.results.map((req) => ({
      text: req.requirement,
      aiClassification: req.type,
      confidence: req.confidence,
      original_text: req.original_text,
      match_score: req.match_score,
      page: req.page
    }));

    renderResults();
  } catch (err) {
    console.error(err);
    alert("Error processing PDF file");
  } finally {
    toggleLoading(false);
  }
});

// MARK: Save Button
// Sends to backend the modified requirements (by the user) and gets back a pdf file with them highlighted
saveBtn.addEventListener("click", async () => {
  try {
    const updatedRequirements = buildRequirementsTable.extractData(window.extracted_requirements, uploadedFileName);

    const response = await postData("/save_requirements/", {
      requirements: updatedRequirements,
      pdf_path: pdfPath,
    }, true);

    alert(response.message || "Saved successfully.");

    if (response.highlighted_pdf_url) {
      const link = document.createElement("a");
      link.href = response.highlighted_pdf_url;
      link.download = "highlighted_requirements.pdf";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  } catch (err) {
    console.error(err);
    alert("Failed to save requirements.");
  }
});

// MARK: Export CSV Button
// Exports the requirements to a CSV file
exportCsvBtn.addEventListener("click", async () => {
  try {
    const updatedRequirements = buildRequirementsTable.extractData(
      window.extracted_requirements,
      uploadedFileName
    );

    const blob = await postForBlob(
      "/export_csv/",
      { requirements: updatedRequirements, filename: (uploadedFileName || "requirements").replace(/\.[^/.]+$/, "") },
      true
    );

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;

    a.download = `${(uploadedFileName || "requirements").replace(/\.[^/.]+$/, "")}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error(err);
    alert("Failed to export CSV.");
  }
});

// MARK: Auxiliary Functions

function renderResults() {
  resultsTable.innerHTML = "";
  buildRequirementsTable.render(resultsTable, window.extracted_requirements);
  classResult.style.display = "block";
  saveBtn.style.display = "inline-block";
  exportCsvBtn.style.display = "inline-block"; 
}

function toggleLoading(isLoading, text = "Analyzing...") {
  uploadBtn.disabled = isLoading;
  uploadBtn.textContent = isLoading ? text : "Upload";
  spinner.style.display = isLoading ? "block" : "none";
}

// let extracted_requirements = [];
// let uploadedFileName = "";
// let pdfPath = "";

// const input = document.getElementById("pdfInput");
// const label = document.querySelector("label[for='pdfInput']");
// input.addEventListener("change", function () {
//   if (this.files.length > 0) {
//     label.textContent = this.files[0].name
//   }
// })

// document.getElementById("uploadBtn").addEventListener("click", async function () {

//   const fileInput = document.getElementById("pdfInput");
//   const spinner = document.getElementById("spinner");
//   const uploadBtn = document.getElementById("uploadBtn");

//   if (!fileInput.files[0]) {
//     alert("Please select a PDF file first.");
//     return;
//   }

//   uploadBtn.disabled = true
//   uploadBtn.innerText = "Analyzing..."

//   let formData = new FormData();
//   formData.append("pdf_file", fileInput.files[0]);

//   uploadedFileName = fileInput.files[0].name;

//   console.log(formData);
//   spinner.style.display = "block";
//   try {
//     let response = await fetch("/process_pdf/", {
//       method: "POST",
//       body: formData
//     });

//     if (!response.ok) throw new Error("Error processing PDF file.");

//     //let table = document.getElementById("resultsTable");

//     let rawData = await response.json();
//     console.log(rawData)
//     pdfPath = rawData.pdf_path;

//     extracted_requirements = [];

//     rawData.results.forEach(req => {
//       extracted_requirements.push({
//         "Text": req.requirement,
//         "AI Classification": req.type,
//         "Confidence": req.confidence,
//         original_text: req.original_text,
//         match_score: req.match_score,
//         page: req.page
//       });
//     });


//     redrawTable();


 
//   } catch (error) {
//     alert("Error sending PDF file to server.");
//     console.error(error);
//   } finally {
//     spinner.style.display = "none"
//     uploadBtn.disabled = false;
//     uploadBtn.innerText = "Send";
//   }
// });

// document.getElementById("saveBtn").addEventListener("click", async function () {
//   let table = document.getElementById("resultsTable");
//   let rows = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr");

//   let updatedRequirements = [];

//   for (let i = 0; i < rows.length; i++) {
//     let row = rows[i];
//     let cells = row.getElementsByTagName("td");

//     const base= extracted_requirements[i];

//     let requirements = {
//       text: base.Text,
//       classification_ai: base["AI Classification"],
//       confidence_ai: base.Confidence,
//       classification_user: cells[3].getElementsByTagName("select")[0].value,
//       project: uploadedFileName,
//       original_text: base.original_text,
//       match_score: base.match_score,
//       page: base.page,
//     };

//     updatedRequirements.push(requirements);
//   }

//   console.log(updatedRequirements);


//   try {
//     let response = await fetch("/save_requirements/", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json"
//       },
//       body: JSON.stringify({ 
//         requirements: updatedRequirements,
//         pdf_path: pdfPath,
//        }),
//     });

//     const message = await response.json();
//     alert(message.message || "Error while saving requirements.");

//     //const fixedPath = "/" + message.highlighted_pdf_url.replace(/\\/g, "/");
//     console.log(message)
//     if (message.highlighted_pdf_url) {
//       const link = document.createElement("a");
//       link.href = message.highlighted_pdf_url;
//       link.download = "highlighted_requirements.pdf";
//       document.body.appendChild(link);
//       link.click();
//       document.body.removeChild(link);
//     }

//   } catch (error) {
//     alert("Saving requirements failed", console.error(error));
//   }

// });

// function redrawTable() {
//   let table = document.getElementById("resultsTable");

//   table.innerHTML = ""

//   const visibleData = extracted_requirements.map(req => ({
//     "Text": req.Text,
//     "AI Classification": req["AI Classification"],
//     "Confidence": req.Confidence
//   }));

//   tableHead(table, visibleData)
//   generateTable(table, visibleData, extracted_requirements, redrawTable)

//   document.getElementById("classResult").style.display = "block";

// }

// function getCSRFToken() {
//   return document.cookie.split("; ").find(row => row.startsWith("csrftoken="))?.split("=")[1];
// }