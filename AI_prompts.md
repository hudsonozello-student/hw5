# AI Prompts Log — Homework 5: Campus Customs Multi-Agent Operations

MGT 409 AI Foundations. This file logs the exact prompts I typed into my vibe coder (Claude Code) for this homework, organized by problem. Each prompt is copied verbatim. Follow-up prompts are listed under the problem they belong to, in the order I sent them, and each one includes at least one sentence explaining what the earlier attempt was missing.

---

## Problem 1: Vibe Coder Prompts

### Prompt 1

```text
MGT 409 HW5: Campus Customs Multi-Agent Operations

Background on this HW:

we are building 3 pieces that will talk to each other: MCP server; FastAPI backend with multi-agent team, and React dashboard s human can watch agents at work and approve requests. this is for a 'campus customs multi-agent operations', an agentic team that runs the campus customs shop at yale som.

agent team will have full connectivity, meaning any agent will have ability to delegate tasks to any other agent to help. throughout this assignment we will build th following 5 agents:

boss: it wll read each ticket and decide whom should work on the ticket, and make final calls
inventory: it will check tock by SKU and size, spot shortfalls, and figure out which vendors can restock
accounting: it will watch cash and invoices, check margins, and prepare payments or POs (purchase orders) for human approval
facilities: this will handle the shop space side (leases, rent, etc.)
customer service: this will drft messages for customers

We are using data from the 'data' folder in C:\Users\hudso\Documents\NOT_ONE_DRIVE\Grad School\Yale\Fall 2026\MGT 409 AI Foundations\Homework\Homework 5

the tools here will update the database as tickets are resolved. 

please make a copy of the db file named 'data/campus_customs_new.db and direct the MCP server and backend at that working copy. keep campus_customs.db (the original) untouched so that I can reset when I want to restart resolving the tickets 

Please note the following rules for thisshop:

* the field desk.date_today is 'today' for the shop. use this data field to determine what is overdue
* vendor lead times will come fro the vendors table
* a vendro cannot ship new product if they still ave an open unpaid invoice
* human approval is requirement for any payments. points WILL be deducted if this is not setup. if a payment is made, please make sure to update relevant table.
* we cannot go to negative balances - if there is not enough cash, the payment tool must refuse.
* we are not modeling revenue, so no money is coming in; cash is only going out in this assignment
* absolutely do NOT email customers or call real vendors. drafts stay on the board only.


Use my PORTKEY_API_KEY for AI calls. for this assignment, use ONLY gpt-6-luna through Portkey for every agent. make sure this is the only model used across all agents.

I will give you one step at a time for a total of 11 problems.

Problem 1: Vibe Coder Prompts

Please create AI_prompts.md and keep it updated as we work. this file is a log of exactly what is typed into the vibe coder. I will explain everything to you in my own words and you need to capture here. Please create one section for each problem, with each section including: 
(1) the problem number and title
(2) the exact prompt that I send
(3) all subsequent prompts for that problem. if I need more than one prompt, then I will add at least one sentence explaining what was lacking in the first attempt
```

---

## Problem 2: Study the Campus Customs Database

### Prompt 1

```text
Problem 2: Study the Campus Customs Database

Please open up the data/campus_customs.db and search through every table and the fields. copy the oroginal file to data/campus_customs_new.db. later problems will uppdate that working cupy. please study the 3 open tickets to see how they link to other tables

please start output/harness.md. for each table, list the fields and one short line on why that table matters for the agents.

note that we will keep growing this harness file in later problems.
```

---

## Problem 3: Build the MCP Server

### Prompt 1

```text
Problem 3: Build the MCP Server

OOh were getting into the fun part. please write an MCP server in mcp_server/ using FastMCP. This will talk to data/campus_customs_new.db. note that you do NOT need to connect or run it in this problem. 

Every agent in this HW uses the tools in this MCP server!! we will add more tools to it later. for this moment, please write THREE tools you know you will need for the tickets in the db. please keep the names clear. NEVER ever invent any data. only use the info in the database. this is important so i dont lose points.

in output/harness.md, please list each of your 3 MCP tools. for every tool please include: which table it reads, whcih ticket it helps unlock (101, 102, or 103) and ONE SENTENCE on why that tool is the rihght tool for that ticket. Please tie the tool to the ticket and be specific - something vague like 'reads inventory' will receive a low score and make me sad.

Please also add a brief mcp_server/README.md file to explain what the MCP server is for, which db file it uses, and the 3 tools it has.
```

