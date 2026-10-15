# Campus Customs Desk: dashboard design

The desk is a React + Vite + TypeScript app in `frontend/`. Start it with `npm run dev` (it opens http://localhost:5173). It talks only to the FastAPI backend at http://localhost:8000, which allows the Vite origin through CORS.

**Design goal:** a person should be able to *watch* five AI agents work a ticket, *understand* who did what, and *sign* for money with confidence. The board should also be a little delightful, so that working the desk feels like being part of a Yale team rather than reading a log file.

---

## Layout: pick → watch → sign, left to right

| Column | What lives there | Why |
|---|---|---|
| **Masthead** (Yale Blue band) | Handsome Dan, the shop day (`desk.date_today`), API status, the *Signing as* name box, **Fresh start** (reset) | Facts that frame everything: whose desk this is, what "today" means for the shop, and who is signing. |
| **Left: Today's tickets** | The three tickets as pennant-edged cards, each with a status badge, requester, item, and the boss's latest note. The selected card shows **Send in the team**. | You start on the left by choosing work. One button on one card makes it obvious which ticket the team will run. |
| **Center: the team** | The roster of five agents with live status lines, the hand-off chain, and two tabs: **Live desk** (the feed) and **Who did what** (the summary). | The agents are the show, so they get the widest column. Tabs keep the play-by-play and the recap in the same place. |
| **Right: money and paper** | **Bulldog Bank** (checking balance), **Signature desk** (approvals), **Drafts on the board** | Money and outgoing messages are what a human must act on, so they never scroll off with the feed. |

Below 1,180 px the right column moves under the other two; below 1,000 px everything stacks, with tickets side by side. Tested at 1,280 px and 768 px with no horizontal overflow.

---

## How the agents read differently

Each agent is a **persona with its own Yale-inspired emblem and color**, used everywhere that agent appears: roster, feed bubbles, summary cards, approval slips, drafts.

| Agent | Persona | Emblem (original drawing) | Why this symbol |
|---|---|---|---|
| Boss | **Handsome Dan** | The Yale bulldog mascot, wearing a white collar with a "Y" tag | The top dog makes the final call. He is also the app icon, the empty state, and the voice of good news. |
| Inventory | **Sterling** | Gothic library arch with shelves of folded merch | A nod to Sterling Memorial Library: the agent who knows exactly where everything is shelved. |
| Accounting | **Lux et Ledger** | A shield holding an open ledger, with a gold coin | A pun on *Lux et Veritas*: the open book of Yale's arms becomes an account book. |
| Facilities | **Harkness** | Harkness Tower silhouette with its clock | The campus's best-known building stands in for the shop's building: the lease and rent. |
| Customer service | **Boola** | A "Y" pennant and a speech bubble | From the fight song *Boola Boola*: the cheerful voice that writes to customers. |
| You | **Approver** | A pen and a signature line, in gold | Gold is reserved for humans and money. If something is gold, it needs you. |

**In the roster,** each agent shows a status line that updates as events arrive: *Reading the brief → Using check_stock → Waiting on Lux et Ledger → Done ✓*. The agent working right now lifts up and gets a pulsing ring, and agents the boss didn't call fade to grey. That makes Problem 6's point visible: **the boss doesn't call everyone**.

**In the feed,** every step is a bubble tinted with the agent's color, and each kind of step has its own look:

- a dotted bubble for *picked up the brief*,
- code chips for tool calls with their arguments, e.g. `check_stock(CC-TEE-WHITE, S, 1)`,
- a dashed bubble for a **hand-off** (with the receiver's emblem) and a white one when the report comes back,
- an amber bubble when a guardrail blocks a hand-off,
- a bordered, serif **"The boss's call"** bubble for the final decision,
- a gold bubble when a human signs.

Bubbles are **indented by hand-off depth**, so boss → inventory → accounting reads like a nested conversation, and a **hand-off chain** breadcrumb under the roster shows who is waiting on whom.

**"Who did what"** turns the run into report cards: the boss's call (decision, what is waiting on you, next steps), then one card per agent with the tools it used (`check_margin ×2`), who it asked for help, what it filed (approval #, draft #), its recommendation, and anything blocking it. The run's cost is in the footer line: model calls, tool calls, tokens, hand-offs, seconds. A gold **"After the run · signed by a human"** card shows the signatures that followed, so a ticket's whole story (agents, then you) reads in one place. When a ticket has been run more than once, a small **run picker** (1 ✗ · 2 ✓ · 3 ✓) switches between runs, so retries are visible rather than hidden.

---

## How resolved tickets show up

Ticket cards move through a clear set of states, each with its own color on the pennant edge and badge:

| State | Look | Meaning |
|---|---|---|
| Open | Blue badge | Nobody has worked it yet. |
| **Team at work** | Navy badge, a trotting **paw-print trail**, live dot on the feed tab | A run is in progress; one run at a time. |
| **Needs your signature** | **Gold** edge and badge, "✍ 1 to sign · $840.00" | The team finished and parked the ticket on a human approval. |
| **Resolved** | Green edge, **rubber stamp** "RESOLVED · Campus Customs · date" that thumps onto the card | Nothing is left to do. |
| Declined / In progress | Grey / stone | The boss said no / the team must re-plan (e.g. a human sent a payment back). |

A ticket becomes **Resolved** when its run finishes and the boss's final call is *resolved*. If the boss's call needs money, the ticket shows *Needs your signature* until you sign; the moment the last slip is signed, the backend marks it resolved and the stamp lands. A finished run always ends with a toast and the boss's decision, and the center panel switches to **Who did what**. We chose this over stamping "Resolved" while money was still waiting, so the board never says "done" when the shop is really waiting on you.

---

## How cash shows up

- **Bulldog Bank** is a dark navy **scoreboard** (think Yale Bowl) with the checking balance in big serif numerals. After you sign, the number **counts down** to the new balance and a red **−$840.00** floats off it, so the drop is unmistakable.
- A bar under the number splits the balance into **free** cash (blue) and cash **waiting for signatures** (gold stripes), so you can see how much the pending slips will use before you sign anything.
- Recent payments list the amount, what it paid, and **who signed**.
- The **Signature desk** shows each prepared payment as a cream **permission slip** with a perforated top edge: what it pays, the amount, the agent who prepared it and why, and the balance after signing. **Sign & pay** stays disabled until you type your name, and it opens a confirmation showing *$3,400.00 → $2,560.00* before any money moves. **Send back** asks for a reason, moves nothing, and returns the ticket to the team.

---

## Creative choices that make it enjoyable

- **A cast, not a log.** Nicknames and emblems turn an event stream into characters you can follow. "Sterling is waiting on Lux et Ledger" is easier to follow than `delegation_start`.
- **Handsome Dan naps** (gently breathing, with floating *z z z*) when nothing has run, and wakes up when you press **Send in the team**.
- **Paw prints** trot across a ticket while the team works it.
- **Y-fetti.** When a ticket resolves, a short burst of blue serif *Y*s falls across the screen, and Handsome Dan announces "**Boola boola!** Ticket #101 is resolved."
- **Paper you can trust.** Rubber stamps for resolved tickets, permission slips for money, and draft cards stamped **DRAFT · NOT SENT** make the human's role physical and obvious.
- **Copy in the shop's voice.** The text is short and warm ("Nothing to sign. When an agent prepares a payment…"), but numbers and ids are always shown in full, so the playfulness never hides a fact.

---

## Trust, safety, and accessibility

- **Only a person moves money:** a name is required, a confirmation shows before → after, and the approve route is the only place cash changes. Drafts are always labeled unsent. **Fresh start** asks first and explains that the audit trail is kept.
- If the API is down, a banner explains exactly how to start it.
- Keyboard focus outlines, `aria-live` regions for the feed and balance, labeled emblems, color always paired with text, and every animation is turned off when the system asks for reduced motion. There is no sound.

**About the emblems:** they are original SVG drawings inspired by Yale symbols (the bulldog, Sterling, Harkness, the open book, the pennant), not official Yale logos or trademarks. Campus Customs is a class setting, not a partnership.
