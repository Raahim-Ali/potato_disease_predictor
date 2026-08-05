document.addEventListener("DOMContentLoaded", () => {
  const countrySelect = document.getElementById("country");
  const citySelect = document.getElementById("city");

  // Fetch countries from restcountries API
  async function fetchCountries() {
    try {
      const response = await fetch(
        "https://restcountries.com/v3.1/all?fields=name,cca2"
      );
      const countries = await response.json();

      // Check if countries is an array
      if (Array.isArray(countries)) {
        // Sort the countries alphabetically by name
        countries.sort((a, b) => {
          const nameA = a.name.common.toLowerCase();
          const nameB = b.name.common.toLowerCase();
          if (nameA < nameB) {
            return -1;
          }
          if (nameA > nameB) {
            return 1;
          }
          return 0; // names are equal
        });

        // Populate country dropdown
        countries.forEach((country) => {
          const option = document.createElement("option");
          option.value = country.cca2; // cca2 is country code from geonames
          option.textContent = country.name.common;
          countrySelect.appendChild(option);
        });
      } else {
        console.error("Expected an array of countries, but got:", countries);
      }
    } catch (error) {
      console.error("Error fetching countries:", error);
    }
  }

  // Fetch cities from geonames API
  async function fetchCities(countryCode) {
    try {
      const response = await fetch(
        `http://api.geonames.org/searchJSON?country=${countryCode}&maxRows=50&username=raahim_21`
      );
      const data = await response.json();

      // Check if geonames exists in the response data and is an array
      if (data.geonames && Array.isArray(data.geonames)) {
        const cities = data.geonames;
        citySelect.innerHTML = '<option value="">Select a City</option>'; // reset cities dropdown

        // Populate city dropdown
        cities.forEach((city) => {
          const option = document.createElement("option");
          option.value = city.name;
          option.textContent = city.name;
          citySelect.appendChild(option);
        });
      } else {
        // If no geonames or it's not an array, display an error
        console.error("Error: No cities found in the GeoNames response", data);
        citySelect.innerHTML = '<option value="">No cities available</option>';
      }
    } catch (error) {
      console.error("Error fetching cities:", error);
      citySelect.innerHTML = '<option value="">Failed to fetch cities</option>';
    }
  }

  // When a country is selected, fetch cities
  countrySelect.addEventListener("change", (e) => {
    const countryCode = e.target.value;
    if (countryCode) {
      fetchCities(countryCode); // Fetch cities for the selected country
    } else {
      // Reset the cities dropdown if no country is selected
      citySelect.innerHTML = '<option value="">Select a City</option>';
    }
  });

  // Initialize countries dropdown
  fetchCountries();
});

// Function to handle prediction requests (called by buttons)
async function getPredictions(days) {
  const country = document.getElementById("country").value;
  const city = document.getElementById("city").value;
  const predictionsContainer = document.querySelector(".predictions-container");

  // Validate inputs
  if (!country || !city) {
    predictionsContainer.innerHTML = `
      <h3>Error</h3>
      <p style="color: red;">Please select both country and city before making predictions.</p>
    `;
    return;
  }

  // Loading message
  predictionsContainer.innerHTML = `
    <h3>Loading...</h3>
    <p>Fetching weather data and generating predictions for ${city}...</p>
  `;

  try {
    // Make API call to get predictions
    const response = await fetch(
      `/api/predict?country=${country}&city=${city}&days=${days}`
    );

    const data = await response.json();

    if (response.ok && data.predictions) {
      // Display successful predictions
      let html = `
        <h3>Predictions for ${data.city}, ${data.country} - Next ${
        data.days - 1
      } Days:</h3>
        <table>
          <thead>
  <tr>
    <th>Date</th>
    <th>Min Temp (°C)</th>
    <th>Max Temp (°C)</th>
    <th>Min Humidity (%)</th>
    <th>Max Humidity (%)</th>
    <th>Predicted Disease</th>
  </tr>
</thead>
<tbody>
  ${data.predictions
    .map(
      (pred) => `
    <tr>
      <td>${pred.Date}</td>
      <td>${pred.min_temp.toFixed(1)}</td>
      <td>${pred.max_temp.toFixed(1)}</td>
      <td>${pred.min_humidity}</td>
      <td>${pred.max_humidity}</td>
      <td>${pred["Predicted Disease"]}</td>
    </tr>
  `
    )
    .join("")}
</tbody>
        </table>
      `;

      predictionsContainer.innerHTML = html;
    } else {
      // Display error message
      predictionsContainer.innerHTML = `
        <h3>Error</h3>
        <p style="color: red;">
          ${data.error || "Failed to fetch predictions. Please try again."}
        </p>
      `;
    }
  } catch (error) {
    console.error("Error fetching predictions:", error);
    predictionsContainer.innerHTML = `
      <h3>Error</h3>
      <p style="color: red;">
        Network error occurred. Please check your connection and try again.
      </p>
    `;
  }
}

// Legacy form submission handler (keeping for compatibility)
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("location-form");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault(); // No page reloading on form submission

      // Get the clicked button's value
      const clickedButton = document.activeElement;
      if (clickedButton && clickedButton.tagName === "BUTTON") {
        const days = clickedButton.value;
        await getPredictions(days);
      }
    });
  }
});
