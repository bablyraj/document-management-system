# Secure Docs

A secure and modern document management system built with Python (FastAPI & Flask).

## Features

- **User Authentication**: Secure signup and login functionality with JWT authentication.
- **Document Management**: Upload, view, download, and delete documents.
- **Profile Management**: Update user profile information and avatar.
- **Modern UI**: Responsive design with a clean interface.
- **Dark Mode**: Built-in dark mode support for better accessibility and user preference.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Flask (Python) serving HTML/CSS/JS templates
- **Database**: SQLite
- **Styling**: Custom CSS with CSS Variables for theming

## Screenshots

### Authentication
| Login | Signup |
|:---:|:---:|
| ![Login Page](assets/login.png) | ![Signup Page](assets/signup.png) |

### Dashboard
| Light Mode | Dark Mode |
|:---:|:---:|
| ![Dashboard Light](assets/dashboard_light_mode.png) | ![Dashboard Dark](assets/dashboard_dark_mode.png) |

### User Experience
| Before Login | After Login |
|:---:|:---:|
| ![Before Login](assets/before_login.png) | ![After Login](assets/after_login.png) |

| Document Interaction | Navigation Menu |
|:---:|:---:|
| ![Document Hover](assets/document_hover.png) | ![Nav Menu](assets/nav_menu.png) |

| Profile | About Us |
|:---:|:---:|
| ![Profile Page](assets/profile.png) | ![About Us](assets/about_us.png) |

## Setup & Running

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Backend**:
   ```bash
   python backend.py
   ```
   The backend API will run at `http://127.0.0.1:8000`.

3. **Start the Frontend**:
   ```bash
   python frontend.py
   ```
   The frontend application will run at `http://127.0.0.1:5000`.

4. **Access the App**:
   Open your browser and navigate to `http://127.0.0.1:5000`.
