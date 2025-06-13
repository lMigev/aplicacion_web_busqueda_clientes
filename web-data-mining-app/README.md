# Web Data Mining Application

This project is a web application designed for data mining, allowing users to search for potential clients based on specific criteria. The application retrieves contact information for professionals, such as physiotherapists, and presents it in a user-friendly interface.

## Project Structure

```
web-data-mining-app
├── src
│   ├── app.py                # Entry point of the application
│   ├── models
│   │   └── search_model.py   # Contains the SearchModel class for processing search queries
│   ├── routes
│   │   └── search_routes.py   # Defines API endpoints for search functionality
│   ├── services
│   │   └── data_mining_service.py # Contains DataMiningService for data mining operations
│   └── templates
│       └── index.html        # HTML template for user interface
├── requirements.txt          # Lists project dependencies
├── README.md                 # Documentation for the project
└── .gitignore                # Specifies files to ignore in version control
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd web-data-mining-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/app.py
   ```

## Usage Guidelines

- Open your web browser and navigate to `http://localhost:5000` to access the application.
- Enter your search criteria (e.g., 'Fisioterapeutas en Panamá') in the provided input field.
- Submit the form to retrieve a list of potential clients based on your search.

## Overview of Functionality

The application allows users to:
- Input search criteria to find potential clients.
- Retrieve and display contact information, including names, emails, phone numbers, and locations.
- Utilize a clean and intuitive user interface for seamless interaction.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.