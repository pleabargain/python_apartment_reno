# Technical Context

## Technologies Used
- JSON for data storage and structure
- File-based document storage for attachments
- Python for data processing (based on .py files in environment)

## Development Setup
- Working directory: c:/Users/denni/Documents/python_apartment_reno
- VSCode as development environment
- Python scripts for data manipulation
- JSON for data storage

## Technical Constraints
1. Data Storage
   - JSON must maintain strict schema compliance
   - File paths in attachments must be relative to project root
   - Currency values stored as floating point numbers
   - Dates in ISO 8601 format (YYYY-MM-DD)

2. File Organization
   - Separate directories for each room's attachments
   - PDF, JPG, and other document formats supported
   - Consistent file naming conventions

3. Data Validation Requirements
   - All costs must be numeric
   - Required fields: project_name, last_updated, status
   - Each room must have a budget object
   - Contact information must follow standard format

4. Logging and Data Persistence
   - Server-side logging using Python's logging module
   - Log levels: DEBUG, INFO, ERROR
   - Log file: server.log
   - Log format: timestamp - level - message
   - Automatic backup creation with timestamps
   - JSON data validation before saves
   - User event tracking and attribution

5. User Interface Features
   - Real-time JSON data viewer
   - Automatic data refresh after saves
   - Success/error notifications
   - Timestamped updates
   - Backup creation before changes

6. Happiness Tracking System
   - JSON Schema validation for happiness records
   - Automated timestamp tracking
   - Structured reason documentation
   - Integration with GitHub workflow

7. GitHub Integration
   - Command Reference (stored in README.md):
     * git add . : Stage all changes
     * git commit -m "message" : Create commit
     * git push origin main : Push to main branch
     * git checkout -b feature/name : Create feature branch
     * git push origin feature/name : Push feature branch
   - Branch Management:
     * main: Production-ready code
     * feature/*: Development branches
   - Commit Message Format:
     * feat: New features
     * fix: Bug fixes
     * docs: Documentation updates
     * test: Test updates
     * refactor: Code refactoring

8. Testing Best Practices
   - HTML Element Testing:
     * Clear existing content before testing
     * Remove all text from input fields
     * Enter new test data from scratch
     * Avoid modifying existing text
     * Verify changes are saved correctly
   - Data Validation:
     * Test with empty fields
     * Test with new data
     * Verify JSON structure after changes
     * Check version history after saves
