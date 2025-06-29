# Cursor IDE Configuration and Chat History

This directory contains Cursor IDE configuration and chat history data for the Mingus Application project.

## Contents

- `workspace-data/` - Symbolic link to workspace-specific Cursor data including:
  - `anysphere.cursor-retrieval/` - AI retrieval data and embeddings
  - `state.vscdb` - Workspace state database
  - `workspace.json` - Workspace configuration

- `global-storage/` - Symbolic link to global Cursor storage including:
  - `state.vscdb` - Global state database (contains chat history)
  - `storage.json` - Global storage configuration
  - `ms-toolsai.jupyter/` - Jupyter extension data

## Chat History

The chat history is stored in the global `state.vscdb` file within the `global-storage` directory. This database contains all conversations and AI interactions for this project.

## Note

These are symbolic links to the actual Cursor data directories. The actual data is stored in:
- `~/Library/Application Support/Cursor/User/workspaceStorage/`
- `~/Library/Application Support/Cursor/User/globalStorage/`

## Git Tracking

This directory is tracked in git to preserve:
- AI conversation history
- Workspace-specific AI embeddings and retrieval data
- Project-specific Cursor configuration

## Backup

The actual Cursor data is automatically backed up by Cursor itself, but this git tracking provides an additional layer of version control for project-specific AI interactions. 