---

## Problem 4: add the MCP server to vibe coder and test each tool

### Prompt 1

The first paragraph answers the vibe coder's earlier question about which model name to use (`gpt-6-luna` vs. `gpt-5.6-luna`).

```text
my instructions given were exactly "Use your PORTKEY_API_KEY for AI calls. For this assignment, use ONLY gpt-6-luna through Portkey for every agent. Multi-agent chats burn tokens fast. Points will be deducted if any other model shows up in your code or runs". does that answer your question?

Problem 4: add the MCP server to vibe coder and test each tool

in the vibe coder (here), please add the MCP server to this project so the vibe coder can call the tools. please save the connection JSON text in .mcp.json at the project root (or however the vibe coder saves local MCP server lists). >>please note this paragraph is instruction from the HW, and Im not sure what it means but im hoping you understand, please let me know if issues or questions.

with the vibe coder connection complete, please teach each of the 3 MCP tools. save the evidence of testing in output/mcp_smoke.json

For every tool please include:

the prompt asked to the vibe coder
the tool name
the tool output (this must match values in data/campus_customs_new.db)

for this problem, please let me know if I (the human) need to ask any follow up prompts/steps or if you are able to handle all on your own- thanks
```

### Prompt 2

The first prompt could not be finished in one go because the vibe coder only loads MCP servers when a session starts, so I restarted the Claude app and sent this using the app's suggested-reply button.

```text
I restarted the Claude app and came back to this session. Please check whether the campus-customs MCP tools are connected.
```

### Prompt 3

The restart did not connect the tools, because the app reattached to the same running session, so I asked whether moving to a new session would keep my setup and prompt log intact.

```text
I need to make sure that I maintain the appropriate setup and audit prompt logs, if I start a new session will those continue forward? 

I want to resolve this in whatever way takes the least effort and risk of messing up config on my end.
```

### Prompt 4

I approved moving the tests to a new (forked) session using the app's suggested-reply button. The vibe coder had already started that session before I clicked, so this approval came after the fact.

```text
Yes, start the forked Problem 4 smoke test session.
```

### Prompt 5

Sent in the new session. Switching sessions left me unsure where Problem 4 stood, so I asked for a short status summary and a check on the Problem 1 setup.

```text
Hi - i  am confused. Can you please explain what the problem was, where we are on problem 4, what is remaining, and if there are any current/outstanding issues. additionally, is the config/setup from prob 1 (includng audit log) still good?

Please explain as concisely as possible, I dont want to read paragraphs and paragraphs.
```

### Prompt 6

I didn't know how to word the tool tests, so I asked the vibe coder to suggest them.

```text
please suggest the exact wording for the 3 test prompts
```

### Prompt 7

This is the first of the three tool tests, using the wording the vibe coder suggested.

```text
Problem 4 test 1: use the campus-customs check_stock tool to check CC-TEE-WHITE in size S, qty needed 1, for ticket 101.
```

### Prompt 8

This is the second of the three tool tests.

```text
Problem 4 test 2: use the campus-customs get_lease tool to look up lease 1 for ticket 102.
```

### Prompt 9

This is the third and final tool test.

```text
Problem 4 test 3: use the campus-customs check_margin tool for 20 CC-HOOD-NAVY at 15% off for ticket 103.
```

---

## Problem 5: Build the agent team and grow the MCP tools

### Prompt 1

