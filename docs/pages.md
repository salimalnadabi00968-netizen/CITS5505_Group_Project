# Page List

This file describes the main pages currently implemented in PerthPins.

| Page Name       | File                    | Purpose                                             |
|-----------------|-------------------------|-----------------------------------------------------|
| Login           | `login.html`            | Let existing users log in                           |
| Register        | `register.html`         | Let new users create an account                     |
| Home            | `index.html`            | Show the map and latest check-ins                   |
| Explore         | `explore.html`          | Browse, filter, sort, and search check-ins          |
| Check-in Detail | `checkin_details.html`  | Show one check-in with photos, map, comments, saves |
| New Check-in    | `new-checkin.html`      | Create and publish a new check-in                   |
| User Profile    | `profile.html`          | Manage personal profile, own posts, and saves       |

## Page Descriptions

### Login (`login.html`)
- **Purpose:** Allow existing users to log in.
- **Core Features:** Log in with username/email and password.

### Register (`register.html`)
- **Purpose:** Allow new users to create an account.
- **Core Features:** Register with username, email, password, and password confirmation.

### Home (`index.html`)
- **Purpose:** Give users an at-a-glance view of community activity around Perth and UWA.
- **Core Features:** View all check-ins on an interactive map, browse recent posts, and navigate to create a new check-in.

### Explore (`explore.html`)
- **Purpose:** Help users discover check-ins that match their interests.
- **Core Features:** Filter by category and minimum rating, sort by newest or highest rated, and search by keyword.

### Check-in Detail (`checkin_details.html`)
- **Purpose:** Let users read the full content of a check-in and engage with it.
- **Core Features:** View photos, description, place name, location, rating, author, comments, and save count; logged-in users can favourite and comment.

### New Check-in (`new-checkin.html`)
- **Purpose:** Allow logged-in users to share a place they have visited.
- **Core Features:** Submit a check-in with place name, map pin, photos, title, category, star rating, and description.

### User Profile (`profile.html`)
- **Purpose:** Give logged-in users a personal space to manage their activity.
- **Core Features:** View and edit avatar, username, and bio; view own check-ins, average rating, and saved check-ins; delete own check-ins.
