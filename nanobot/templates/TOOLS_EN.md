# Tools & Skills Guide

This document provides in-depth context, constraints, and best practices for the agent to use available tools effectively.

## 1. Core Tools

### 1.1 shell (exec) —— System Interaction
- **Security**: Dangerous commands are intercepted.
- **Safety Redline**: Do NOT execute `rm -rf *` or clear critical databases/session directories unless the user explicitly uses extremely strong language such as "complete factory reset, delete all history, no retention". **By default, no 'cleanup/optimization' request should lead to the loss of core facts.**
- **Self-Reflection (Skill Mining)**: If you successfully execute a complex command, proactively suggest encapsulating it as a skill: "I notice this operation is frequently used; would you like me to encapsulate it as a skill?"

### 1.2 web (search/fetch) —— Networking
- **web_search**: Get the latest information.
- **web_fetch**: Fetch the full content of a web page and convert it to Markdown.

### 1.3 mcp —— Model Context Protocol (Lazy Loading)
- **python**: **Persistent Python REPL**. It maintains variables and functions across the entire conversation cycle. Use this for complex data modeling or calculations requiring consistency.
- **sqlite**: **Structured Persistence**. Connected to `main.db`. Use SQL tables for data that needs long-term tracking (e.g., TODO lists, historical records, project progress) instead of plain text files.
- **obsidian/notion**: For cross-platform knowledge synchronization and retrieval.

### 1.4 memory —— Memory System
- **Memory Pruning**: Use `self.context.memory.prune()`.
- **Pruning Logic**: The core of auditing is **resolving contradictions, deduplication, and categorization**. NEVER delete personal preferences or core project information unless they are strictly outdated or replaced by new facts.
- **Differentiation**: `MEMORY.md` for facts, `HISTORY.md` for logs, `sqlite` for structured data.

### 1.5 spawn —— Sub-Agents
- Used for parallel tasks or time-consuming background tasks that should not block the main process.

## 2. Core Skills (Skills)
- **skill-creator**: The core for encapsulating new skills.
- **cron**: Automation maintenance and reminders.
- **summarize**, **vision**, **tester**, **weather**, **github** (see the skills directory for details).

## 3. Best Practices
1. **Persistence Thinking**: Prioritize using the `python` (REPL) MCP over a single `exec` for complex calculation logic.
2. **Structured Thinking**: Prioritize using `sqlite` over text files for large-scale data storage.
3. **Closed-Loop Thinking**: Proactively suggest encapsulating complex, successful operations as a Skill.
4. **Clean Memory**: Regularly audit memory to ensure `MEMORY.md` is concise and free of contradictions.
