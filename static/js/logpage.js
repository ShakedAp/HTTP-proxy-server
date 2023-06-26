const logContainer = document.getElementById('log_container');

const storedHTML = sessionStorage.getItem("logContainer");
if (storedHTML)
  logContainer.innerHTML = storedHTML;

function updateLogHTML(log)
{
  let para = document.createElement("p");
  para.textContent = log; 

  const isScrolledToBottom = logContainer.scrollHeight - logContainer.clientHeight <= logContainer.scrollTop + 1;

  logContainer.appendChild(para);
  if (logContainer.childElementCount > 100)
    logContainer.removeChild(logContainer.firstElementChild);

  if (isScrolledToBottom)
    logContainer.scrollTop = logContainer.scrollHeight - logContainer.clientHeight;
}


function fetchData() {
  fetch('/data')
    .then(response => response.json())
    .then(data => {
      data.forEach(element => {
        updateLogHTML(element);
      });
    })
    .catch(error => console.log(error));
}




window.addEventListener('unload', function() {
  sessionStorage.setItem('logContainer', logContainer.innerHTML);
}); 

setInterval(fetchData, 1000);