```text
Problem 5: Build the agent team and grow the MCP tools. 
now, we will build the agentic team for Campus Customs using PydanticAI: Boss, Inventory, Accounting, Facilities, and Customer Service. Please include prompts, models, and agent loops so they can delegate work to each other with full connectivity. 
Please put the agent prompts in backend/prompts/ with ONE FILE PER AGENT. please put data types in backend/models.py, and the agent files under backend/ (note that your layout can vary as long as the 5 roles are clear). use the PORTKEY_API_KEY and only gpt-6-luna for every agent (as already discussed). 
Please write each prompt in your own words using the shop rules needed for that specific agent. note that more detailed prompts that cover all aspects of a given agents work and scope will score higher than short and generic prompts. I want a high score! so please comply.
please now add any tool that is needed by the agents to the MCP server so that they agents can work on the open tickets. Note that shop facts come from the MCP server over data/campus_customs_new.db. do NOT invent a second shop-tools layer that bypasses MCP. 

Please write the agents so they apend to output/audit_trail.json as they run. for each agent-loop step record enough to audit later. append to this file and do not wipe it after each run. 

then, in output/harness.md, list each agent and each MCP tool (including ones that are added in this problem) along with wich table the tool uses. also please add a short SAFETY section -the guardrails a real business would want to have when agents touch real customers and real money, plus limits that keep token use in check. 

Please update mcp_server/README.md so the tool list matches what we now have
```

---

## Problem 6: plan the three tickets

### Prompt 1

```text
problem 6: plan the three tickets

Before we wire the backend, please write down what we expect the team to do on each open ticket. please build output/desk_tickets.html, which is a page where I can double-click with one tab per ticket (101, 102, 103). please also add empty Cash and Reflection tabs for later problems (leave them blank or with a short 'coming later' note for the time being) 

on each ticket tab, please fill an expected section only (leave room for an Actual section that will fill after running the agents). 

For each ticket's expected section, I will need to write in my own words: 

1. who the boss should call first and why
2. all the agent delegrations I expect (not boss calls everyone)
3. which MCP tools yu expect that run to use


I will need to write these myself, so please open up the location and tell me where to answer this. please also provide guidance/suggestions on how to complete (note - I must write myself but am allowed to ask you to help me suggest)
```

### Prompt 2

I had written my Expected answers into the page myself, so I asked the vibe coder to check that I filled it in correctly before moving on.

```text
I updated the desk_tickets.html. can you please review to make sure I did it correctly and see if we can move to enxt step
```

---

## Problem 7: Backend routes

### Prompt 1

```text
Problem 7: Backend routes

we will create a reach frontend dashboard in the next problem, but before we do so, we willneed a backend for it to call. in backend/main.py, please use FastAPI and add routes to do the following tasks:

1. return the 3 tickets and whether each is open or resolved
2. take a ticket id and run the gent team on that ticket
3. return recent agent events: what each agent sand and which tools they used, so the board can refresh
4. approve a payment or purchase after a human clicks approve (agents only prepare the pay. this route is what actually changes cash)
5. return the current checking balance from cash_accounts
6. reset the db to the original values when you want to try a fresh run


From the backend server, please start the server with: 

uvicorn main:app --reload --port 8000

this will turn on the backend at http://localhost:8000 so the frontend dashboard can call those routes

In output/harness.md, please list each route in one line (what URL and what it does)
```

---

## Problem 8: Agent dashboard

### Prompt 1

```text
Problem 8: Agent dashboard

Pleas build the frontend dashboard in frontend/ with react + vite + typescript. please note that the page should call the routes built in problem 7. at minimum, the board should:

1. list all 3 tickets
2. let you pick one ticket and start the agent team on it
3. show each agent, what they are saying/doing while the ticket runs
4. mark a ticket as resolved when the run is finished
5. show a short summary of what each agent did for that ticket
6. let a human approve a pay or purchase whn asked
7. show the checking balance (it should drop after an approved pay)

Make the dashboard look good - to do so, lets add yale-themed throughout, with different agents being represented by different yale logos, including the mascot bulldog.  its important to be creative here and make it enjoyable for a human user.


the front-end should talk to the back-end through http://localhost:8000. on the backend, allow the vite page origin (usually http://localhost:5173) so the browser is allowed to call thsoe routes

start the board with: npm run dev

this opens the react desk in your browser so can pick tickets and watch agents

write output/design.md with what we chose for the dashboard look (layout, how agents read differently, how resolved tickets and cash show up) and whiy, including the creative choices that make it feel special and somhting humans would actually enjoy using.
```

