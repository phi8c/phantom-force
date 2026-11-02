"use client";

import { useState } from "react";
import type { StructuredResult } from "../types/chat.types";

const colors = ["#2563eb", "#d97706", "#059669"];
const format = (value: unknown) => value === null || value === undefined ? "—" : String(value);
const formatCell = (value: unknown, column: string, result: StructuredResult) =>
  typeof value === "number" && result.column_metadata?.[column]?.percentage
    ? new Intl.NumberFormat("vi", { style: "percent", maximumFractionDigits: 4 }).format(value)
    : format(value);

function ResultChart({ result }: { result: StructuredResult }) {
  const spec = result.chart;
  if (!spec) return null;
  const x = result.columns.indexOf(spec.x);
  const series = spec.y.map((key) => ({ key, index: result.columns.indexOf(key) })).filter((s) => s.index >= 0);
  const rows = result.rows.slice(0, 50);
  const percent = series.every((s) => result.column_metadata?.[s.key]?.percentage);
  if (x < 0 || !series.length || !rows.length) return null;
  const values = rows.flatMap((row) => series.map((s) => row[s.index])).filter((v): v is number => typeof v === "number" && Number.isFinite(v));
  if (!values.length) return null;
  const min = Math.min(0, ...values), max = Math.max(0, ...values);
  const span = max - min || 1;
  const left = 75, top = 20, width = 630, height = 210;
  const step = width / rows.length;
  const cx = (index: number) => left + step * (index + 0.5);
  const cy = (value: number) => top + height - (value - min) / span * height;
  return (
    <figure className="space-y-2" aria-label={spec.title ?? "Biểu đồ từ kết quả truy vấn Excel"}>
      <figcaption className="text-sm font-medium">{spec.title ?? "Biểu đồ dữ liệu"}</figcaption>
      <svg viewBox="0 0 760 300" role="img" className="w-full rounded-lg border bg-background">
        <title>{spec.title ?? "Biểu đồ dữ liệu Excel"}</title>
        {Array.from({ length: 5 }, (_, i) => {
          const value = min + span * i / 4;
          return <g key={i}>
            <line x1={left} x2={left + width} y1={cy(value)} y2={cy(value)} stroke="currentColor" opacity="0.12" />
            <text x={left - 8} y={cy(value) + 4} textAnchor="end" fontSize="10" fill="currentColor">{new Intl.NumberFormat("vi", percent ? { style: "percent", maximumFractionDigits: 2 } : { maximumFractionDigits: 2, notation: "compact" }).format(value)}</text>
          </g>;
        })}
        <line x1={left} x2={left + width} y1={cy(0)} y2={cy(0)} stroke="currentColor" opacity="0.4" />
        {series.map((s, seriesIndex) => {
          if (spec.type === "line") {
            let drawing = false;
            const path = rows.map((row, i) => {
              const value = row[s.index];
              if (typeof value !== "number" || !Number.isFinite(value)) { drawing = false; return ""; }
              const part = `${drawing ? "L" : "M"}${cx(i)},${cy(value)}`;
              drawing = true;
              return part;
            }).join(" ");
            return <path key={s.key} d={path} stroke={colors[seriesIndex % colors.length]} fill="none" strokeWidth="2"><title>{s.key}</title></path>;
          }
          return rows.map((row, i) => {
            const value = row[s.index];
            if (typeof value !== "number" || !Number.isFinite(value)) return null;
            const barWidth = Math.max(1, step * 0.8 / series.length);
            return <rect key={`${s.key}-${i}`} x={left + i * step + step * 0.1 + seriesIndex * barWidth}
              y={Math.min(cy(0), cy(value))} width={barWidth} height={Math.abs(cy(value) - cy(0))}
              fill={colors[seriesIndex % colors.length]}><title>{`${format(row[x])} · ${s.key}: ${formatCell(value,s.key,result)}`}</title></rect>;
          });
        })}
        {rows.map((row, i) => i % Math.max(1, Math.ceil(rows.length / 8)) === 0 &&
          <text key={i} x={cx(i)} y={top + height + 20} textAnchor="end" transform={`rotate(-25 ${cx(i)} ${top + height + 20})`} fontSize="10" fill="currentColor">{format(row[x]).slice(0, 28)}</text>)}
      </svg>
      <div className="flex flex-wrap gap-4 text-xs">{series.map((s, i) => <span key={s.key} className="flex items-center gap-1"><span className="size-2 rounded-sm" style={{ background: colors[i % colors.length] }} />{s.key}</span>)}</div>
      {result.rows.length > 50 && <p className="text-xs text-muted-foreground">Biểu đồ hiển thị 50 dòng đầu; xem bảng để đọc các dòng còn lại.</p>}
    </figure>
  );
}

export function StructuredResultView({ result }: { result: StructuredResult }) {
  const [visible, setVisible] = useState(25);
  const warnings = [...new Set(result.sources.flatMap((source) => source.warnings ?? []))];
  return (
    <section className="mt-4 space-y-3 rounded-xl border p-3" aria-label="Kết quả truy vấn Excel">
      <ResultChart result={result} />
      <div className="max-h-96 overflow-auto">
        <table className="w-full border-collapse text-left text-xs">
          <caption className="mb-2 text-left font-medium">Kết quả tính từ dữ liệu Excel · {result.rows.length} dòng</caption>
          <thead><tr>{result.columns.map((column) => <th key={column} scope="col" className="sticky top-0 border-b bg-background p-2">{column}</th>)}</tr></thead>
          <tbody>{result.rows.slice(0, visible).map((row, index) => <tr key={index}>{result.columns.map((column, i) => <td key={column} className="border-b p-2 align-top">{formatCell(row[i],column,result)}</td>)}</tr>)}</tbody>
        </table>
        {!result.rows.length && <p className="p-2 text-xs text-muted-foreground">Truy vấn không trả về dòng dữ liệu trong giới hạn hiện tại.</p>}
      </div>
      {result.rows.length > visible && <button type="button" className="text-xs underline" onClick={() => setVisible((value) => value + 50)}>Xem thêm dòng</button>}
      {result.truncated && <p role="status" className="text-xs text-amber-700 dark:text-amber-400">Kết quả hiển thị đã được giới hạn; chưa thể xem là toàn bộ các dòng/nhóm khớp truy vấn.</p>}
      <details className="text-xs text-muted-foreground">
        <summary className="cursor-pointer">Nguồn Excel và điều kiện truy vấn</summary>
        <ul className="mt-2 space-y-1">{result.sources.map((source) => <li key={source.dataset_id}>{source.file_name} · {source.sheet}!{source.range} · phiên bản {source.version.slice(0, 12)}</li>)}</ul>
        {warnings.length > 0 && <ul className="mt-2 list-inside list-disc">{warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
        <pre className="mt-2 overflow-auto whitespace-pre-wrap">{JSON.stringify(result.plan, null, 2)}</pre>
      </details>
    </section>
  );
}
