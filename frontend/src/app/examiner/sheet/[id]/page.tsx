
"use client";

import { useParams } from "next/navigation";
import dynamic from "next/dynamic";

const PDFViewer = dynamic(
  () => import("@/components/PDFViewer"),
  { ssr: false }
);

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/layout/DashboardLayout";
import {
  saveMark,
  confirmBlankMark,
  generateAISuggestion,
  getLatestAISuggestion,
  fetchSubmissionCheck,
  submitSheetEvaluation,
} from "@/lib/api";

type AISuggestionState = {
  id: number | null;
  marks: number | null;
  reasoning: string;
  summary: string;
  strengths: string[];
  missingConcepts: string[];
  raw: Record<string, unknown>;
};

type QuestionStatus =
  | "NOT_ANSWERED"
  | "ANSWER_DETECTED_UNEVALUATED"
  | "EVALUATED"
  | "CONFIRMED_BLANK";

type Question = {
  id: number;
  number: string;
  marks: number;
  maxMarks: number;
  status: QuestionStatus;
};

type AnnotationType = "TICK" | "CROSS" | "COMMENT";

type Annotation = {
  id: number;
  type: AnnotationType;
  x: number;
  y: number;
  text?: string;
};

const initialQuestions: Question[] = [];

export default function OSMPage() {
  const params = useParams();
  const sheetId = params.id;
  const [loadingMarks, setLoadingMarks] = useState(true);
const [marksError, setMarksError] = useState("");
  const [questions, setQuestions] =
    useState<Question[]>(initialQuestions);

   const [sheetInfo, setSheetInfo] = useState<{
   anonymous_code: string;
  exam: string;
} | null>(null);

const [pdfUrl, setPdfUrl] = useState("");
const [pdfPageCount, setPdfPageCount] = useState(0);
const [currentPdfPage, setCurrentPdfPage] = useState(2);
const [pdfZoom, setPdfZoom] = useState(1);
const [pdfRotation, setPdfRotation] = useState(0);
const [aiSuggestion, setAiSuggestion] = useState<AISuggestionState | null>(null);
const [aiLoading, setAiLoading] = useState(false);
const [aiError, setAiError] = useState("");
const [aiEditMode, setAiEditMode] = useState(false);
const [aiEditMarks, setAiEditMarks] = useState("");
const [submitMessage, setSubmitMessage] = useState("");
const [submitting, setSubmitting] = useState(false);

useEffect(() => {
  const token = localStorage.getItem("access_token");

  if (!token || !sheetId) {
    return;
  }

  fetch(`http://127.0.0.1:8000/examiner/sheets/${sheetId}/file`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to load answer sheet: ${response.status}`);
      }

      return response.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
    })
    .catch((error) => {
      console.error("Answer sheet error:", error);
    });
}, [sheetId]);

  const [selectedIndex, setSelectedIndex] = useState(2);

  const [annotationTool, setAnnotationTool] =
  useState<AnnotationType>("TICK");

const [annotations, setAnnotations] =
  useState<Annotation[]>([]);

const [commentText, setCommentText] =
  useState("");

  const [marksInput, setMarksInput] = useState("0");

  const [validationMessage, setValidationMessage] =
    useState("");
useEffect(() => {
  const token = localStorage.getItem("access_token");

  if (!token || !sheetId) {
    return;
  }

  fetch("http://127.0.0.1:8000/examiner/queue", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(
          `Failed to load sheet information: ${response.status}`
        );
      }

      return response.json();
    })
    .then((data) => {
      const sheet = data.find(
        (item: {
          sheet_id: number;
          anonymous_code: string;
          exam: string;
        }) => String(item.sheet_id) === String(sheetId)
      );

      if (sheet) {
        setSheetInfo({
          anonymous_code: sheet.anonymous_code,
          exam: sheet.exam,
        });
      }
    })
    .catch((error) => {
      console.error("Sheet information error:", error);
    });
}, [sheetId]);

    useEffect(() => {
  const token = localStorage.getItem("access_token");

  if (!token || !sheetId) {
    setMarksError("Authentication required.");
    setLoadingMarks(false);
    return;
  }

  fetch(`http://127.0.0.1:8000/sheets/${sheetId}/marks`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Failed to load marks: ${response.status}`);
      }

      return response.json();
    })
    .then((data) => {
  console.log("Marks API response:", data);

  const backendQuestions: Question[] = (data.questions || []).map(
    (question: {
      question_id: number;
      question_number: string;
      max_marks: number;
      final_marks: number | null;
      eval_status: string | null;
    }) => {
      const qNum = String(question.question_number).startsWith("Q")
        ? String(question.question_number)
        : `Q${question.question_number}`;

      const rawStatus = question.eval_status;
      let status: QuestionStatus = "NOT_ANSWERED";
      if (rawStatus === "CONFIRMED_BLANK") {
        status = "CONFIRMED_BLANK";
      } else if (rawStatus === "EVALUATED" || question.final_marks !== null) {
        status = "EVALUATED";
      } else if (rawStatus === "ANSWER_DETECTED_UNEVALUATED") {
        status = "ANSWER_DETECTED_UNEVALUATED";
      } else {
        status = "NOT_ANSWERED";
      }

      return {
        id: question.question_id,
        number: qNum,
        marks: question.final_marks ?? 0,
        maxMarks: question.max_marks,
        status,
      };
    }
  );

  setQuestions(backendQuestions);

  if (backendQuestions.length > 0) {
    setSelectedIndex(0);
    setMarksInput(String(backendQuestions[0].marks));
    void loadLatestAiSuggestion(backendQuestions[0].id);
  }
})
    .catch((error) => {
      setMarksError(
        error instanceof Error
          ? error.message
          : "Unable to load marks."
      );
    })
    .finally(() => {
      setLoadingMarks(false);
    });
}, [sheetId]);

  const selectedQuestion = questions[selectedIndex] || {
    id: 0,
    number: "Q1",
    marks: 0,
    maxMarks: 10,
    status: "NOT_ANSWERED" as QuestionStatus,
  };

  const addAnnotation = (
  event: React.MouseEvent<HTMLDivElement>
) => {
  const rect = event.currentTarget.getBoundingClientRect();

  const x =
    (event.clientX - rect.left) / rect.width;

  const y =
    (event.clientY - rect.top) / rect.height;

  if (
    annotationTool === "COMMENT" &&
    !commentText.trim()
  ) {
    return;
  }

  const annotation: Annotation = {
    id: Date.now(),
    type: annotationTool,
    x,
    y,
    text:
      annotationTool === "COMMENT"
        ? commentText
        : undefined,
  };

  setAnnotations((current) => [
    ...current,
    annotation,
  ]);

  if (annotationTool === "COMMENT") {
    setCommentText("");
  }
};

  const totalMarks = questions.reduce(
    (total, question) => total + question.marks,
    0
  );

  const totalMaximum = questions.reduce(
    (total, question) => total + question.maxMarks,
    0
  );

  const validateMarks = (value: string) => {
    if (value.trim() === "") {
      setValidationMessage("");
      return;
    }

    const marks = Number(value);

    if (Number.isNaN(marks)) {
      setValidationMessage("Enter a valid number.");
      return;
    }

    if (marks < 0) {
      setValidationMessage("Marks cannot be negative.");
      return;
    }

    if (marks > selectedQuestion.maxMarks) {
      setValidationMessage(
        `Marks cannot exceed ${selectedQuestion.maxMarks}.`
      );
      return;
    }

    if (marks * 2 !== Math.floor(marks * 2)) {
      setValidationMessage(
        "Marks must be entered in 0.5 steps."
      );
      return;
    }

    setValidationMessage("");
  };

  const updateMarks = (value: string) => {
    setMarksInput(value);
    validateMarks(value);

    const marks = Number(value);

    if (
      value.trim() !== "" &&
      !Number.isNaN(marks) &&
      marks >= 0 &&
      marks <= selectedQuestion.maxMarks &&
      marks * 2 === Math.floor(marks * 2)
    ) {
      setQuestions((currentQuestions) =>
        currentQuestions.map((question, index) =>
          index === selectedIndex
            ? {
                ...question,
                marks,
                status: "EVALUATED",
              }
            : question
        )
      );
            const token = localStorage.getItem("access_token");

      if (token && sheetId) {
        saveMark({
          baseUrl: "http://127.0.0.1:8000",
          sheetId: Array.isArray(sheetId) ? sheetId[0] : sheetId,
          questionId: selectedQuestion.id,
          finalMarks: marks,
          comment: commentText,
          token,
        }).catch((error) => {
          console.error("Failed to save marks:", error);
        });
      }
    }
  };

  const getSheetIdValue = () =>
    Array.isArray(sheetId) ? sheetId[0] : sheetId;

  const normalizeAiSuggestion = (data: unknown): AISuggestionState => {
    const raw =
      data && typeof data === "object"
        ? (data as Record<string, unknown>)
        : {};

    const possibleMarks = [
      raw.suggested_marks,
      raw.suggestedMarks,
      raw.ai_marks,
      raw.aiMarks,
      raw.marks,
      raw.score,
    ];

    const numericMarks = possibleMarks.find(
      (value) =>
        typeof value === "number" && Number.isFinite(value)
    );

    const reasoningValue =
      raw.reasoning ?? raw.explanation ?? raw.rationale ?? raw.reason ?? "";

    const idValue = raw.id ?? raw.ai_suggestion_id ?? raw.suggestion_id;

   return {
  id: typeof idValue === "number" ? idValue : null,
  marks: typeof numericMarks === "number" ? numericMarks : null,
  reasoning:
    typeof reasoningValue === "string"
      ? reasoningValue
      : JSON.stringify(reasoningValue),
  summary: typeof raw.summary === "string" ? raw.summary : "",
  strengths: Array.isArray(raw.strengths)
    ? raw.strengths.filter((value): value is string => typeof value === "string")
    : [],
    missingConcepts: Array.isArray(raw.missing_concepts)
    ? raw.missing_concepts.filter(
        (value): value is string => typeof value === "string"
      )
    : [],
  raw,
  };
  };

  const loadLatestAiSuggestion = async (questionId: number) => {
    const token = localStorage.getItem("access_token");
    const id = getSheetIdValue();

    if (!token || !id || !questionId) {
      setAiSuggestion(null);
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/sheets/${id}/questions/${questionId}/ai-suggest`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.status === 404) {
        setAiSuggestion(null);
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to load AI suggestion: ${response.status}`);
      }

      const data = await response.json();
      setAiSuggestion(normalizeAiSuggestion(data));
      setAiEditMode(false);
    } catch (error) {
      console.error("AI suggestion load error:", error);
    }
  };

  const requestAiSuggestion = async () => {
    const token = localStorage.getItem("access_token");
    const id = getSheetIdValue();

    if (!token || !id || !selectedQuestion?.id) {
      setAiError("Unable to request AI suggestion.");
      return;
    }

    setAiLoading(true);
    setAiError("");
    setAiEditMode(false);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/sheets/${id}/questions/${selectedQuestion.id}/ai-suggest`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : `AI suggestion failed: ${response.status}`
        );
      }

      setAiSuggestion(normalizeAiSuggestion(data));
    } catch (error) {
      setAiError(
        error instanceof Error
          ? error.message
          : "Unable to generate AI suggestion."
      );
    } finally {
      setAiLoading(false);
    }
  };

  const saveAiAction = async (
    action: "ACCEPTED" | "EDITED" | "IGNORED",
    marks: number | null
  ) => {
    const token = localStorage.getItem("access_token");
    const id = getSheetIdValue();

    if (!token || !id || !selectedQuestion?.id || !aiSuggestion) {
      return;
    }

    if (action !== "IGNORED" &&
        (marks === null ||
          marks < 0 ||
          marks > selectedQuestion.maxMarks ||
          marks * 2 !== Math.floor(marks * 2))) {
      setAiError("AI marks must be within the question limit and use 0.5 steps.");
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/sheets/${id}/marks/${selectedQuestion.id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            final_marks: marks ?? selectedQuestion.marks,
            comment: commentText || null,
            ai_suggestion_id: aiSuggestion.id,
            ai_action: action,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to save AI action: ${response.status}`);
      }

      if (action !== "IGNORED" && marks !== null) {
        setMarksInput(String(marks));
        setQuestions((current) =>
          current.map((question, index) =>
            index === selectedIndex
              ? { ...question, marks, status: "EVALUATED" }
              : question
          )
        );
      }

      setAiEditMode(false);
      setAiError("");
    } catch (error) {
      setAiError(
        error instanceof Error
          ? error.message
          : "Unable to save AI action."
      );
    }
  };

  const checkAndSubmit = async () => {
    setSubmitMessage("");

    const unchecked = questions.find(
  (question) =>
    question.status !== "EVALUATED" &&
    question.status !== "CONFIRMED_BLANK"
);

    if (unchecked) {
      setSubmitMessage(
        `Potential unchecked question detected. Please review ${unchecked.number}.`
      );
      setSelectedIndex(questions.indexOf(unchecked));
      setMarksInput(String(unchecked.marks));
      return;
    }

    const token = localStorage.getItem("access_token");
    const id = getSheetIdValue();

    if (!token || !id) {
      setSubmitMessage("Authentication required.");
      return;
    }

    setSubmitting(true);

    try {
      const checkResponse = await fetch(
        `http://127.0.0.1:8000/sheets/${id}/submission-check`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const checkData = await checkResponse.json().catch(() => ({}));

      if (!checkResponse.ok) {
        throw new Error(
          typeof checkData?.detail === "string"
            ? checkData.detail
            : `Submission check failed: ${checkResponse.status}`
        );
      }

      const canSubmit =
        checkData?.can_submit ??
        checkData?.canSubmit ??
        checkData?.ready ??
        true;

      if (!canSubmit) {
        const issues = Array.isArray(checkData?.issues)
          ? checkData.issues
          : Array.isArray(checkData?.errors)
            ? checkData.errors
            : [];

        setSubmitMessage(
          issues.length > 0
            ? issues.join(" ")
            : "Submission check did not pass. Please review the questions before submitting."
        );
        return;
      }

      const submitResponse = await fetch(
        `http://127.0.0.1:8000/sheets/${id}/submit`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const submitData = await submitResponse.json().catch(() => ({}));

      if (!submitResponse.ok) {
        throw new Error(
          typeof submitData?.detail === "string"
            ? submitData.detail
            : `Submission failed: ${submitResponse.status}`
        );
      }

      setSubmitMessage(
        typeof submitData?.message === "string"
          ? submitData.message
          : "Sheet submitted successfully."
      );
    } catch (error) {
      setSubmitMessage(
        error instanceof Error
          ? error.message
          : "Unable to submit the sheet."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const selectQuestion = (index: number) => {
    setSelectedIndex(index);

    setMarksInput(
      String(questions[index].marks)
    );

    setValidationMessage("");
    setAiError("");
    setAiEditMode(false);
    void loadLatestAiSuggestion(questions[index].id);
  };

  const goToPreviousQuestion = () => {
    if (selectedIndex === 0) {
      return;
    }

    selectQuestion(selectedIndex - 1);
  };

  const goToNextQuestion = () => {
    if (selectedIndex === questions.length - 1) {
      return;
    }

    selectQuestion(selectedIndex + 1);
  };

  return (
    <DashboardLayout>
      <div className="space-y-5">

        {/* Header */}
        <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold text-slate-900">
                On-Screen Marking
              </h2>

              <span className="text-slate-700">
  {sheetInfo?.anonymous_code ?? "Loading..."}
</span>
            </div>

            <p className="text-sm text-slate-600">
  {sheetInfo?.exam ?? "Loading..."}
</p>
          </div>

          {/* Live Total */}
          <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
            <p className="text-xs text-slate-500">
              Live Total
            </p>

            <p className="mt-1 text-lg font-semibold text-slate-900">
              {totalMarks} / {totalMaximum}
            </p>
          </div>
        </div>

        {/* OSM Workspace */}
        <div className="grid min-h-[650px] grid-cols-1 overflow-hidden rounded-lg border border-slate-200 bg-white lg:grid-cols-[1fr_340px]">

          {/* Page Viewer */}
          <section className="border-b border-slate-200 bg-slate-100 lg:border-b-0 lg:border-r">

            <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
              <div>
                <p className="text-sm font-medium text-slate-900">
                  Answer Sheet
                </p>

                <p className="text-xs text-slate-500">
                  Original scanned page
                </p>
              </div>

              <div className="flex items-center gap-2">

                <button
  type="button"
  onClick={() =>
    setPdfZoom((zoom) => Math.max(0.5, zoom - 0.1))
  }
  className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
>
                  −
                </button>

                <span className="text-xs text-slate-500">
                  {Math.round(pdfZoom * 100)}%
                </span>

                <button
  type="button"
  onClick={() =>
    setPdfZoom((zoom) => Math.min(2, zoom + 0.1))
  }
  className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
>
  +
</button>



              </div>
            </div>

            <div className="mt-3 flex items-center gap-2">

  <button
    type="button"
    onClick={() => setAnnotationTool("TICK")}
    className={`rounded-md border px-3 py-1.5 text-sm font-medium ${
      annotationTool === "TICK"
        ? "border-green-500 bg-green-50 text-green-700"
        : "border-slate-300 bg-white text-slate-700"
    }`}
  >
    ✓ Tick
  </button>

  <button
    type="button"
    onClick={() => setAnnotationTool("CROSS")}
    className={`rounded-md border px-3 py-1.5 text-sm font-medium ${
      annotationTool === "CROSS"
        ? "border-red-500 bg-red-50 text-red-700"
        : "border-slate-300 bg-white text-slate-700"
    }`}
  >
    ✕ Cross
  </button>

  <button
    type="button"
    onClick={() => setAnnotationTool("COMMENT")}
    className={`rounded-md border px-3 py-1.5 text-sm font-medium ${
      annotationTool === "COMMENT"
        ? "border-blue-500 bg-blue-50 text-blue-700"
        : "border-slate-300 bg-white text-slate-700"
    }`}
  >
    T Comment
  </button>

</div>

            {/* Scanned page */}

            {/* Scanned page */}
<div className="flex min-h-[580px] items-start justify-center overflow-auto p-6">
  <PDFViewer
    pdfUrl={pdfUrl}
    currentPdfPage={currentPdfPage}
    pdfZoom={pdfZoom}
    pdfRotation={pdfRotation}
    annotations={annotations}
    onLoadSuccess={({ numPages }) => {
      setPdfPageCount(numPages);
    }}
    onAddAnnotation={addAnnotation}
  />
</div>

        {/* Page navigation */}
        <div className="flex items-center justify-between border-t border-slate-200 bg-white px-4 py-3">

              <button
  type="button"
  onClick={() => {
    if (currentPdfPage > 2) {
      setCurrentPdfPage((page) => page - 1);
    }
  }}
  disabled={currentPdfPage <= 2}
  className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
>
  Previous Page
</button>

             <span className="text-sm text-slate-500">
  {pdfPageCount > 1
    ? `${currentPdfPage - 1} / ${pdfPageCount - 1}`
    : "Loading..."}
</span>

             <button
  type="button"
  onClick={() => {
    if (currentPdfPage < pdfPageCount) {
      setCurrentPdfPage((page) => page + 1);
    }
  }}
  disabled={currentPdfPage >= pdfPageCount}
  className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
>
  Next Page
</button>

            </div>

          </section>

          {/* Right Panel */}
          <aside className="bg-white">

            {/* Questions */}
            <div className="border-b border-slate-200">

              <div className="px-4 py-4">

                <h3 className="text-sm font-semibold text-slate-900">
                  Questions
                </h3>

                <p className="mt-1 text-xs text-slate-500">
                  Select a question to evaluate.
                </p>

              </div>

              <div className="divide-y divide-slate-100">

                {questions.map((question, index) => (
                  <button
                    key={question.number}
                    type="button"
                    onClick={() => selectQuestion(index)}
                    className={`w-full px-4 py-4 text-left transition hover:bg-slate-50 ${
                      index === selectedIndex
                        ? "bg-blue-50"
                        : ""
                    }`}
                  >

                    <div className="flex items-center justify-between">

                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          {question.number}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          Max marks: {question.maxMarks}
                        </p>
                      </div>

                      <span
                        className={`rounded-full px-2 py-1 text-[10px] font-medium ${
                          question.status === "EVALUATED"
                            ? "bg-green-50 text-green-700"
                            : question.status === "CONFIRMED_BLANK"
                              ? "bg-slate-100 text-slate-600"
                              : "bg-amber-50 text-amber-700"
                        }`}
                      >
                        {question.status}
                      </span>

                    </div>

                  </button>
                ))}

              </div>

            </div>

            {/* Marking Panel */}
            <div className="p-4">

              <div className="mb-4">

                <h3 className="text-sm font-semibold text-slate-900">
                  Marking
                </h3>

                <p className="mt-1 text-xs text-slate-500">
                  {selectedQuestion.number} · Maximum marks{" "}
                  {selectedQuestion.maxMarks}
                </p>

              </div>

              {/* Marks */}
              <div>

                <label
                  htmlFor="marks"
                  className="mb-2 block text-sm font-medium text-slate-700"
                >
                  Marks
                </label>

                <input
                  id="marks"
                  type="text"
                  inputMode="decimal"
                  value={marksInput}
                  onChange={(event) =>
                    updateMarks(event.target.value)
                  }
                  className={`w-full rounded-md border px-3 py-2.5 text-sm text-slate-900 outline-none ${
                    validationMessage
                      ? "border-red-400 focus:ring-2 focus:ring-red-100"
                      : "border-slate-300 focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                  }`}
                />

                {validationMessage && (
                  <p className="mt-2 text-xs text-red-600">
                    {validationMessage}
                  </p>
                )}

                {!validationMessage && (
                  <p className="mt-2 text-xs text-slate-500">
                    Marks can be entered in 0.5 steps.
                  </p>
                )}

                            </div>

              {/* Comment */}
              <div className="mt-5">
                <label
                  htmlFor="comment"
                  className="mb-2 block text-sm font-medium text-slate-700"
                >
                  Comment
                </label>

                <textarea
                  id="comment"
                  value={commentText}
                  onChange={(event) =>
                    setCommentText(event.target.value)
                  }
                  placeholder="Enter examiner comment..."
                  rows={3}
                  className="w-full resize-none rounded-md border border-slate-300 px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                />

                <p className="mt-2 text-xs text-slate-500">
                  Select Comment, then click on the answer sheet.
                </p>
              </div>

              {/* Question total */}

              {/* AI Suggest */}
              <div className="mt-5">
                <button
                  type="button"
                  onClick={requestAiSuggestion}
                  disabled={aiLoading}
                  className="w-full rounded-md border border-blue-300 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {aiLoading ? "Generating AI Suggestion..." : "AI Suggest"}
                </button>
              </div>

              <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">
                  AI Suggestion
                </p>

                {aiError && (
                  <p className="mt-2 text-xs text-red-600">{aiError}</p>
                )}

                {!aiSuggestion && !aiError && (
                  <p className="mt-2 text-xs text-slate-500">
                    AI suggestion and reasoning will appear here.
                  </p>
                )}

                {aiSuggestion && (
                  <>
                    <div className="mt-3 rounded-md border border-slate-200 bg-white p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-xs font-medium text-slate-500">
                          Suggested Marks
                        </span>
                        {aiEditMode ? (
                          <input
                            type="text"
                            inputMode="decimal"
                            value={aiEditMarks}
                            onChange={(event) => setAiEditMarks(event.target.value)}
                            className="w-20 rounded border border-slate-300 px-2 py-1 text-sm"
                          />
                        ) : (
                          <span className="text-sm font-semibold text-slate-900">
                            {aiSuggestion.marks ?? "Not provided"}
                          </span>
                        )}
                      </div>

                      <p className="mt-3 text-xs font-medium text-slate-500">
                        Reasoning
                      </p>
                      <p className="mt-1 text-xs leading-5 text-slate-700">
                        {aiSuggestion.reasoning || "No reasoning provided."}
                      </p>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={aiSuggestion.marks === null}
                        onClick={() =>
                          void saveAiAction("ACCEPTED", aiSuggestion.marks)
                        }
                        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Accept
                      </button>

                      {aiEditMode ? (
                        <button
                          type="button"
                          onClick={() => {
                            const edited = Number(aiEditMarks);
                            void saveAiAction(
                              "EDITED",
                              Number.isFinite(edited) ? edited : null
                            );
                          }}
                          className="rounded-md border border-blue-300 bg-blue-50 px-3 py-2 text-xs font-medium text-blue-700"
                        >
                          Save Edit
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => {
                            setAiEditMarks(
                              aiSuggestion.marks === null
                                ? ""
                                : String(aiSuggestion.marks)
                            );
                            setAiEditMode(true);
                          }}
                          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700"
                        >
                          Edit
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => void saveAiAction("IGNORED", null)}
                        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700"
                      >
                        Ignore
                      </button>
                    </div>
                  </>
                )}
              </div>
              <div className="mt-5 rounded-md bg-slate-50 p-4">

                <div className="flex items-center justify-between">

                  <span className="text-sm text-slate-600">
                    Question Score
                  </span>

                  <span className="text-sm font-semibold text-slate-900">
                    {selectedQuestion.marks} /{" "}
                    {selectedQuestion.maxMarks}
                  </span>

                </div>

              </div>

              {/* Question Navigation */}
              <div className="mt-5 grid grid-cols-2 gap-2">

                <button
                  type="button"
                  onClick={goToPreviousQuestion}
                  disabled={selectedIndex === 0}
                  className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous Q
                </button>

                <button
                  type="button"
                  onClick={goToNextQuestion}
                  disabled={
                    selectedIndex === questions.length - 1
                  }
                  className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next Q
                </button>

              </div>

              {/* Submit */}
              <div className="mt-5 border-t border-slate-200 pt-4">
                <button
                  type="button"
                  onClick={checkAndSubmit}
                  disabled={submitting}
                  className="w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submitting ? "Checking..." : "Submit"}
                </button>

                {submitMessage && (
                  <p className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-700">
                    {submitMessage}
                  </p>
                )}
              </div>

              {/* Status */}
              <div className="mt-5 border-t border-slate-200 pt-4">

                <div className="flex items-center justify-between">

                  <span className="text-xs text-slate-500">
                    Status
                  </span>

                  <span className="rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
                    {selectedQuestion.status}
                  </span>

                </div>

              </div>

            </div>

          </aside>

        </div>

      </div>
    </DashboardLayout>
  );
}