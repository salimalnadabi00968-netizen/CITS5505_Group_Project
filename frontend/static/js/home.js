let map = L.map('map', {
  scrollWheelZoom: false
}).setView([-31.9805, 115.8178], 14);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

markerData.forEach(function(m) {
  const popup = document.createElement('div');
  popup.className = 'perthpins-popup';

  const title = document.createElement('strong');
  title.className = 'perthpins-popup-title';
  title.textContent = m.title || 'Untitled';

  let place = null;
  if (m.place_name) {
    place = document.createElement('div');
    place.className = 'perthpins-popup-place';
    place.textContent = m.place_name;
  }

  const category = document.createElement('span');
  category.className = 'perthpins-popup-category';
  category.textContent = m.category || 'Uncategorised';

  const rating = document.createElement('div');
  rating.className = 'perthpins-popup-rating';
  rating.textContent = m.rating ? `Rating: ${m.rating} / 5` : 'Not rated yet';

  const link = document.createElement('a');
  link.href = `/checkins/${m.id}`;
  link.textContent = 'View Details →';
  link.style.fontSize = '0.82rem';

  popup.appendChild(title);
  if (place) popup.appendChild(place);
  popup.appendChild(category);
  popup.appendChild(rating);
  popup.appendChild(link);

  L.marker([m.lat, m.lng])
    .addTo(map)
    .bindPopup(popup);
});

if (markerData.length > 0) {
  const bounds = markerData.map(m => [m.lat, m.lng]);
  map.fitBounds(bounds, { padding: [40, 40] });
}
