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

const fmt = (n: number) => n.toLocaleString("ko-KR") + "원";

export default function EstimateDetailPage() {
  const { id } = useParams();
  const [budget, setBudget] = useState<BudgetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch(`/api/estimates/${id}/budget`)
      .then((r) => r.ok ? r.json() : r.json().then((d) => Promise.reject(d.detail)))
      .then((data) => {
        setBudget(data);
        setExpanded(new Set(data.categories.map((c: BudgetCategory) => c.name)));
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (error) return (
    <div className="max-w-2xl mx-auto p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-300">
      오류: {error}
    </div>
  );

  if (!budget) return null;

  const toggle = (name: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/estimates" className="text-slate-400 hover:text-white text-sm">← 목록</Link>
        <h2 className="text-xl font-bold">{budget.site_name} — 실행예산</h2>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-sm">총 실행금액</p>
          <p className="text-2xl font-bold text-blue-400">{fmt(budget.total_amount)}</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-sm">항목 수</p>
          <p className="text-2xl font-bold">{budget.item_count}개</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-sm">공정 수</p>
          <p className="text-2xl font-bold">{budget.categories.length}개</p>
        </div>
      </div>

      {budget.obsidian_budget_path && (
        <div className="mb-6 p-3 bg-green-900/30 border border-green-700 rounded-lg text-green-300 text-sm">
          Obsidian 저장 완료: {budget.obsidian_budget_path}
        </div>
      )}

      <div className="space-y-3">
        {budget.categories.map((cat) => (
          <div key={cat.name} className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            <button
              onClick={() => toggle(cat.name)}
              className="w-full flex items-center justify-between p-4 hover:bg-slate-700/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="font-semibold">{cat.name}</span>
                <span className="text-slate-400 text-sm">{cat.item_count}개 항목</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-blue-400">{fmt(cat.subtotal)}</span>
                <span className="text-slate-400">{expanded.has(cat.name) ? "▲" : "▼"}</span>
              </div>
            </button>

            {expanded.has(cat.name) && (
              <div className="border-t border-slate-700 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-700/50">
                    <tr>
                      <th className="text-left p-3 text-slate-400">항목명</th>
                      <th className="text-left p-3 text-slate-400">규격</th>
                      <th className="text-right p-3 text-slate-400">수량</th>
                      <th className="text-right p-3 text-slate-400">단가</th>
                      <th className="text-right p-3 text-slate-400">합계</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cat.items.map((item) => (
                      <tr key={item.id} className="border-t border-slate-700/50 hover:bg-slate-700/30">
                        <td className="p-3">{item.name}</td>
                        <td className="p-3 text-slate-400">{item.specification}</td>
                        <td className="p-3 text-right">{item.quantity} {item.unit}</td>
                        <td className="p-3 text-right">{item.unit_price.toLocaleString("ko-KR")}</td>
                        <td className="p-3 text-right font-medium">{item.total_price.toLocaleString("ko-KR")}</td>
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
