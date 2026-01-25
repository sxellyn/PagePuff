# 🌸 PagePuff Frontend

PagePuff React Frontend - Personal manga library with personalized recommendations.

## 🚀 Technologies

- **React 18** - JavaScript library for interfaces
- **React Router** - Routing
- **Axios** - HTTP client for API calls
- **Vite** - Fast build tool
- **React Icons** - Icons

## 📦 Installation

1. Install dependencies:
```bash
npm install
```

2. Configure API URL (optional):
```bash
cp .env.example .env
```

Edit the `.env` file if needed:
```
VITE_API_URL=http://localhost:8080
```

3. Start development server:
```bash
npm start
# or
npm run dev
```

Frontend will be available at: http://localhost:3000

## 🏗️ Project Structure

```
frontend/
├── public/          # Static files
├── src/
│   ├── components/  # Reusable components
│   │   └── Header.jsx
│   ├── context/     # Context API
│   │   └── AuthContext.jsx
│   ├── pages/       # Application pages
│   │   ├── Home.jsx
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Mangas.jsx
│   │   ├── MangaDetail.jsx
│   │   └── Favorites.jsx
│   ├── services/    # API services
│   │   └── api.js
│   ├── App.jsx      # Main component
│   ├── main.jsx     # Entry point
│   └── index.css    # Global styles
├── package.json
└── vite.config.js
```

## 🎨 Features

- ✨ **Home** - Landing page with presentation
- 📚 **Manga Library** - Lists all mangas with search
- 📖 **Manga Details** - Full view with favorite option
- ❤️ **Favorites** - User's favorite mangas list
- 🔐 **Authentication** - Login and user registration

## 🔗 Backend Integration

The frontend communicates with the backend through the Gateway on port 8080.

Endpoints used:
- `/user/login` - Authentication
- `/user/register` - Registration
- `/user/favorites` - Favorites
- `/manga/mangas` - Manga list
- `/manga/mangas/:id` - Manga details

## 🎨 Design

The design was created with a soft and modern color palette:
- **Primary**: Pink (#ff6b9d)
- **Secondary**: Light purple (#c8a8e9)
- **Background**: Very light pink (#fff5f8)
- **Surface**: White (#ffffff)

## 📝 Available Scripts

- `npm start` or `npm run dev` - Starts development server
- `npm run build` - Creates production build
- `npm run preview` - Preview production build

## 🌐 Requirements

- Node.js 18+
- npm or yarn
- Backend running on port 8080
