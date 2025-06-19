/*
    This file contains the functions that are used to create the table that will be used to classify the requirements.
    Created by: Paulo Cerqueira
*/

let sortDirections = {
  "Confidence": "asc",
  "AI Classification": "asc"
}

// Function to create the head of the table
export function tableHead(table, data) {
    let thead = document.createElement("thead");
    let row = document.createElement("tr");

    let keys = Object.keys(data[0]);

    for (let key of keys) {
      let th = document.createElement("th");
      let text = document.createTextNode(key);
      console.log(text, typeof text);
      th.appendChild(text);
      row.appendChild(th);


      if (key === "Confidence" || key === "AI Classification") {
        th.style.cursor = "pointer";

        th.addEventListener("click", () => {
          let currentDirection = sortDirections[key];

          if (key === "Confidence") {
            data.sort((a, b) => {
              if (currentDirection === "asc") {
                return a.Confidence - b.Confidence;
              } else {
                return b.Confidence - a.Confidence;
              }
            });
          } else if (key === "AI Classification") {
            data.sort((a, b) => {
              if (currentDirection === "asc") {
                return a["AI Classification"].localeCompare(b["AI Classification"]);
              } else {
                return b["AI Classification"].localeCompare(a["AI Classification"]);
              }
            });
          }

          sortDirections[key] = currentDirection === "asc" ? "desc" : "asc";

          table.innerHTML = "";
          tableHead(table, data);
          generateTable(table, data);
        });
      }
    }

    let th = document.createElement("th");
    let text = document.createTextNode("User Classification");
    th.appendChild(text);
    row.appendChild(th);
    thead.appendChild(row);
    table.appendChild(thead);
  }

// Function to create the table
export function generateTable(table, data) {
let classifications = [
    "---", "Functional", "NF - Security", "NF - Availability", "NF - Legal", "NF - Look and Feel",
    "NF - Maintenability", "NF - Operacional", "NF - Performance", "NF - Scalability",
    "NF - Usability", "NF - Fault Tolerance", "NF - Portability", "Out of Scope"
];
let tbody = document.createElement("tbody");

for (let element of data) {
    let row = document.createElement("tr");

    for (let key in element) {
    let cell = document.createElement("td");
    let text;

    if (key === "Confidence") {
      let percentage = (element[key] * 100).toFixed(0) + "%";
      text = document.createTextNode(percentage);
    } else {
      text = document.createTextNode(element[key]);
    }

    cell.appendChild(text);
    row.appendChild(cell);
    }
    table.appendChild(row);

    let cell = document.createElement("td");
    let select = document.createElement("select");

    classifications.forEach(classification => {
    let option = document.createElement("option");
    option.value = classification;
    option.textContent = classification;
    select.appendChild(option);
    });

    cell.appendChild(select);
    row.appendChild(cell);
    tbody.appendChild(row);
}

table.appendChild(tbody);
document.getElementById("saveBtn").style.display = "block";
}