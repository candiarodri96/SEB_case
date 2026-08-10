# Portfolio Monitor — compliance monitoring for Portfolio Bond (Kapitalförsäkring)

A prototype second line of defence monitoring system. It reads daily EOD holdings, evaluates every holding against a defined investment policy, reacts to corporate events that change an instrument's characteristics, and shows a compliance officer what needs to be reviewed, and why.

## 1. Background: why this system needs to exist

A Portfolio Bond (kapitalförsäkring) is an insurance wrapper around a securities account. The customer decides what is bought and sold, but the insurance company legally owns the assets. That split is the entire reason for this system:

The customer chooses. The insurer owns it and carries the responsibility.

If a customer buys something outside the investment policy, it is not the customer's problem. It sits on the insurer's balance sheet, and the insurer answers for it. The policy exists because the company carries the risk for a choice it did not make. This system exists because someone has to verify, every day and across every account, that the policy actually holds.

## 2. How I interpreted the task

Two different problems:

**A. Something new arrives.** An instrument appears that has never been held before.
The trigger is a transaction. The customer did something.

**B. Something existing changes.** An instrument held for years stops being eligible
without anyone touching it: delisted, downgraded. The trigger is an event in the
world. Nobody did anything, but the holding is now wrong.

B is the substantive half. Eligibility is not a one time check at purchase. It is a
state that has to be re-evaluated over time.

### Why check after the trade

A trading platform would block many bad purchases up front, and I assume such a
control exists. This system is the second line: an independent check of what the
first line cannot catch. Instruments that were eligible when bought, portfolio level
limits that can break with no transaction at all when a price moves, and instruments
arriving by transfer or corporate action rather than a purchase.

## 3. Scenarios implemented

1. **New investment detected → eligibility check.** Triggered by an instrument that has never been held on any account.
2. **Corporate event → revalidation.** Triggered by an event that changed an instrument's characteristics.

They cover both halves of the problem, entry and time, and they share a single rule engine. Only the reason for evaluating differs: one engine, two triggers.

I skipped the other two options. *Policy breach → action* is the tail end of these two, so every flag already carries a suggested action instead. *Asset monitor → dashboard* contains no compliance logic, and a UI is required regardless, so the dashboard here delivers scenarios 1 and 2 rather than being a scenario of its own.

## 4. Architecture

The EOD file and the corporate event file are read in the same nightly run. The EOD file
is compared against every ISIN ever seen to find new holdings. The event file updates the
instrument register, and every account holding that ISIN is re-evaluated. Both paths end
in the same rule engine, which reads the rules from `policy_v1.json` and the instrument facts
from the register, and returns `COMPLIANT`, `BREACH` or `UNKNOWN` per holding and rule.

Two things follow from this:

**The engine knows nothing about corporate events.** The event updates the register, and
the engine then reads the instrument's current properties as it always does. That is why
there is one rule set rather than two. It also means a new purchase of an already delisted
instrument is caught by scenario 1, with no event needed.

**The AI layer sits after the flags and is removable.** Delete it and the system produces
identical flags and identical outcomes. Only readability degrades.

## 5. Monitoring rules

### What counts as a "new holding"

An ISIN that has never appeared on any account in any previous EOD file. System wide,
not per account, which means persisting the set of all instruments ever seen.

If an instrument is sold and re-bought months later it is not treated as new. It has been
assessed before and the register still holds its classification. The opposite choice is
defensible too, it just generates repeat noise.

### Eligibility rules

Stored as data in `policy/policy_v1.json`, not as hard coded conditionals.

| Rule ID | Rule | Applies to | Rationale |
|---------|------|-----------|-----------|
| R-01 | Only equities, bonds and funds | All | The product is defined for these. Derivatives and structured products need different risk handling. |
| R-02 | Minimum credit rating BBB- | Bonds | BBB- is the investment grade floor. Below it the risk profile is materially different from what the product implies. |
| R-03 | Must be listed on a regulated market | Equities | Unlisted holdings cannot be valued daily or sold when the customer wants to withdraw. |
| R-04 | Max 10% of account value per instrument | All | Concentration risk. The only portfolio level rule. |
| R-05 | Fund domicile within EU/EEA | Funds | Outside the EEA there is often no supervision or reporting that can be relied on. |

Rules have scope. **Instrument level** rules (rating, asset class, listing status) depend
only on the ISIN, so they are evaluated once and reused across every account holding it.
**Portfolio level** rules (concentration) depend on the account, so the same instrument
can pass on one and breach on another.

Every rule also carries an `applies_to` condition that is checked before it runs. A credit
rating measures an issuer's ability to repay a loan, so it exists for bonds and means
nothing for equities. Running a rating rule against an equity would crash or, worse,
produce a false flag.

### Relevant corporate events

