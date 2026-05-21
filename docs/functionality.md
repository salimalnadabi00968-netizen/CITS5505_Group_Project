# Functionality

This document lists the features currently implemented in PerthPins.

1. Register with username, email, and hashed password.
2. Log in and log out using Flask-Login session management.
3. Browse recent check-ins on the homepage.
4. View all check-ins on the homepage Leaflet map.
5. Browse all check-ins on the Explore page.
6. Filter Explore results by category and minimum rating.
7. Sort Explore results by newest or highest rated.
8. Search check-ins by title or description.
9. Create a check-in with place name, map location, photos, title, category, rating, and description.
10. Pick a check-in location using the embedded Leaflet map picker.
11. View a full check-in detail page with photos, description, exact map location, comments, saves, and author information.
12. Add comments to a check-in when logged in.
13. Save or unsave check-ins as favourites when logged in.
14. View a personal profile page with avatar, bio, own check-ins, average rating, and saved check-ins.
15. Edit profile username, bio, and avatar.
16. Delete your own check-ins from the profile page.

## Page Coverage

- `login.html`: login
- `register.html`: registration
- `index.html`: homepage, latest check-ins, map
- `explore.html`: browse, filter, sort, and search results
- `new-checkin.html`: create check-in and pick map location
- `checkin_details.html`: full check-in detail, comments, favourites
- `profile.html`: profile editing, own check-ins, saved check-ins
