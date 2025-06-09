// responsive nav bar
function toggleMenu(){
    document.querySelector(".nav-right").classList.toggle('show')
}
   
  
  
// --- FETCH WEATHER INFO USING OPENWEATHERMAP API ---
const apiKey = "65a2b4e2a781eab6d8d2c63f22d5302a";
const city = "Srinagar";

async function getWeather() {
  try {
    const res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`);
    const data = await res.json();
    document.querySelector(".weather-city").innerText = `📍 ${data.name}`;
    document.querySelector(".weather-desc").innerText = `☁️ ${data.weather[0].description}`;
    document.querySelector(".weather-temp").innerText = `🌡️ Temperature: ${data.main.temp}°C`;
    document.querySelector(".weather-humidity").innerText = `💧 Humidity: ${data.main.humidity}%`;
  } catch {
    document.getElementById("weather-info").innerText = "⚠️ Failed to fetch weather.";
  }
}

getWeather();
// graph showing past 2 month prices of commodities
let chart;

// Load available commodities into dropdown
async function loadCommodities() {
    const response = await fetch('/api/commodities');
    const commodities = await response.json();

    const select = document.getElementById("commoditySelect");
    select.innerHTML = ""; // Clear any old options

    commodities.forEach(commodity => {
        const option = document.createElement("option");
        option.value = commodity;
        option.text = commodity;
        select.appendChild(option);
    });
    
    // Load default commodity chart (first in list)
    loadChart();
}

// Load chart for selected commodity
async function loadChart() {
    const commodity = document.getElementById("commoditySelect").value;

    const response = await fetch(`/api/past_prices?commodity=${commodity}`);
    const data = await response.json();

    // if (response.status !== 200) {
    //     alert(data.message || data.error);
    //     return;
    // }

    const ctx = document.getElementById('priceChart').getContext('2d');

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: `${commodity} Modal Price`,
                data: data.prices,
                borderColor: 'rgb(75, 192, 192)',
                fill: false,
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: 'Date' } },
                y: { title: { display: true, text: 'Price (Rs./Quintal)' } }
            }
        }
    });
}

// Initialize on page load
window.onload = loadCommodities;