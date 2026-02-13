# TensorMarketData Discord Server Setup & Moderation Guide

## Server Structure

### Category: Welcome
- **#welcome** - Server intro, rules, getting started
- **#announcements** - Official news, product updates, launches (announcements-only)

### Category: Community
- **#general** - General chat for all community members
- **#introductions** - New members introduce themselves
- **#showcase** - Share your projects, integrations, use cases
- **#off-topic** - Non-work banter, memes, fun

### Category: Product & Support
- **#product-updates** - Changelog, new features, roadmap
- **#documentation** - Links to docs, tutorials, guides
- **#api-help** - Technical questions, integration support
- **#bug-reports** - Report issues, request features
- **#feedback** - Suggestions, ideas, improvement requests

### Category: Developer Hub
- **#integration-examples** - Code snippets, tutorials
- **#data-marketplace** - Discuss datasets, APIs, data sources
- **#ai-agents** - Agent development, LangChain, AutoGPT discussions
- **#sdk-discussion** - Python SDK, REST API, client libraries

### Category: Events
- **#office-hours** - Weekly Q&A with the team
- **#ama-archives** - Past AMA transcripts
- **#hackathons** - Events, challenges, prizes

### Category: Partners (Tiered Roles)
- **#partners-general** - Partner discussions
- **#partner-showcase** - Featured partner projects

---

## Role Structure

| Role | Permissions | Purpose |
|------|-------------|---------|
| @Founder | Admin | Founding team |
| @Admin | Admin | Server administrators |
| @Moderator | Moderate, Manage Roles | Community moderators |
| @Community Manager | Moderate | Lead community management |
| @Developer | Send Messages | Core developers |
| @Contributor | Send Messages | Community contributors |
| @Partner | Send Messages | Official partners |
| @Member | Send Messages | Verified community members |
| @Newcomer | Read-only | Fresh accounts (<24h) |

---

## Moderation Workflow

### Step 1: Warning System
1. **First offense**: Gentle reminder in channel or DM
2. **Second offense**: Formal warning with rule reference
3. **Third offense**: 24-hour timeout
4. **Fourth offense**: 7-day timeout or ban

### Step 2: Escalation Protocol
- **Spam/Self-promotion**: Remove message → Warn → Timeout if repeat
- **Harassment**: Immediate timeout → Investigate → Permanent ban if confirmed
- **Malicious links**: Remove immediately → Check for harm → Ban if malicious
- **Off-topic spam**: Remove → Redirect to #off-topic

### Step 3: Moderation Tools
- **Thread creation**: For long discussions
- **Slow mode**: Set for high-traffic channels
- **Pins**: Important announcements, resources
- **Polls**: Community feedback, decisions

---

## Auto-Moderation Rules

```
Rule 1: Anti-Spam
- Max 5 messages/10 seconds
- Max 1 invite link per hour
- Block discord.gg links from non-partners

Rule 2: Anti-Profanity
- Filter common curse words
- Allow medical/technical terms

Rule 3: New Account Filter
- <24h accounts: read-only until manual review
- Block: alt accounts for ban evasion

Rule 4: Large Attachments
- Block .exe, .scr, .bat files
- Max 10MB per attachment
```

---

## Moderator Onboarding Checklist

- [ ] Read all channel purposes and pins
- [ ] Review server rules and guidelines
- [ ] Set up 2FA for Discord account
- [ ] Complete moderator training (30 min)
- [ ] Shadow senior moderator for 1 week
- [ ] Practice with mod tools in test channel
- [ ] Add moderator role

---

## Weekly Moderation Tasks

1. **Daily**: Check #introductions, welcome new members
2. **Monday**: Review mod queue, pending bug reports
3. **Wednesday**: Office hours prep, Q&A review
4. **Friday**: Weekly summary, highlight top discussions
5. **Monthly**: Server stats report, role cleanup

---

## Community Engagement Best Practices

### For Moderators:
- Be present but not overbearing
- Lead by example (friendly, helpful)
- Celebrate community wins publicly
- Redirect rather than punish when possible
- Keep transparency in decisions

### Response Templates:

**New Member Welcome:**
```
Welcome to TensorMarketData, {name}! 🎉
We're thrilled to have you here. Check out #welcome to get started, and feel free to introduce yourself in #introductions!

Questions? Just ask — we're here to help.
```

**Helpful Response:**
```
Great question, {name}! Here's what you need to know:

{answer}

Let me know if you'd like more details or have follow-up questions!
```

**Conflict De-escalation:**
```
Hey everyone, let's keep this constructive. Different perspectives are valuable here, but let's focus on the ideas, not the people.

{topic} is an important discussion — let's keep it respectful and helpful.
```

---

## Server Analytics to Track

- Member growth rate
- Active users (DAU/MAU)
- Message volume by channel
- Response time in #support
- Sentiment trends
- Top contributors

---

## Emergency Protocols

### Server Attack/Spam Wave:
1. Enable Server Lockdown (all channels read-only)
2. Activate anti-spam filters at max
3. Mass ban spammers (review logs first)
4. Announce in #announcements
5. Gradually lift lockdown

### Troll/Harassment Situation:
1. Screenshot evidence
2. Remove offending messages
3. Timeout or ban the user
4. Check for brigading
5. Post statement if public response needed

---

*Last Updated: February 2025*
