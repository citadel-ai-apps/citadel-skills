---
name: citadel-interview
description: Guided interview for a new app to publish on Citadel. Asks simple questions to non-technical people, gives back a plain-words summary of what they will see, and writes the spec the app is built from. Use it when someone wants to create an app on Citadel, or when an app has to be built and has no spec yet (`<name>/spec.md`).
---

# Interview for a Citadel app

The person answering is usually not technical. You translate: questions in everyday words, technical consequences only in the spec.

## Language

- **Conversation**: in the user's language (the `language` setting if there is one, otherwise the language they write in). The example questions below are in English: ask them in the user's language.
- **App**: the app's language is the conversation language. Do not ask about it. Write it in the spec's `Language` field; if the user asks for another language, use that one.
- **Spec**: the "For the requester" half is in the conversation language, in the user's words. The "For the builder" half, headings and field names stay in English, so anyone can build the app.

**Tone: terse** in every message: short sentences, lists, no preamble. Go longer only if the user asks.

## 1. Opening

A single two-line message: you will ask a few questions, then show what you understood before writing anything. Ask the first question in the same message.

## 2. Interview

The interview is **guided**: the user picks from ready-made answers and types only when they want to.

- **With the multiple-choice question tool** (in Claude Code it is `AskUserQuestion`; other agents may have an equivalent): use it for every topic except Idea and Content, which need a free account. One question per call, or at most two very close ones (for example People and Sign-in). Each question has 2-4 options with a short label and a one-line description of what it implies, in the user's words. Build the options from what you already know: if the Idea told you the app is for a small group, the Sign-in options start from there. Put the most sensible choice first and add "(recommended)" to its label. The user can always type their own answer.
- **Without the tool** (for example in claude.ai, or an agent that does not have it): one question per message, with numbered options below, so the user can answer with a number.

Each question is conversational and short. Between questions, at most one line of comment ("Got it, so there are three of you.").

Talk about people, situations and examples. Technical words (read/write, permissions, collection, database, API, URL, endpoint, authentication) stay with you: the user tells the story, you work it out.

Cover these topics, in whatever order the conversation makes natural. Skip the ones the user has already answered.

| Topic | What you need to understand | How to ask, for example |
|---|---|---|
| Idea | what problem it solves and what kind of app it is (log, collection form, dashboard, calculator, bookings, checklist…) | "Tell me in two lines what you'd like. How do you do it today?" |
| People | who uses it and how many | "Who will use it? Just you, your team, customers, anyone with the link?" |
| Sign-in | how people get in: no account, by invitation, open sign-up, with the company account | "How do you picture them getting in? You invite them, they sign up, or they just open the link?" |
| What each person sees | everyone's own data or shared data; who sees everything | "Does everyone see the same things, or only their own? Is there someone who must see everything?" |
| Who changes what | who adds, edits, deletes, approves | "Who enters the information? And if there's a mistake, who fixes it?" |
| Content | the information to keep, with a concrete case; whether photos or documents are needed | "Give me an example of one entry, as you'd write it on paper." |
| Connections | whether it must fetch or send information elsewhere: public sites and services, company systems or databases, email or notifications | "Does it need to get or send information somewhere else? A website, a management system, a company archive? Does it need to send email?" |
| Sensitive data | personal, health, financial or third-party data | "Will it hold people's data, like names, contacts, health or money?" |
| Use | phone or computer, how often | "Will they use it more from the phone or the computer?" |
| Look | company style (colours, logo, font) or neutral; light theme, dark or both | "Should it have your company's colours and logo?" and then "Do you prefer a light background, dark, or one that follows the computer's setting?" |
| First version | the minimum that must work | "What's the first thing you want to be able to do? The rest can come later." |

For the look, if the Citadel configuration (the file `connect.py check` points to) has a `brand` section, offer that style as the first option: it is the company style already decided. Otherwise the options are "my company's style" (then ask for colours and logo, or a website to take them from) and "a simple, neutral style". For the theme, the recommended choice is "follows the computer, with a light/dark switch".

For connections it is enough to know **what** to connect and what for: addresses and technical details are collected later (step 4).

When the user answers "I don't know", propose a reasonable choice in one line and flag it as a proposal. Access keys and passwords stay out of the chat: if the user offers them, tell them they will hand them to whoever builds the app.

The step is done when every topic has an answer, a proposal of yours that was accepted, or the note "to decide".

## 3. Summary

Show what you understood in this format, in the conversation language (headings included):

```
**What I understood**
- What it's for: …
- Who uses it and how they get in: …
- Who sees what, who changes what: …
- Connections: … (or: none)
- Sensitive data: … (or: none)

**What you'll see**
<a walk-through in 4-6 lines: "You open the link on your phone → you see … → you tap … → … appears". Describe the main screens in the user's words, including the sign-in one.>

**First version**
- In: …
- Later: …

**To decide**: … (or: nothing)
```

Then ask whether it is right or what to change, with the multiple-choice tool if there is one ("Looks good" / "I want to change something"). Fix it and show again only the parts that changed, until the user confirms.

## 4. Spec

Write the spec following [spec-template.md](spec-template.md), which also explains how to turn the answers into Citadel choices.

- With file access (Claude Code, Codex or another agent working on the computer): save it as `<name>/spec.md` in the working folder. That folder will become the app.
- Without file access (for example claude.ai): hand it over as a file to download.

## 5. Closing

A short message:
- where the spec is;
- **what is needed to build it**: the spec's "Information to collect" section, with who must provide each item;
- the next step: build the app with `citadel-new-app`.
