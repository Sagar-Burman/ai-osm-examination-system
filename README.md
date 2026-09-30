# EvalAI

AI-Driven Examination Evaluation & On-Screen Marking Platform

## Overview

EvalAI is a digital examination evaluation platform for scanned answer sheets.
It supports anonymous examiner evaluation, On-Screen Marking (OSM), AI-assisted
evaluation, quality checks, anomaly detection, moderation, analytics and
result processing.

## Core Principle

AI assists. Humans decide.

The examiner remains responsible for the final evaluation.

## Key Features

- Anonymous answer-sheet evaluation
- Examiner allocation and queue
- On-Screen Marking (OSM)
- Question-wise marks and live total
- Automatic mark validation
- Unchecked-answer detection
- OCR-assisted processing
- AI Suggested Marks with Accept / Edit / Ignore
- Anomaly and answer-similarity detection
- Moderation workflow
- Analytics and audit APIs
- Result approval, release and export

## Demo Workflow

1. Examiner login
2. Open assigned anonymous answer sheet
3. Evaluate answers using OSM
4. Enter and validate marks
5. Use AI Suggest
6. Resolve unchecked questions
7. Submit the sheet
8. Anomaly/moderation workflow

## Technology Stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- React PDF
- Recharts

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication
- OCR / AI / ML services

## Local Setup

### Backend

```bash
cd backend
uvicorn app.main:app --reload