---

## Problem 9: resolve the tickets

### Prompt 1

```text
Problem 9: resolve the tickets

before we test the agents on a full run over the 3 tickets, lets reset the working db data/campus_customs_new.db again so we have a clean start. note the starting checking balance. then run all 3 tickets on the board (101, 102, 103) until each is resolved. 

Next, open output/desk_tickets.html from prob 6. on each ticket tab, please fill the actual section from this run: which agents worked, what they delegated, and which tools they used. please keep the expected section untouched so we can compare the 2 later.

On the cash tab of the same output/desk_tickets. html, please itemize the money:

* starting checking balance (after the reset)
* for each ticekt: how cash was changedwhen the ticket resolved, and why (which pay/ purchase, dollar amount)
* Ending checking balance: it must match cash_accounts in the working db

wrong acsh math loses points EVEN IF the board shows every ticket resolved. 

Also, please save:
output/resolved_tickets.json: for each ticket: id, final status, short outcome, what each agent contrbited, and any human approvals
output/resolved_board.html: a page you can double-click with a screenshot of the reach board for EACH resolved ticket (101-103)

append real runs to output/audit_trail.json. finish output/harness.md so it covers tables, MCP tools, the 5 agents, API routes, dashboard, and safety rules.
```

### Prompt 2

The first runs left two payments waiting for a human signature, so I approved both on the board myself and re-ran ticket 103 before telling the vibe coder to continue.

```text
I signed both and re-ran 103
```

---

## Problem 10: Reflection

### Prompt 1

```text
Problem 10: Reflection

For this problem, I must write a reflection in my own vibe (you cannot generate it for me). however, can you please help provide some reflection thoughts from this experience?

general thought categories: evaluate agent performance/why
how did actual compare to expected? (please actually list out the actual clearly and I will compare to expected myself)
what would be simpler if using one agent and why?
what are 3-5 problems CC might face that this team could and could not solve

all answers will need to relate to ticket and cash tab
```

### Prompt 2

The Reflection tab still only said "coming later", so I asked for a place to write my reflection myself.

```text
please open reflections tab so i can write
```

### Prompt 3

The tab was split into four separate question boxes, but I wanted to write one general reflection, so I asked to merge them and whether line breaks are safe.

```text
can you update so its just one general reflection section, not broken out by questions? also, am I able to use a return to write across multiple lines, or does that mess up code/formatting?
```

---

## Problem 11: Submit to GitHub

### Prompt 1

```text
Problem 11: Submit to GitHub
now, we need to push code to a public GitHub repo so graders can clone. 
Do NOT push the real .env to github repo. DO include both db files under data/ (the original and working copy) so graders can run app easily
expected file layout:
hw5/
__AI_prompts.md
__requirements.txt
__.env.example
__.gitignore
__.mcp.json
__README.md
__data/
____campus_customs.db
____campus_customs_new.db
__mcp_server/
____server.py
____README.md
__frontend/
__backend/
____main.py
____models.py
____prompts/
______boss.md
______inventory.md
______accounting.md
______facilities.md
______customer_service.md
__output/
____harness.md
____mcp_smoke.json
____desk_tickets.html
____design.md
____resolved_tickets.json
____resolved_board.html
____audit_trail.json
____hgithub_url.txt
Please fix if any of those are clearly misspelled
README should explain: copy original DB to working copy when you need a clean run, start MCP server, start FastAPI backend, start the react board, reset the DB before a full 3-ticket run
```

### Prompt 2

While the vibe coder was preparing the repo, I added a note to make sure the repo URL ends up in the right output file.

```text
repo url should be in output/github_url.txt btw
```

### Prompt 3

The vibe coder asked me to create the empty GitHub repo myself, but I wanted it to handle every step of the submission.

```text
can you do all this for me please
```
