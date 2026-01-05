# cc-plugins

Claude Code plugins by kateleext.

## Installation

```bash
# Add the marketplace (one time)
/plugin marketplace add kateleext/cc-plugins

# Install plugins
/plugin install deja@kateleext
```

---

## Plugins

### deja

Episodic memory for Claude Code. Search and recall past conversations.

**Includes:**
- `memory` skill - search and retrieve past conversations
- `memory-briefer` agent - deep exploration and synthesis across sessions

**Commands:**
```bash
deja                        # Recent sessions
deja "query"                # Search
deja <session>              # Session overview
deja <session>:2            # Read episode 2
deja <session>@3            # Read around turn 3
deja <session> +note "..."  # Add a note
```

**Permissions** - add to `.claude/settings.json`:
```json
{
  "permissions": {
    "allow": ["Bash(deja *)"]
  }
}
```

**Todo Support:**
- Indexes both `todowrite` tool calls and OpenCode interface todos
- Search for todo content: `deja "fix bug"`, `deja "add feature"`
- Sessions with todos get higher search ranking and show todo summaries

---

## Adding More Plugins

Future plugins will be added here. Once you've added the marketplace, just install new ones:
```bash
/plugin install new-plugin@kateleext
```
