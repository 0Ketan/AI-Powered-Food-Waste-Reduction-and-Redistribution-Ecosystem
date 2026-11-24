# AnnaSetu AI: Agent Conventions

This file documents how team members should define and use agents (anthropic.com/claude/subagents) for multi-step complex work.

## When to Use Agents

Use a subagent when:
- You need independent parallel work
- The task is complex and multi-step
- You're delegating across code modules owned by different people
- You need to read multiple files to verify or fix something
- You want to offload code review

When NOT to use: clone or replace an agent (too error-prone).

## Agent Types

- **`fork`**: Runs your session context (inherits git state, open prs, etc.) in the background
- **`general-purpose`** (default): Fresh agent with this conversation's context

## Instructions for Fork Agents

Give the fork the **same context** as you would a new agent, because it lacks session memory. Brief it by:
- Stating the goal clearly
- What you've already ruled out
- Pointing at the exact files/docs worth reading instead of retyping
- Keeping scope explicit and narrow

## Detail vs Speed Trade-off

An agent pays per token, so ask for the right effort level:
- **`low`**: Quick spot checks
- **`medium`**: Standard full review (default, good balance)
- **`high`**: Thorough review with checkpoints
- **`xhigh`**: Maximum verification (use only if explicitly requested)
- **`max`**: Detailed, expensive, use sparingly

## Available Agents

Ask me (`Claude Code`) to list available agent types in a session:
```
/listagents
```

## Using Agents

```
/conversation
# Check available agents
```

Then call `Agent` with a helpful description (3-5 words) and a detailed prompt.

## Important Notes for AnnaSetu

When using agents across module boundaries:
- Give them a **snapshot** of relevant contract files (contracts/API.md, contracts/FLOWS.md)
- Specify which repository paths they should (or shouldn't) edit
- Ask them to report findings, not decision-making
- Before trusting their output, verify against your own knowledge of the code
- If a reported finding contradicts your reading, re-read the target files yourself
- If a fork agent needs to look at the same things you're looking at, run it yourself instead
