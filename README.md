# Deja

Episodic memory for Claude Code. Search and recall past conversations.

## Installation

```bash
/plugin marketplace add kateleext/deja-plugin
```

## What's Included

### Skill: memory

The `memory` skill gives Claude the ability to search and retrieve past conversations. Claude uses this automatically when context from previous sessions is needed.

**Commands:**
```bash
deja                        # Recent sessions
deja "query"                # Search
deja <session>              # Session overview
deja <session>:2            # Read episode 2
deja <session>@3            # Read around turn 3
deja <session> +note "..."  # Add a note
```

### Agent: memory-briefer

A specialized subagent for deep exploration of conversation history. Use when:
- The topic is exploratory and you're not sure what to search for
- Context spans multiple sessions
- Full narrative is needed before making decisions

The briefer explores multiple search paths, reads across sessions, and synthesizes a comprehensive narrative with turn pointers for verification.

## Permissions

For smooth operation, add to your `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Bash(deja *)"]
  }
}
```

## Requirements

- Claude Code CLI
- Conversation history retention enabled in Claude settings

## How It Works

Deja indexes your Claude Code conversation history, extracting:
- Todos and their completion status
- Files touched and commands run
- Episode boundaries (natural conversation segments)
- Full-text search with stemming

The index updates automatically. Searches score by relevance (todos > files > text) with recency boost.
