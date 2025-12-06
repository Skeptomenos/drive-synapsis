# Usage Guide

This comprehensive guide covers all features of the Google Drive MCP Server and how to use them with AI assistants like Gemini CLI.

## Table of Contents

- [Getting Started](#getting-started)
- [Search & Discovery](#search--discovery)
- [Google Docs Operations](#google-docs-operations)
- [Google Sheets Operations](#google-sheets-operations)
- [File Management](#file-management)
- [Local Synchronization](#local-synchronization)
- [Sharing & Permissions](#sharing--permissions)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)

## Getting Started

### Basic Interaction Pattern

The MCP server enables natural language interaction with Google Drive through your AI assistant. Simply describe what you want to do, and the AI will use the appropriate tools.

**Example:**
```
Search my Drive for "Project Budget" and show me the first 5 results
```

### Understanding Aliases

When the server returns search results, it assigns short **aliases** (like `A`, `B`, `C`) to files. Use these aliases in subsequent commands instead of typing file IDs.

**Example:**
```
Search for "Meeting Notes"
```

**Response:**
```
A: Weekly Standup Notes (Confidence: 85%)
   Notes from the weekly team standup meetings...

B: Client Meeting - Q3 Review (Confidence: 72%)
   Discussion of Q3 goals and deliverables...
```

**Follow-up:**
```
Read file A
```

## Search & Discovery

### Basic Search

Search for files using simple queries:

```
Search my Drive for "financial report"
```

**Features:**
- **Smart ranking**: Results are scored based on title and content matches
- **Content snippets**: Preview of file content to verify relevance
- **Confidence scores**: Percentage indicating match quality

### Advanced Search

Filter results by type, date, and ownership:

```
Find all spreadsheets modified after 2024-01-01 containing "sales data"
```

**Available filters:**
- **File type**: `doc`, `sheet`, `folder`, `pdf`, `image`
- **Modified date**: `YYYY-MM-DD` format
- **Owner**: `me` (your files) or `anyone` (all accessible files)

**Example:**
```
Search for PDFs owned by me modified after 2024-06-01 with "invoice"
```

### Folder Search

Search within a specific folder:

```
Search in folder [folder_id] for "quarterly review"
```

> [!TIP]
> First search for the folder by name, get its alias, then search within it.

**Example workflow:**
```
1. Search for folder "2024 Reports"
2. Search in folder A for "Q4"
```

## Google Docs Operations

### Reading Documents

#### Basic Read

Read a Google Doc and convert it to Markdown:

```
Read document A
```

**Output format:**
- **Headers**: Converted to `#`, `##`, `###` syntax
- **Bold/Italic**: Converted to `**bold**` and `*italic*`
- **Lists**: Preserved as Markdown lists
- **Tables**: Converted to Markdown tables
- **Links**: Preserved with `[text](url)` syntax

#### Advanced Read with Options

Download with advanced formatting options:

```
Read document B with comments and preserve all links
```

**Options:**
- **Include comments**: Extract inline and suggestion comments
- **Link rewriting**: Convert Drive links to relative references
- **Tab support**: Handle multi-tab documents (Google Docs with tabs)

### Creating Documents

#### Create from Content

```
Create a new Google Doc called "Project Plan" with these headers: 
Introduction, Timeline, Budget
```

**Features:**
- Accepts Markdown formatting
- Automatically applies Google Docs styles
- Supports rich text elements

#### Create from Template

Use an existing document as a template:

```
Create a new document called "Meeting Notes" based on template [template_id]
```

### Updating Documents

#### Upload Local Changes

```
Update document A with content from local file docs/notes.md
```

> [!WARNING]
> By default, updates run in **dry-run mode** and show a diff of changes. Set `dry_run=False` to apply changes.

**Safety features:**
- **Conflict detection**: Warns if remote file changed since last sync
- **Diff preview**: Shows exactly what will change
- **Force option**: Override conflict warnings if needed

#### Append to Document

Add content to the end of a document:

```
Append this text to document B: "Meeting adjourned at 3:30 PM"
```

### Advanced Document Features

#### Insert at Position

Insert content at a specific location:

```
Insert "## New Section" at position 150 in document C
```

#### Replace Content

Replace specific text in a document:

```
In document A, replace "Q3 2024" with "Q4 2024"
```

**Parameters:**
- **target_text**: Text to find and replace
- **replacement_text**: New text to insert
- **all_occurrences**: Replace all matches or just the first

#### Extract Headings

Get a table of contents from a document:

```
Show me all headings in document D
```

**Output:**
```
Heading 1: Introduction (Level 1)
  Heading 1.1: Background (Level 2)
  Heading 1.2: Objectives (Level 2)
Heading 2: Methodology (Level 1)
```

#### Working with Templates

List available templates:

```
Show me all document templates
```

Apply a template to existing content:

```
Apply template "Company Memo" to document E
```

## Google Sheets Operations

### Reading Sheets

#### Read as CSV

```
Read spreadsheet A as CSV
```

**Features:**
- Preserves cell values
- Maintains proper CSV escaping
- Handles multiple sheets

#### Read Specific Range

```
Read cells A1:D10 from spreadsheet B
```

#### Read by Sheet Name

```
Read sheet "Q4 Data" from spreadsheet C
```

### Creating Sheets

#### Create from Data

```
Create a new spreadsheet called "Sales Report" with headers:
Date, Product, Quantity, Revenue
```

#### Create from CSV

```
Create a spreadsheet from this CSV data:
[paste CSV content]
```

### Updating Sheets

#### Update Cell Range

```
In spreadsheet A, update range B2:B5 with values: 100, 250, 175, 300
```

#### Append Row

Add data to the next available row:

```
Append a new row to spreadsheet B: 2024-12-06, Widget, 50, $1250
```

#### Batch Update

Update multiple ranges at once:

```
In spreadsheet C:
- Set A1 to "Updated Report"
- Set C1:E1 to headers: "Product", "Qty", "Total"
- Set B2:B10 to formula: "=C2*D2"
```

### Sheet Formatting

#### Format Cells

```
In spreadsheet A, format range A1:E1 as bold with blue background
```

**Formatting options:**
- **Font**: Bold, italic, font size, font family
- **Colors**: Background and text colors
- **Alignment**: Horizontal and vertical
- **Number format**: Currency, percentage, date, custom

#### Add Sheet

Create a new sheet within an existing spreadsheet:

```
Add a new sheet called "Q1 Data" to spreadsheet B
```

## File Management

### Organizing Files

#### Move Files

```
Move file A to folder B
```

#### Copy Files

```
Create a copy of document A and name it "Backup - Project Plan"
```

#### Rename Files

```
Rename file C to "Final Report - 2024"
```

### File Operations

#### Delete Files

```
Delete file D
```

> [!CAUTION]
> Deleted files go to Google Drive trash. They can be restored from there within 30 days.

#### Get File Metadata

```
Show me details about file A
```

**Returns:**
- File name
- Type (MIME type)
- Size
- Created/modified dates
- Owner
- Permissions

#### Upload Files

Upload local files to Drive:

```
Upload file ./report.pdf to my Drive
```

**With folder destination:**
```
Upload ./data.csv to folder B
```

### Folder Management

#### Create Folder

```
Create a new folder called "2024 Projects"
```

#### List Folder Contents

```
Show me all files in folder A
```

#### Create Nested Folders

```
Create folder structure: Projects/2024/Q4/Reports
```

## Local Synchronization

The sync feature enables bidirectional synchronization between local files and Google Drive documents.

### Linking Files

#### Link Local to Remote

Establish a sync relationship:

```
Link local file ./docs/notes.md to Google Doc A
```

**What this does:**
- Creates a `.sync_map.json` file to track the relationship
- Stores the remote file's last known state
- Enables conflict detection

### Uploading Changes

#### Preview Changes (Safe)

```
Update Google Doc from ./docs/notes.md
```

**Dry-run output:**
```diff
--- Remote Content
+++ Local Content
@@ -5,7 +5,9 @@
 ## Budget
-Initial estimate: $50,000
+Revised estimate: $75,000
+Additional resources required
```

#### Apply Changes

```
Update Google Doc from ./docs/notes.md with dry_run=False
```

#### Force Update (Override Conflicts)

If the remote file changed:

```
Update Google Doc from ./docs/notes.md with force=True and dry_run=False
```

> [!WARNING]
> Force updates override remote changes. Use with caution.

### Downloading Changes

#### Preview Download

```
Download Google Doc A to ./docs/notes.md
```

**Shows:**
- Diff between remote and local
- What will be written to disk

#### Apply Download

```
Download Google Doc A to ./docs/notes.md with dry_run=False
```

#### Advanced Download Options

```
Download Doc A with comments, rewrite links, format as markdown, dry_run=False
```

**Options:**
- `format`: `markdown` or `html`
- `include_comments`: Extract comments as annotations
- `rewrite_links`: Convert Drive links to local paths (if linked)

### Bulk Synchronization

#### Upload Folder

Recursively upload an entire directory:

```
Upload folder ./project_docs to Drive folder B
```

**Features:**
- **Breadth-first traversal**: Handles deep directory trees
- **Automatic linking**: Links all uploaded files to local sources
- **Error resilience**: Reports errors but continues processing

#### Mirror Drive Folder

Download an entire Drive folder locally:

```
Mirror Drive folder "Project Archive" to ./archive
```

**Options:**
- `recursive`: Download subfolders (default: `true`)
- Maintains directory structure
- Auto-links downloaded files

**Example:**
```
Mirror folder A to ./local_backup with recursive=True
```

### Sync Best Practices

1. **Always preview first**: Use dry-run mode to verify changes
2. **Link before syncing**: Establish links for tracked synchronization
3. **Handle conflicts carefully**: Review diffs before forcing updates
4. **Use version control**: Keep local files in Git for additional safety

## Sharing & Permissions

### Managing Access

#### Share with User

```
Share document A with user@example.com as editor
```

**Permission levels:**
- `reader`: View only
- `commenter`: Can add comments
- `writer`: Can edit
- `owner`: Full control (transfer ownership)

#### Share with Anyone

Make a file publicly accessible:

```
Make document B viewable by anyone with the link
```

#### Share with Domain

For Google Workspace users:

```
Share spreadsheet C with my entire organization as readers
```

### Permission Management

#### List Permissions

```
Show me who has access to file A
```

**Output:**
```
Owner: you@example.com
Editor: colleague@example.com
Reader (Anyone with link): Public access
```

#### Remove Permission

```
Remove access for user@example.com from document A
```

#### Update Permission

```
Change user@example.com's access to document B from editor to reader
```

### Link Sharing

#### Get Shareable Link

```
Get the sharing link for document A
```

#### Revoke Public Access

```
Make document C private (remove public access)
```

## Advanced Features

### Comment Extraction

When downloading documents, you can extract comments:

```
Download document A with comments included
```

**Comment format in Markdown:**
```markdown
This is the document text.[^1]

[^1]: **Jane Doe**: This section needs review.
```

### Smart Link Rewriting

When syncing between Drive and local files, links are automatically rewritten:

**In Google Docs:**
```
See [Project Plan](https://docs.google.com/document/d/abc123/edit)
```

**Downloaded to local (if linked):**
```
See [Project Plan](./docs/project_plan.md)
```

**Uploaded back to Drive:**
```
See [Project Plan](https://docs.google.com/document/d/abc123/edit)
```

### Multi-Tab Documents

For Google Docs with multiple tabs:

```
Read all tabs from document A
```

**Output includes:**
- Tab names
- Content from each tab
- Proper separation and formatting

### Batch Operations

#### Process Multiple Files

```
For files A, B, and C: download as markdown to ./docs/
```

#### Bulk Permissions

```
Share all files in folder D with team@company.com as editors
```

## Best Practices

### Efficient Searching

1. **Use specific queries**: Instead of "document", use "quarterly sales document"
2. **Leverage filters**: Use advanced search for precise results
3. **Check confidence scores**: Higher scores indicate better matches
4. **Use aliases**: Reference files by alias to avoid ID confusion

### Safe Editing

1. **Always dry-run first**: Preview changes before applying
2. **Read before writing**: Review current content before updates
3. **Use version history**: Google Drive maintains automatic version history
4. **Handle conflicts**: Review diffs when sync conflicts occur

### Organization

1. **Use folders**: Organize files logically in Drive
2. **Link important files**: Maintain sync for frequently edited documents
3. **Consistent naming**: Use descriptive, searchable file names
4. **Regular syncing**: Keep local and remote in sync

### Performance

1. **Limit search results**: Use appropriate limits for faster responses
2. **Batch operations**: Upload/download folders instead of individual files
3. **Use specific ranges**: When reading sheets, specify ranges to reduce data transfer
4. **Cache results**: Aliases remain valid during your session

### Security

1. **Review permissions regularly**: Check who has access to sensitive files
2. **Use appropriate sharing levels**: Grant minimum necessary permissions
3. **Revoke unused access**: Remove permissions when no longer needed
4. **Avoid public sharing**: Use user-specific sharing when possible

## Troubleshooting

### Common Issues

#### "File not found"

**Problem**: Using an expired or invalid alias

**Solution**: Search again to refresh aliases

#### "Permission denied"

**Problem**: Trying to access a file you don't have rights to

**Solution**: Check file permissions or ask the owner for access

#### "Sync conflict detected"

**Problem**: Remote file changed since last sync

**Solution**:
1. Download latest version: `download_google_doc`
2. Review changes
3. Merge if needed
4. Upload with `force=True` if you want to override

#### "No files found"

**Problem**: Search query too specific or files don't exist

**Solution**:
- Broaden your search query
- Check spelling
- Use advanced search with filters
- Verify you have access to the files

### Getting Help

**View available tools:**
```
What Google Drive tools are available?
```

**Check tool parameters:**
```
How do I use the update_google_doc tool?
```

**Debug authentication:**
- Verify `token.json` exists
- Re-run authentication: `uv run drive-synapsis`
- Check Google Cloud Console permissions

## Example Workflows

### Workflow 1: Create and Share a Meeting Agenda

```
1. Create a new Google Doc called "Team Meeting - Dec 6"
2. Add content: "## Agenda\n- Project updates\n- Budget review\n- Q4 planning"
3. Share the document with team@company.com as editors
4. Get the sharing link
```

### Workflow 2: Analyze Spreadsheet Data

```
1. Search for "Sales Data 2024"
2. Read spreadsheet A as CSV
3. Analyze the data (AI assistant can process the CSV)
4. Create a summary document with insights
```

### Workflow 3: Sync Project Documentation

```
1. Create folder "Project Docs" in Drive
2. Link ./docs/readme.md to a Google Doc
3. Link ./docs/api.md to another Google Doc
4. Periodically: update all Google Docs from local files
5. Share folder with collaborators
```

### Workflow 4: Backup Important Files

```
1. Search for files modified in the last 7 days
2. Mirror the results to ./backups/
3. (Optional) Commit ./backups/ to Git for version control
```

### Workflow 5: Template-Based Document Creation

```
1. Search for template "Weekly Report"
2. Create new document "Weekly Report - Dec 6" from template A
3. Fill in this week's data
4. Share with manager@company.com as reader
```

## Next Steps

Now that you understand how to use the Google Drive MCP Server:

1. **Explore features**: Try different tools and combinations
2. **Create workflows**: Develop patterns that fit your work style
3. **Automate tasks**: Use the AI to handle repetitive operations
4. **Integrate with other tools**: Combine with local file operations, version control, etc.

For installation help, see the [Installation Guide](INSTALLATION.md).

For architecture and technical details, see the [README](README.md).
