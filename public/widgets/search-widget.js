(function() {
  class OrchidSearchWidget extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            font-family: Arial, sans-serif;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            padding: 16px;
            max-width: 400px;
            background: #f9fff9;
          }
          h3 {
            margin-top: 0;
            color: #2e7d32;
          }
          input {
            width: 100%;
            padding: 8px;
            margin-bottom: 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
          }
          button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            text-align: center;
            border-radius: 4px;
            cursor: pointer;
          }
          button:hover {
            background-color: #45a049;
          }
          .results {
            margin-top: 12px;
          }
          .orchid {
            border-bottom: 1px solid #ddd;
            padding: 8px 0;
          }
          .orchid:last-child {
            border-bottom: none;
          }
        </style>
        <h3>Search Orchids</h3>
        <input type="text" id="searchBox" placeholder="Type genus or species...">
        <button id="searchBtn">Search</button>
        <div class="results" id="results"></div>
      `;
    }

    connectedCallback() {
      this.shadowRoot.querySelector("#searchBtn")
        .addEventListener("click", () => this.performSearch());
    }

    async performSearch() {
      const query = this.shadowRoot.querySelector("#searchBox").value.trim();
      const resultsContainer = this.shadowRoot.querySelector("#results");
      resultsContainer.innerHTML = "<p>Searching...</p>";

      if (!query) {
        resultsContainer.innerHTML = "<p>Please enter a search term.</p>";
        return;
      }

      try {
        // 🔧 Replace this API URL with your Orchid Continuum endpoint later
        const response = await fetch(
          `https://orchid-continuum-api.example.com/search?query=${encodeURIComponent(query)}`
        );
        const orchids = await response.json();

        if (orchids.length === 0) {
          resultsContainer.innerHTML = "<p>No orchids found.</p>";
          return;
        }

        resultsContainer.innerHTML = orchids.map(orchid => `
          <div class="orchid">
            <strong>${orchid.name}</strong><br>
            <em>${orchid.genus} ${orchid.species}</em><br>
            ${orchid.description || "No description available."}
          </div>
        `).join("");
      } catch (err) {
        resultsContainer.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
      }
    }
  }

  customElements.define("orchid-search-widget", OrchidSearchWidget);
})();

