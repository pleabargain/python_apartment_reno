# Apartment Renovation Manager

A comprehensive data management system for tracking and organizing apartment renovation projects. This system helps manage renovation details, costs, contractor information, and documentation across multiple rooms.

## Features

- Room-based organization of renovation data
- Budget and cost tracking
- Contractor and vendor information management
- Document and specification storage
- Automated cost reporting
- File attachment system for PDFs, images, and documentation

## Project Structure

```
project/
├── cline_docs/           # Project documentation
├── guest_bathroom/       # Room-specific attachments
├── kitchen/             # Room-specific attachments
├── living_room/         # Room-specific attachments
├── master_bedroom/      # Room-specific attachments
└── [Python files]       # Data processing scripts
```

## Technical Stack

- Python for data processing
- JSON for data storage
- File-based document management
- Markdown for report generation

## Data Organization

- JSON-based data structure with strict schema compliance
- Hierarchical organization by rooms
- Standardized patterns for costs, notes, and attachments
- Consistent contractor information format
- Currency values stored as floating point numbers
- Dates in ISO 8601 format (YYYY-MM-DD)

## Features Status

✅ Completed:
- Initial JSON data structure
- Room-based organization
- Contractor information structure
- Budget tracking system
- File attachment system
- Enhanced Room Cost Report functionality
  - Custom report filenames with dates
  - User attribution
  - Report generation tracking
  - Markdown export

🚧 In Progress:
1. Schema Documentation
   - JSON schema creation
   - Field documentation
   - Data type definitions
   - Validation rules

2. Data Validation
   - Schema validation implementation
   - Cost calculation validation
   - File attachment path verification

## File Requirements

- All costs must be numeric
- Required fields: project_name, last_updated, status
- Each room must have a budget object
- Contact information must follow standard format
- File paths in attachments must be relative to project root

## Reports

The system generates detailed cost reports in Markdown format with:
- Customized filenames including dates (YYYY.MM.DD)
- User attribution in headers
- Report generation date tracking
- Organized cost breakdowns by room

## GitHub Workflow

### Commands Reference

```bash
# Basic Git Operations
git add .                    # Stage all changes
git commit -m "type: message" # Create commit with type prefix
git push origin main         # Push to main branch

# Branch Management
git checkout -b feature/name # Create new feature branch
git push origin feature/name # Push feature branch
git checkout main           # Switch to main branch
git pull origin main        # Update main branch
git merge feature/name      # Merge feature branch into main

# Commit Message Types
feat:     # New features
fix:      # Bug fixes
docs:     # Documentation updates
test:     # Test updates
refactor: # Code refactoring
```

### Branch Strategy
- `main`: Production-ready code
  - Direct commits when user happiness check passes
  - Must be stable and tested
- `feature/*`: Development branches
  - Created when user happiness check fails
  - Used for improvements and fixes
  - Merged to main after review

### Workflow Steps
1. Regular happiness checks after feature updates
2. If happy:
   - Commit directly to main
   - Include happiness record
3. If unhappy:
   - Create feature branch
   - Document reasons
   - Make improvements
   - Re-check happiness before merge

## Development Setup

1. Clone the repository
2. Ensure Python is installed
3. Place renovation documents in appropriate room directories
4. Maintain JSON data according to schema specifications
5. Configure Git for branch management
6. Follow happiness tracking workflow
