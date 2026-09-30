export async function generateAISuggestion({
  baseUrl,
  sheetId,
  questionId,
  token,
}: {
  baseUrl: string;
  sheetId: number | string;
  questionId: number | string;
  token: string;
}) {
  const response = await fetch(
    `${baseUrl}/sheets/${sheetId}/questions/${questionId}/ai-suggest`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message =
      typeof errorData?.detail === "string"
        ? errorData.detail
        : typeof errorData?.detail?.error?.message === "string"
          ? errorData.detail.error.message
          : `AI suggestion request failed: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

export async function getLatestAISuggestion({
  baseUrl,
  sheetId,
  questionId,
  token,
}: {
  baseUrl: string;
  sheetId: number | string;
  questionId: number | string;
  token: string;
}) {
  const response = await fetch(
    `${baseUrl}/sheets/${sheetId}/questions/${questionId}/ai-suggest`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Failed to load AI suggestion: ${response.status}`);
  }

  return response.json();
}

export async function saveMark({
  baseUrl,
  sheetId,
  questionId,
  finalMarks,
  comment,
  aiSuggestionId,
  aiAction = "NONE",
  token,
}: {
  baseUrl: string;
  sheetId: number | string;
  questionId: number | string;
  finalMarks: number;
  comment?: string | null;
  aiSuggestionId?: number | null;
  aiAction?: "ACCEPTED" | "EDITED" | "IGNORED" | "NONE";
  token: string;
}) {
  const response = await fetch(
    `${baseUrl}/sheets/${sheetId}/marks/${questionId}`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        final_marks: finalMarks,
        comment: comment ?? null,
        ai_suggestion_id: aiSuggestionId ?? null,
        ai_action: aiAction,
      }),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message =
      typeof errorData?.detail === "string"
        ? errorData.detail
        : typeof errorData?.detail?.error?.message === "string"
          ? errorData.detail.error.message
          : `Failed to save marks: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

export async function confirmBlankMark({
  baseUrl,
  sheetId,
  questionId,
  token,
}: {
  baseUrl: string;
  sheetId: number | string;
  questionId: number | string;
  token: string;
}) {
  const response = await fetch(
    `${baseUrl}/sheets/${sheetId}/marks/${questionId}/blank`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message =
      typeof errorData?.detail === "string"
        ? errorData.detail
        : `Failed to mark question blank: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

export async function fetchSubmissionCheck({
  baseUrl,
  sheetId,
  token,
}: {
  baseUrl: string;
  sheetId: number | string;
  token: string;
}) {
  const response = await fetch(
    `${baseUrl}/sheets/${sheetId}/submission-check`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      typeof data?.detail === "string"
        ? data.detail
        : `Submission check failed: ${response.status}`;
    throw new Error(message);
  }

  return data;
}

export async function submitSheetEvaluation({
  baseUrl,
  sheetId,
  token,
}: {
  baseUrl: string;
  sheetId: number | string;
  token: string;
}) {
  const response = await fetch(
    `${baseUrl}/sheets/${sheetId}/submit`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.detail?.error?.message === "string"
          ? data.detail.error.message
          : typeof data?.error?.message === "string"
            ? data.error.message
            : `Submission failed: ${response.status}`;
    throw new Error(message);
  }

  return data;
}