**Rating downgrade.** The most common way a holding silently becomes non-compliant.
Ratings are reassessed continuously, so a bond bought at BBB can fall below the floor
without any transaction.

**Delisting.** The instrument stops trading on a regulated venue, which makes it hard
to value and hard to sell.

**Domicile change.** A fund moves jurisdiction and may fall outside permitted domiciles.

**Merger or acquisition.** The holder receives a different instrument that was never
assessed.

**Trading suspension.** Temporary, so arguably a warning rather than a breach. Included
because severity is a policy choice, not a technical one.

## 6. Outcomes

| Outcome | Meaning |
|---------|---------|
| COMPLIANT | The rule was evaluated and satisfied. |
| BREACH | The rule was evaluated and the limit is exceeded. |
| UNKNOWN | The rule could not be evaluated because data is missing. |

UNKNOWN is the most important design decision here. A bond arriving with no rating is not proven compliant and not proven in breach. Treating it as compliant would mean the system's silence is indistinguishable from an actual pass and in compliance, silence about missing data is the dangerous default. UNKNOWN is a first-class outcome requiring human review.

COMPLIANT results are logged rather than discarded. It has to be possible to demonstrate that a check was performed, not merely that it did not fire.

## 7. Data model

| Table | Purpose |
|-------|---------|
| accounts | Account ID, holder type (private / corporate) |
| instruments | One row per ISIN: asset class, issuer, rating, listing status, domicile. Not one row per purchase, instrument facts belong to the ISIN. |
| holdings | One row per account × ISIN × date: quantity, market value |
| corporate_events | Date, ISIN, event type, old value, new value |
| findings | Outcome per holding × rule per run: rule_id, status, threshold, actual, severity, reason, is_new, is_affected |

The EOD file deliberately carries no instrument characteristics, only ISIN and quantity.
Instrument facts come from a separate register. Keeping them separate reflects reality, since
they come from different sources and change at different rates, and it is what makes an event
driven update of a single instrument propagate to every account holding it.

`is_new` and `is_affected` on a finding record which scenario triggered the evaluation. The
rule engine does not set them, since it does not know why it was called. The batch does.

## 8. Assumptions

- A pre-trade eligibility control exists in the trading system. This prototype is the independent second line check.
- EOD files are state snapshots, not transaction logs. New holdings are derived by comparison, not announced.
- Corporate events arrive as a structured feed from a data vendor, not scraped from news. The sample event file simulates this.
- The system flags for human decision. It never divests automatically. Selection is automated, judgement is not.
- Sample data is authored to demonstrate specific scenarios, including deliberate missing data cases.

## 9. Key design decisions

### Rules as data, not code

Hard coded conditionals work, but the policy then only exists scattered through source code. Changing a concentration limit from 10% to 8% would need a developer and a deploy, and there would be nothing to point at when asked what the policy is.

Storing rules as JSON gives three things: the policy can change without a deploy, `rule_id` travels through to the UI as the audit trail, and the file can be versioned, so "which policy applied on 3 March" is answerable.

The trade off is that this replaces simple conditionals with a small interpreter that has to be written and tested. For three rules it is over engineering. For a system meant to live, it is correct.

### SQLite rather than Postgres

SQLite keeps setup at zero for a prototype: no container, no server, no connection string. The repository layer is the only place that would change for Postgres, which is what a production system would use. The schema itself is the same either way.

### A deterministic rule engine, with no LLM in it

Every flag has to be defensible. When a compliance officer asks why something was flagged, the answer has to be "rule R-02, threshold BBB-, actual BB", not "the model judged it unsuitable". The same input must produce the same output every time, or it is not a control.

It is also the right tool. Comparing two values against a threshold is ordinary code, and ordinary code is faster and cheaper across thousands of holdings.

### Where AI is used instead

AI affects presentation, never the outcome:

- **Plain language explanation.** The engine emits `rule_id / threshold / actual`, which is correct and unreadable. The model turns it into a sentence a human can act on.
- **Grouping.** Five breaches stemming from one issuer downgrade are one problem, not five.
- **Prioritisation.** Forty flags are not equally urgent, and ordering is judgement rather than calculation.
- **Classification of unknown instruments.** When an instrument arrives without an asset class, the model proposes one from its name and issuer. The result is marked as a suggestion requiring confirmation. It never enters the register as fact.

The layer has a deterministic template fallback. When no API key is present, or the call
fails, each finding still gets a readable sentence built from the same fields. The demo runs
without a key, which is also the clearest demonstration that the layer is optional: the
findings, the counts and the outcomes are identical either way.

## 10. Considered and rejected

**Anomaly detection over the EOD file.** My first instinct was that an EOD file is a lot of data, so the search should be made efficient by looking for deviating patterns, the way a tax authority screens returns. I rejected it. Pattern screening answers "what looks unusual", which is a different question from "what breaks the rule". A breach can be statistically unremarkable, and an outlier can be perfectly compliant. A control that samples cannot demonstrate coverage, and coverage is the point of a second line control.

