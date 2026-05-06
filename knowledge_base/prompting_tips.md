# Prompting tips (baseline vs improved)

## Baseline prompt

A baseline prompt usually contains:

- A generic "helpful assistant" system message
- The user question

This is simple but may be **ungrounded**.

## Improved prompt

An improved prompt often adds:

- Explicit rules to use provided context
- A few-shot block showing desired style/behavior
- A structured template including a "Context" section and a "Question" section

## Handling missing context

If the retrieved context doesn't contain the answer, a good response should:

- Say the context is insufficient
- Explain what information is missing
- Provide a cautious best-effort answer
