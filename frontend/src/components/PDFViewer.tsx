"use client";

import { Document, Page, pdfjs } from "react-pdf";

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type AnnotationType = "TICK" | "CROSS" | "COMMENT";

type Annotation = {
  id: number;
  type: AnnotationType;
  x: number;
  y: number;
  text?: string;
};

type PDFViewerProps = {
  pdfUrl: string;
  currentPdfPage: number;
  pdfZoom: number;
  pdfRotation: number;
  annotations: Annotation[];
  onLoadSuccess: (data: { numPages: number }) => void;
  onAddAnnotation: (event: React.MouseEvent<HTMLDivElement>) => void;
};

export default function PDFViewer({
  pdfUrl,
  currentPdfPage,
  pdfZoom,
  pdfRotation,
  annotations,
  onLoadSuccess,
  onAddAnnotation,
}: PDFViewerProps) {
  return (
    <div
      onClick={onAddAnnotation}
      className="relative w-full max-w-2xl cursor-crosshair"
    >
      {pdfUrl ? (
        <Document
          file={pdfUrl}
          onLoadSuccess={onLoadSuccess}
          loading={
            <div className="flex min-h-[700px] items-center justify-center rounded-sm border border-slate-300 bg-white shadow-sm">
              <span className="text-sm text-slate-500">
                Loading scanned page...
              </span>
            </div>
          }
          error={
            <div className="flex min-h-[700px] items-center justify-center rounded-sm border border-red-200 bg-white shadow-sm">
              <span className="text-sm text-red-600">
                Unable to load scanned page.
              </span>
            </div>
          }
        >
          <div className="relative">
            <Page
              pageNumber={currentPdfPage}
              width={650}
              scale={pdfZoom}
              rotate={pdfRotation}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />

            {annotations.map((annotation) => (
              <div
                key={annotation.id}
                className="absolute -translate-x-1/2 -translate-y-1/2"
                style={{
                  left: `${annotation.x * 100}%`,
                  top: `${annotation.y * 100}%`,
                }}
              >
                {annotation.type === "TICK" && (
                  <span className="text-3xl font-bold text-green-600">
                    ✓
                  </span>
                )}

                {annotation.type === "CROSS" && (
                  <span className="text-3xl font-bold text-red-600">
                    ✕
                  </span>
                )}

                {annotation.type === "COMMENT" && (
                  <div className="max-w-48 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-slate-700 shadow-sm">
                    {annotation.text}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Document>
      ) : (
        <div className="flex min-h-[700px] items-center justify-center rounded-sm border border-slate-300 bg-white shadow-sm">
          <span className="text-sm text-slate-500">
            Loading scanned page...
          </span>
        </div>
      )}
    </div>
  );
}