The volume concern was also wrong. Rule evaluation is cheap, and instrument level rules run once per ISIN rather than once per holding. The scarce resource is the compliance officer's attention, which is a prioritisation problem downstream of evaluation, not a reason to evaluate less.

**An LLM as the rule engine.** Rejected for determinism and auditability, see above.

**RAG over the policy document.** Retrieval and interpretation are right when a rule is ambiguous prose. These rules are not: "is the rating below BBB-" is a comparison between two values. RAG would introduce non-determinism to solve a problem that does not exist here. It would suit a different project, deriving machine readable rules from a real policy document, which is out of scope.

**A multi agent architecture.** An early sketch had separate agents for detection, news monitoring and analysis. The coordination overhead would have consumed the time budget without improving the output, and the core has to be deterministic regardless.

## 11. Possible extensions

**Proximity to breach score.** A holding at 9.2% against a 10% limit is not a breach, but it will be tomorrow if the price moves. A bond at exactly BBB- is one downgrade from failing. Surfacing this would let the officer act before the breach rather than after.

If built, it has to be kept strictly separate from compliance status. A holding is `COMPLIANT` or `BREACH`, determined by the rule, with no grey scale. A proximity score is a separate column for prioritisation, never a judgement about compliance. Mixing them produces "somewhat in breach", which is not defensible in an audit.

Other extensions: issuer level aggregation across instruments, policy version history with as of queries, a remediation workflow with case status.

## 12. Use of AI in building this

### Where it was used

I started with no background in financial instruments or compliance and used Claude to build up the terminology and the regulatory framing before designing anything: what a rating is and what it applies to, what a corporate event is, and why a Portfolio Bond creates the responsibility it does.

It was also used to challenge my framing. My first mind map designed an investment advisor, recommending assets to a customer and weighing risk against opportunity. The case asks for a compliance monitor serving an internal officer. That reframing changed the entire design.

The frontend was generated. The rule engine and the evaluator were not.

### How I validated output

The AI generated a version of `evaluate_all` where `return findings` sat inside the loop rather than after it. Three other errors in the same file raised exceptions immediately, but this one did not. Nothing in the output indicated that anything was wrong: the function ran, returned a valid list, and reported findings for the first holding only.

I found it by running the engine against test data where I knew in advance how many breaches should appear, not by reading the code. That is why the sample data contains deliberately planted breaches. It gives me an expected count to check against.

The same approach caught two more problems. An agent reported the sample data as generated when the files were zero bytes: the loaders returned empty lists, and the batch would have run to completion reporting no breaches at all. And on the first data generation, seven holdings breached the concentration limit rather than the one I intended, because the random range was too wide. Neither would have been visible without checking the numbers against an expectation.

### What I changed manually

The rule engine and the evaluator I typed by hand rather than generating. They are the two files the whole system rests on.

I dropped Postgres for SQLite. A real system would use Postgres, but for a prototype it adds a container and a connection string without changing the schema. The repository layer is the only thing that would differ.

I stopped delegating file generation to the agent after the zero byte incident and wrote the generator script myself, which also made the sample data reproducible.

I changed the concentration rule to report the computed percentage rather than the raw market value. The first version showed `threshold 10.0, actual 109623.0`, which is correct but unreadable. The two numbers now share a unit.

I also rewrote most of the generated prose in my own words. Text I could not say out loud without reading it was text I did not understand well enough to defend, so it went. The first draft of this README ran to roughly three times its current length.

### Limitations encountered

AI generated code is effective as long as you test it and know the expected outcome beforehand. The risk is not that it writes bad code, it is that it writes plausible code that fails quietly. Reading it is not enough to catch that. Three of the four problems above produced no error at all: an empty file, a truncated loop, and a silent count.

The larger limitation is ownership. If I had handed over more of the design, I would have ended up with a product I could not explain or defend.

A known limitation of the system itself: the instrument register holds current state only. Each run reloads it from the source file and then applies that day's events, which works when days are processed in order but means the register is not a true accumulated history. Re-running an earlier date would evaluate against whatever the register looks like now. An `instrument_history` table with as-of lookups would fix it, and `corporate_events` already holds the raw material.

## 13. Running the project

Backend:

```bash
pip install -r requirements.txt
python scripts/generate_data.py
python -m src.batch.run_daily 2026-08-05
python -m src.batch.run_daily 2026-08-06
python -m src.batch.run_daily 2026-08-07
uvicorn src.api.main:app --reload
```

The three dates must be run in order. The batch derives new holdings by comparing against earlier runs, so starting at the last date would report everything as new.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Tests:

```bash
python -m pytest tests/ -v
```

## 14. Tech stack

Python · SQLite · FastAPI · React (Vite)
