# System Patterns

## Data Structure
- JSON-based data storage
- Hierarchical organization by rooms
- Consistent patterns for costs, notes, and attachments
- Standardized contractor information format

## Key Technical Decisions
1. Use of JSON for data storage
2. Hierarchical organization of renovation data
3. Standardized object patterns for common elements (costs, attachments, contact info)
4. Consistent property naming conventions

## Architecture Patterns
1. Room-based organization
   - Each room is a top-level object
   - Consistent internal structure for room elements
   - Budget tracking per room

2. Common Object Patterns
   - Budget objects include amount, notes, attachments
   - Contractor objects include contact info, credentials, rates
   - Item objects include costs, notes, vendor information

3. Document References
   - Consistent attachment handling
   - PDF and image file references
   - Organized by room/category

4. Data Persistence and Logging
   - Automatic backup creation before saves
   - Timestamped saves with user attribution
   - Comprehensive event logging
   - JSON data validation before save
   - Real-time data visualization through JSON viewer

5. Happiness Tracking Pattern
   - Regular happiness check intervals (every major feature update)
   - JSON-based happiness record storage
   - Schema validation for happiness records
   - Timestamp tracking for each record
   - Reason documentation for happy/unhappy states

6. GitHub Integration Pattern
   - Regular commits at defined intervals
   - if user is happy, commit to main
   - if user is unhappy, commit to feature branches
   - Branch strategy:
     * main: stable production code
     * feature branches: new development
   - Commit message standards
   - Version tagging for releases

7. Testing Patterns
   - Input Field Testing:
     * Clear all existing content first
     * Test with completely new data
     * Avoid modifying existing content
     * Verify data persistence after save
   - Version Management:
     * Each save creates timestamped version
     * Maintain version history in dedicated directory
     * Allow loading previous versions
     * Validate loaded versions before applying
   - User Interface Patterns:
     * Clear feedback for user actions
     * Visual confirmation of saves
     * Error handling with clear messages
     * Real-time data visualization
