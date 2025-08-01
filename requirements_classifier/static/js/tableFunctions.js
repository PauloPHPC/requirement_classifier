const classifications = [
  "---", "Functional", "NF - Security", "NF - Availability", "NF - Legal", "NF - Look and Feel",
  "NF - Maintenability", "NF - Operacional", "NF - Performance", "NF - Scalability",
  "NF - Usability", "NF - Fault Tolerance", "NF - Portability", "Out of Scope"
];

const sortDirections = {
  confidence: "asc",
  aiClassification: "asc"
};

function render(table, data) {
  const previouseSelections = {};
  document.querySelectorAll("#resultsTable tbody tr").forEach((row, i) => {
    const select = row.querySelector("select");
    if (select) {
      const text = row.children[0].textContent;
      previouseSelections[text] = select.value;
    }
  });

  table.innerHTML = "";
  const thead = createTableHead(data);
  const tbody = createTableBody(data, previouseSelections);
  table.append(thead, tbody)
};

// MARK: Table Head
// Creates the table head
function createTableHead(data) {
  const thead = document.createElement("thead");
  const row = document.createElement("tr");

  const keys = ["Text", "aiClassification", "confidence"];

  keys.forEach((key) => {
    const th = document.createElement("th");
    th.textContent = headerLabel(key);
    if (key !== "text") {
      th.style.cursor = "pointer";
      th.addEventListener("click", () => handleSort(key, data));
    }
    row.appendChild(th);
  });

  row.innerHTML += `<th>User Classification</th><th>Delete</th>`;
  thead.appendChild(row);
  return thead;
}

// MARK: Table Body
// Creates the table body
function createTableBody(data, previouseSelections) {
  const tbody = document.createElement("tbody");

  data.forEach((entry, index) => {
    const row = document.createElement("tr");
    const textCell = document.createElement("td");
    textCell.textContent = entry.text;

    const aiClassCell = document.createElement("td");
    aiClassCell.textContent = entry.aiClassification;
    
    const confCell = document.createElement("td");
    confCell.textContent = `${(entry.confidence * 100).toFixed(0)}%`;

    const userSelect = document.createElement("select");
    classifications.forEach(opt => {
      const option = document.createElement("option");
      option.value = option.textContent = opt;
      userSelect.appendChild(option);
    });

    if (previouseSelections[entry.text]) {
      userSelect.value = previouseSelections[entry.text];
    }

    const userCell = document.createElement("td");
    userCell.appendChild(userSelect);

    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "🗑️";
    deleteBtn.title = "Delete Requirement";
    deleteBtn.classList.add("delete-btn")
    deleteBtn.addEventListener("click", () => deleteRequirement(entry));

    const deleteCell = document.createElement("td");
    deleteCell.appendChild(deleteBtn);

    row.append(textCell, aiClassCell, confCell, userCell, deleteCell);
    tbody.appendChild(row);
    

  });

  return tbody;
}

function handleSort(key, data) {
  const dir = sortDirections[key];

  data.sort((a, b) => {
    if (key === "confidence") return dir === "asc" ? a.confidence - b.confidence : b.confidence - a.confidence;
    return dir === "asc" ? a[key].localeCompare(b[key]) : b[key].localeCompare(a[key]);
  });
  sortDirections[key] = dir === "asc" ? "desc" : "asc";
  render(document.getElementById("resultsTable"), data);
}

function headerLabel(key) {
  return {
    text: "Text",
    aiClassification: "AI Classification",
    confidence: "Confidence",
  }[key];
}

function extractData(originalData, uploadedFileName) {
  const tableRows = document.querySelectorAll("#resultsTable tbody tr");
  const updated = [];

  tableRows.forEach((row, i) => {
    const select = row.querySelector("select");
    const userValue = select ? select.value : "---"
    updated.push({
      text: originalData[i].text,
      classification_ai: originalData[i].aiClassification,
      confidence_ai: originalData[i].confidence,
      classification_user: userValue,
      project: uploadedFileName,
      original_text: originalData[i].original_text,
      match_score: originalData[i].match_score,
      page: originalData[i].page,
    });

  });

  return updated;
}

