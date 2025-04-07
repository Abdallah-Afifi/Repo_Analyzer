# GitHub Repository Analyzer

A comprehensive tool for analyzing GitHub repositories to extract insights and visualize key metrics.

## Features

- **Repository Overview**: Basic information about the repository, including stars, forks, watchers, and issue counts.
- **Commit Analysis**: Analyze commit patterns and contributor activity over time.
- **Language Distribution**: Visualize the programming languages used in the repository.
- **Contributor Insights**: View top contributors and their contribution statistics.
- **Issue Analysis**: Track open and closed issues and resolution rates.

## Tech Stack

- **Backend**: Python with Flask
- **Data Analysis**: Pandas, NumPy
- **Visualization**: Chart.js (browser), Matplotlib, Seaborn, Plotly (server-side)
- **API Integration**: PyGithub for GitHub API access

## Prerequisites

- Python 3.8+
- GitHub Personal Access Token

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Repo_Analyzer.git
   cd Repo_Analyzer
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Create a `.env` file in the backend directory with your GitHub token:
   ```
   SECRET_KEY=your-secret-key
   GITHUB_TOKEN=your-github-personal-access-token
   FLASK_APP=app.py
   FLASK_ENV=development
   ```
   
   > **Note:** You can generate a GitHub Personal Access Token from your [GitHub Settings](https://github.com/settings/tokens). The token needs `repo` scope to access repository data.

## Running the Application

1. Activate the virtual environment (if not already active):
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the Flask application:
   ```bash
   cd backend
   python app.py
   ```

3. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Enter a GitHub repository name in the format `owner/repo` (e.g., `facebook/react`)
2. Click "Analyze Repository" button
3. View the generated analysis and visualizations

## Project Structure

```
.
├── backend/
│   ├── api/              # API endpoints
│   ├── models/           # Data models
│   ├── static/           # Static files
│   ├── templates/        # HTML templates
│   ├── utils/            # Utility functions
│   ├── app.py            # Main application file
│   ├── config.py         # Configuration
│   └── requirements.txt  # Python dependencies
│
└── frontend/             # Future React frontend
    └── src/
        ├── components/   # UI components
        ├── pages/        # Page components
        ├── services/     # API services
        └── utils/        # Utility functions
```

## Future Enhancements

- Advanced code analysis metrics
- Pull request statistics
- Release and tag analysis
- Contributor network visualization
- Comparative analysis between repositories
- Full React frontend implementation

## License

MIT