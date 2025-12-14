# IPL Auction Frontend

A modern, responsive web frontend for the IPL Auction Strategist System. Built with vanilla HTML, CSS, and JavaScript.

## Features

- **Team Analysis**: Comprehensive gap analysis, weak points identification, and team matrix visualization
- **Live Auction Tracking**: Real-time auction state updates and live recommendations
- **Player Recommender**: AI-powered player recommendations grouped by priority (A/B/C)
- **AI Chat Assistant**: Interactive chat interface for strategy questions
- **Responsive Design**: Mobile-first approach with support for all screen sizes
- **Smooth Animations**: Performance-optimized animations and transitions

## Project Structure

```
Auction_Frontend/
├── index.html              # Home page
├── services.html           # Services/Features page
├── team-analysis.html      # Team analysis dashboard
├── live-auction.html       # Live auction tracking
├── recommender.html        # Interactive recommender
├── chat.html              # AI chat interface
├── css/
│   ├── style.css          # Main stylesheet
│   ├── animations.css     # Animation definitions
│   └── responsive.css     # Responsive breakpoints
├── js/
│   ├── main.js            # Main application logic
│   ├── api.js             # API communication layer
│   ├── animations.js      # Animation controllers
│   ├── team-analysis.js   # Team analysis functionality
│   ├── live-auction.js    # Live auction updates
│   ├── recommender.js     # Recommender interface
│   └── chat.js            # Chat interface
└── assets/
    └── images/            # Team logos, icons
```

## Getting Started

### Prerequisites

- A running instance of the IPL Auction Strategist backend API (default: `http://127.0.0.1:8000`)
- A modern web browser (Chrome, Firefox, Safari, Edge)

### Setup

1. Ensure the backend API is running on `http://127.0.0.1:8000`
2. Open `index.html` in your web browser, or
3. Serve the files using a local web server:

```bash
# Using Python
python -m http.server 8080

# Using Node.js (http-server)
npx http-server -p 8080

# Using PHP
php -S localhost:8080
```

4. Navigate to `http://localhost:8080` in your browser

## API Configuration

The frontend is configured to connect to the backend API at `http://127.0.0.1:8000` by default. To change this, edit `js/api.js`:

```javascript
const API_BASE_URL = 'http://your-api-url:port';
```

## Pages

### Home Page (`index.html`)
- Hero section with animated title
- Features overview
- Real-time auction statistics
- How it works section
- Team showcase

### Services Page (`services.html`)
- Detailed service descriptions
- Feature lists for each service
- Links to relevant pages

### Team Analysis Page (`team-analysis.html`)
- Team selector
- Team overview dashboard
- Gap analysis visualization
- Weak points display
- Team matrix visualization
- Player recommendations (Group A/B/C)

### Live Auction Page (`live-auction.html`)
- Auction status display
- Record player sale form
- Live recommendations panel (all teams)
- Recent sales feed
- Auto-refresh every 5 seconds

### Recommender Page (`recommender.html`)
- Team selection
- Group filtering (A/B/C)
- Role and speciality filters
- Search functionality
- Sort options
- Player detail modals

### Chat Page (`chat.html`)
- AI chat interface
- Team context selector
- Suggested questions
- Chat history (localStorage)
- Message timestamps

## API Endpoints Used

- `GET /state` - Current auction state
- `GET /teams/{team}/matrix` - Team matrix visualization
- `GET /teams/{team}/recommendations?group=A|B|C` - Grouped recommendations
- `GET /teams/{team}/gaps` - Detailed gap analysis
- `GET /teams/{team}/weak-points` - Weak points view
- `GET /live/recommendations` - Live recommendations for all teams
- `POST /auction/sell` - Record player sale
- `POST /chat` - AI chat endpoint

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Responsive Breakpoints

- Mobile: 320px - 767px
- Tablet: 768px - 1023px
- Desktop: 1024px - 1439px
- Large Desktop: 1440px+

## Color Scheme

- Primary: Cricket Green (#1B5E20)
- Secondary: Gold (#FFD700)
- Accent: Green (#4CAF50)
- Background: Light Gray (#F5F5F5)

## Features

### Animations
- Scroll-triggered animations
- Hover effects
- Loading indicators
- Smooth transitions
- Reduced motion support

### Accessibility
- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- Focus indicators

## Development

### Adding New Features

1. Create new JavaScript module in `js/` directory
2. Add corresponding HTML page if needed
3. Update navigation in `js/main.js`
4. Add styles in `css/style.css` or create new stylesheet

### Styling Guidelines

- Use CSS variables for colors (defined in `:root`)
- Follow mobile-first approach
- Use semantic class names
- Keep animations performance-optimized

## Troubleshooting

### API Connection Issues
- Verify backend is running on correct port
- Check CORS settings on backend
- Verify API_BASE_URL in `js/api.js`

### Styling Issues
- Clear browser cache
- Check browser console for errors
- Verify all CSS files are loaded

### JavaScript Errors
- Open browser developer console
- Check for API errors
- Verify all JavaScript files are loaded in correct order

## License

This project is part of the IPL Auction Strategist System.