function deleteRequirement(entryToDelete) {
  const updated = window.extracted_requirements.filter(
    r => !(r.text === entryToDelete.text && r.page === entryToDelete.page)
  );
  window.extracted_requirements = updated;
  render(document.getElementById("resultsTable"), updated);
}


export const buildRequirementsTable = {
  render,
  extractData
};



// /*
//     This file contains the functions that are used to create the table that will be used to classify the requirements.
//     Created by: Paulo Cerqueira
// */

// let sortDirections = {
//   "Confidence": "asc",
//   "AI Classification": "asc"
// }

// // Function to create the head of the table
// export function tableHead(table, data) {
//     let thead = document.createElement("thead");
//     let row = document.createElement("tr");

//     let keys = Object.keys(data[0]);

//     for (let key of keys) {
//       let th = document.createElement("th");
//       let text = document.createTextNode(key);
//       console.log(text, typeof text);
//       th.appendChild(text);
//       row.appendChild(th);


//       if (key === "Confidence" || key === "AI Classification") {
//         th.style.cursor = "pointer";

//         th.addEventListener("click", () => {
//           let currentDirection = sortDirections[key];

//           if (key === "Confidence") {
//             data.sort((a, b) => {
//               if (currentDirection === "asc") {
//                 return a.Confidence - b.Confidence;
//               } else {
//                 return b.Confidence - a.Confidence;
//               }
//             });
//           } else if (key === "AI Classification") {
//             data.sort((a, b) => {
//               if (currentDirection === "asc") {
//                 return a["AI Classification"].localeCompare(b["AI Classification"]);
//               } else {
//                 return b["AI Classification"].localeCompare(a["AI Classification"]);
//               }
//             });
//           }

//           sortDirections[key] = currentDirection === "asc" ? "desc" : "asc";

//           table.innerHTML = "";
//           tableHead(table, data);
//           generateTable(table, data);
//         });
//       }
//     }

//     let th = document.createElement("th");
//     let text = document.createTextNode("User Classification");
//     th.appendChild(text);
//     row.appendChild(th);
    
//     let thDelete = document.createElement("th");
//     let textDelete = document.createTextNode("Delete");
//     thDelete.appendChild(textDelete);
//     row.appendChild(thDelete);

//     thead.appendChild(row);
//     table.appendChild(thead);
//   }

// // Function to create the table
// export function generateTable(table, data, extracted_requirements, redrawTable) {
// let classifications = [
//     "---", "Functional", "NF - Security", "NF - Availability", "NF - Legal", "NF - Look and Feel",
//     "NF - Maintenability", "NF - Operacional", "NF - Performance", "NF - Scalability",
//     "NF - Usability", "NF - Fault Tolerance", "NF - Portability", "Out of Scope"
// ];
// let tbody = document.createElement("tbody");

// for (let element of data) {
//     let row = document.createElement("tr");

//     for (let key in element) {
//     let cell = document.createElement("td");
//     let text;

//     if (key === "Confidence") {
//       let percentage = (element[key] * 100).toFixed(0) + "%";
//       text = document.createTextNode(percentage);
//     } else {
//       text = document.createTextNode(element[key]);
//     }

//     cell.appendChild(text);
//     row.appendChild(cell);
//     }
//     table.appendChild(row);

//     let cell = document.createElement("td");
//     let select = document.createElement("select");

//     classifications.forEach(classification => {
//     let option = document.createElement("option");
//     option.value = classification;
//     option.textContent = classification;
//     select.appendChild(option);
//     });

//     cell.appendChild(select);
//     row.appendChild(cell);

//     let deleteCell = document.createElement("td");
//     let deleteButton = document.createElement("button");
//     deleteButton.textContent = "🗑️";
//     deleteButton.style.cursor = "pointer";
//     deleteButton.title("Delete Requirement");

//     deleteButton.addEventListener("click", () => {
//       const indexToDelete = data.indexOf(element);
//       if (indexToDelete !== -1) {
//         data.splice(indexToDelete, 1);
//         extracted_requirements.splice(indexToDelete, 1);
//         redrawTable();
//       }
//     });

//     deleteCell.appendChild(deleteButton);
//     row.appendChild(deleteCell);

//     tbody.appendChild(row);
// }

// table.appendChild(tbody);
// document.getElementById("saveBtn").style.display = "block";
// }