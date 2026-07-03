# Agency Engine

> *The decision-to-act system of Chameha.*

---

# Overview

Agency determines whether Chameha should take action.

Most AI systems only answer questions.

Chameha may instead

- answer
- recommend
- plan
- ask permission
- execute
- monitor
- continue autonomously

The Agency Engine determines which behaviour is appropriate.

It represents Chameha's operational autonomy.

---

# Responsibilities

The Agency Engine decides

- whether an action should occur
- when an action should occur
- whether user approval is required
- whether permissions allow execution
- whether confidence is sufficient
- whether the action is safe
- whether the action aligns with active goals

Agency never decides *how* to perform work.

Planning and Execution handle that.

Agency only decides whether action should begin.

---

# Position

```
Intent

↓

Reasoning

↓

Agency

↓

Planning

↓

Execution
```

---

# Decision Levels

Agency classifies actions into five levels.

## Level 0

Observation only.

Example

"I noticed your battery is low."

No action.

---

## Level 1

Recommendation.

Example

"You should probably charge your laptop."

Still no execution.

---

## Level 2

Permission Request.

Example

"I can order your medication.

Would you like me to?"

---

## Level 3

Delegated Execution.

The user has already granted permission.

Example

- schedule meetings
- pay subscriptions
- control smart home
- start backups

---

## Level 4

Autonomous Behaviour.

Reserved for trusted environments.

Examples

- hospital monitoring
- industrial control
- military systems
- enterprise automation

Actions occur without asking every time because policy already authorises them.

---

# Inputs

Agency evaluates

- Intent
- Goals
- Permissions
- Digital Twin
- Confidence
- Risk assessment
- Safety policies
- Current context
- Organisational policies

---

# Outputs

Agency produces

```
Decision

Permission Required

Confidence

Priority

Execution Mode

Explanation
```

---

# Execution Modes

```
Respond

Recommend

Request Approval

Execute

Schedule

Monitor

Ignore
```

---

# Safety

Agency never bypasses

- permissions
- privacy rules
- security policies
- organisational governance

Every autonomous action must be explainable.

---

# Enterprise Examples

## Personal Assistant

Order groceries.

↓

Permission required.

---

## Hospital

Detect cardiac emergency.

↓

Immediate execution.

Alert staff.

---

## Company

Revenue forecast completed.

↓

Automatically notify finance team.

---

## Military

Threat confidence exceeds threshold.

↓

Escalate command workflow.

---

# Relationship with Other Engines

Reasoning determines what is logically correct.

Agency determines whether Chameha should act.

Planning determines how.

Execution performs the work.

Reflection evaluates the outcome.

---

# Future Evolution

Future versions will support

- adaptive autonomy
- organisation-specific policies
- trust scoring
- continuous permission learning
- ethical reasoning
- autonomous multi-agent delegation

---

# Summary

Agency transforms intelligence into behaviour.

Without Agency, Chameha can only answer questions.

With Agency, Chameha becomes capable of acting responsibly within permissions, policies and user intent.
