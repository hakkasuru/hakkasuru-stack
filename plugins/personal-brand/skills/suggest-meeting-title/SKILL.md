---
name: suggest-meeting-title
description: Suggest YouTube-style clickbait titles for a meeting invite, from an existing calendar event's description and invitees or from a description of a new meeting. Use when the user wants a catchier, ragebait, or YouTube-style meeting title.
---

# Suggest Meeting Title

Rewrite a meeting invite title the way a YouTuber would title a video: dramatic, curiosity-baiting, a little unhinged. The joke only works if people still know what the meeting is about. Done well, invitees laugh, actually open the invite, and show up.

## The Core Tests

Every title must pass both:
- *"Would this make someone stop scrolling their calendar and click?"*
- *"Could an invitee still guess what the meeting is about?"*

If a title passes the first test and fails the second, it's just confusing. Keep the real topic, or a recognisable piece of it, in every title.

## Title Patterns

Use a different pattern for each suggestion so the user gets real variety.

### 1. The Challenge / Endurance Run
- "We Have 30 Minutes to Fix the Q4 Roadmap (IMPOSSIBLE)"
- "Surviving 60 Minutes of Sprint Planning With No Coffee"
- "Last Person to Speak in Standup Wins $0"

### 2. The Versus / Only One Survives
- "Postgres vs DynamoDB: Only One Leaves This Meeting"
- "5 Engineers. 1 Backlog. Who Wins?"
- "Design vs Engineering (FINAL SHOWDOWN)"

### 3. The Exposé / Truth Bomb
- "The TRUTH About Our Build Times (Not Clickbait)"
- "Exposing the Real Reason Onboarding Takes 3 Weeks"
- "What They Don't Tell You About the Billing Migration"

### 4. The "We Need to Talk" / Something Happened
- "We Need to Talk About the Release Process..."
- "I Can't Believe What Happened to Our Velocity 😳"
- "It's Finally Time to Address the Flaky Tests"

### 5. The Death Declaration
- "Jira Is DEAD (Sprint Retro)"
- "Is This the End of Monday Standups?"
- "RIP Legacy Auth Service (2019–2026)"

### 6. The Reaction / Ranking
- "Reacting to Our Q3 Numbers (EMOTIONAL)"
- "Ranking Every Bug in the Backlog From Worst to Worst"
- "Rating Your Side Projects: Brutally Honest"

### 7. The MrBeast Escalation
- "$1 vs $1,000,000 Infrastructure Budget"
- "I Gave the Interns Prod Access for 24 Hours"
- "Every Minute This Meeting Runs, We Delete a Microservice"

### Seasoning
Use these sparingly, one or two per title at most:
- One word in ALL CAPS, not the whole title
- A parenthetical tag: (GONE WRONG), (NOT CLICKBAIT), (EMOTIONAL), (FINAL), (MUST WATCH), (PART 2)
- A trailing ellipsis for suspense
- One emoji: 😱 😳 🔥 💀 🚨 ‼️

## Using the Invitees

The invitee list is material. Use it.
- **Head count** fuels Versus and Challenge titles: "4 PMs, 1 Roadmap".
- **Teams or roles** set up a rivalry: "Backend vs Frontend", "Sales Asked Engineering for ONE Thing".
- **Names** can headline a title if it's affectionate and the person can take a joke: "Priya Explains Kubernetes (EMOTIONAL)". Never make someone the target of a title that reads as mocking, blaming, or calling them out.
- **Leadership attending** raises the stakes in the title ("The CTO Is Watching 👀"), but tone down anything that could read as a dig at them.
- **External attendees** (customers, partners, candidates, vendors, or any address outside the user's domain): flag this to the user. Suggest milder titles, or recommend keeping the clickbait title off external invites.

## Where Not to Go

- **Sensitive meetings.** For performance reviews, PIPs, layoffs, terminations, HR or legal matters, incident reviews with customer impact, or anything about someone's health or personal life, tell the user the trend is a bad fit and offer only gently playful options, or none.
- **Fake news.** Hyperbole that is obviously a joke is fine ("$1,000,000 budget"). Claims that could be read as real are not: layoffs, reorgs, someone quitting, a project being cancelled, money lost. A title must never cause real panic.
- **Invented facts.** Don't put numbers, outcomes, or decisions in the title that aren't in the agenda or from the user, unless they are absurd enough to be obvious jokes.
- **Anything you wouldn't say in front of the whole company.** No sexual innuendo (skip "GONE SEXUAL"), slurs, or punching down.
- **Length.** Calendar views truncate titles. Put the hook in the first ~40 characters and keep the whole title under ~70.

## Instructions

### Existing meeting

1. Find the event. If a calendar tool is available (for example a Google Calendar MCP server's `search_events`, `list_events`, and `get_event` tools), search by the title, date, or keywords the user gave. If several events match, list them with date and time and ask which one. If no calendar tool is available or authenticated, ask the user to paste the current title, description or agenda, and the invitee list.
2. Read the current title, the description or agenda, any attached doc titles, the invitee list, the duration, and whether it recurs.
3. Decide whether you know what the meeting is about. The description, agenda, attached docs, or an informative current title can tell you. If none of them do (a title like "Sync" or "Catch up", with no description), ask the user what the meeting is about before suggesting anything. Don't guess.
4. Suggest titles (see Output).
5. Do not rename the event unless the user picks a title and asks you to. Before updating, remind them that renaming may notify every invitee, and on a recurring event ask whether to change this occurrence or the whole series.

### New meeting

1. Ask what the meeting is about. Also ask who's invited (rough roles or teams are enough), since the invitees make better titles. If the user has already told you either, don't ask again.
2. Suggest titles (see Output).
3. If the user wants the invite created and a calendar tool is available, ask for anything still missing (time, duration, invitees) and create it with the chosen title only after they confirm.

### Output

Give at least 3 titles, each from a different pattern. For each:
- The title on its own line
- The pattern used, and in one short line what it hooks on (the invitees, the agenda item, the stakes)

After the list, keep the real meeting findable. If you replaced the original title entirely, suggest putting the plain-language topic in the first line of the description, e.g. "Actual agenda: Q4 roadmap prioritisation". If you flagged external attendees or a sensitive topic, say so above the list.
