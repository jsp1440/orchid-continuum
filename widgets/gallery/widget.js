// Orchid Gallery Widget JavaScript

// Example orchid data (you will replace with real JSON later)
const orchids = [
  { name: "Cattleya dowiana", img: "https://via.placeholder.com/150?text=Cattleya+dowiana" },
  { name: "Phalaenopsis amabilis", img: "https://via.placeholder.com/150?text=Phalaenopsis+amabilis" },
  { name: "Oncidium gramineum", img: "https://via.placeholder.com/150?text=Oncidium+gramineum" }
];

// Function to render the gallery
function renderGallery() {
  const gallery = document.getElementById("oc-gallery");
  if (!gallery) return;

  const html = orchids.map(o => `
    <figure>
      <img src="${o.img}" alt="${o.name}">
      <figcaption>${o.name}</figcaption>
    </figure>
  `).join("");

  gallery.innerHTML = `<div class="oc-grid">${html}</div>`;
}

// Run when page loads
document.addEventListener("DOMContentLoaded", renderGallery);
