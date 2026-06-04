"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface BudgetItem {
  id: number;
  name: string;
  specification: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  classification_confidence: number;
}

interface BudgetCategory {
  name: string;
  subtotal: number;
  item_count: number;
  items: BudgetItem[];
}

interface BudgetData {
  estimate_id: number;
  site_name: string;
  total_amount: number;
  item_count: number;
  categories: BudgetCategory[];
  obsidian_budget_path: string | null;
}

const fmt = (n: number) => `${n.toLocaleString("ko-KR")}원`;

export default function EstimateDetailPage() {
  const { id } = useParams();
  const [budget, setBudget] = useState<BudgetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch(`/api/estimates/${id}/budget`)
      .then((r) => (r.ok ? r.json() : r.json().then((d) => Promise.reject(d.detail))))
      .then((data) => {
        setBudget(data);
        setExpanded(new Set(data.categories.map((c: BudgetCategory) => c.name)));
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl rounded-lg border border-red-700 bg-red-900/50 p-4 text-red-300">
        오류: {error}
      </div>
    );
  }

  if (!budget) return null;

  const toggle = (name: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex items-center gap-3">
        <Link href="/estimates" className="text-sm text-slate-400 hover:text-white">
          목록
        </Link>
        <h2 className="text-xl font-bold">{budget.site_name} 실행예산</h2>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-4">
          <p className="text-sm text-slate-400">총 실행금액</p>
          <p className="text-2xl font-bold text-blue-400">{fmt(budget.total_amount)}</p>
        </div>
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-4">
          <p className="text-sm text-slate-400">항목 수</p>
          <p className="text-2xl font-bold">{budget.item_count}개</p>
        </div>
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-4">
          <p className="text-sm text-slate-400">공정 수</p>
          <p className="text-2xl font-bold">{budget.categories.length}개</p>
        </div>
      </div>

      {budget.obsidian_budget_path && (
        <div className="mb-6 rounded-lg border border-green-700 bg-green-900/30 p-3 text-sm text-green-300">
          Obsidian 저장 완료: {budget.obsidian_budget_path}
        </div>
      )}

      <div className="space-y-3">
        {budget.categories.map((cat) => (
          <div key={cat.name} className="overflow-hidden rounded-xl border border-slate-700 bg-slate-800">
            <button
              onClick={() => toggle(cat.name)}
              className="flex w-full items-center justify-between p-4 transition-colors hover:bg-slate-700/50"
            >
              <div className="flex items-center gap-3">
                <span className="font-semibold">{cat.name}</span>
                <span className="text-sm text-slate-400">{cat.item_count}개 항목</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-blue-400">{fmt(cat.subtotal)}</span>
                <span className="text-slate-400">{expanded.has(cat.name) ? "접기" : "펼치기"}</span>
              </div>
            </button>

            {expanded.has(cat.name) && (
              <div className="overflow-x-auto border-t border-slate-700">
                <table className="w-full text-sm">
                  <thead className="bg-slate-700/50">
                    <tr>
                      <th className="p-3 text-left text-slate-400">항목명</th>
                      <th className="p-3 text-left text-slate-400">규격</th>
                      <th className="p-3 text-right text-slate-400">수량</th>
                      <th className="p-3 text-right text-slate-400">단가</th>
                      <th className="p-3 text-right text-slate-400">합계</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cat.items.map((item) => (
                      <tr key={item.id} className="border-t border-slate-700/50 hover:bg-slate-700/30">
                        <td className="p-3">{item.name}</td>
                        <td className="p-3 text-slate-400">{item.specification}</td>
                        <td className="p-3 text-right">
                          {item.quantity} {item.unit}
                        </td>
                        <td className="p-3 text-right">{fmt(item.unit_price)}</td>
                        <td className="p-3 text-right font-medium">{fmt(item.total_price)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
