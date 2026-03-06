import { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString("ru-RU");
}

function NumberBadge({ value }) {
  return <span className="badge">{value}</span>;
}

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [results, setResults] = useState([]);
  const [resultsTotal, setResultsTotal] = useState(0);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [loadingResults, setLoadingResults] = useState(false);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    in_stock: "",
    min_price: "",
    max_price: "",
    category: "",
    name_query: "",
    external_id: "",
    currency: "",
  });

  const selectedSession = useMemo(
    () => sessions.find((s) => s.id === Number(selectedSessionId)) ?? null,
    [sessions, selectedSessionId],
  );

  async function loadSessions() {
    setLoadingSessions(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/sessions?limit=500`);
      if (!res.ok)
        throw new Error(`Не удалось загрузить сессии: ${res.status}`);
      const data = await res.json();
      setSessions(data);
      if (data.length > 0 && !selectedSessionId) {
        setSelectedSessionId(data[0].id);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingSessions(false);
    }
  }

  async function loadResults(sessionId) {
    if (!sessionId) return;
    setLoadingResults(true);
    setError("");

    const params = new URLSearchParams({
      limit: "500",
      offset: "0",
      sort_by: "updated_at",
      sort_order: "desc",
    });

    if (filters.in_stock !== "") params.set("in_stock", filters.in_stock);
    if (filters.min_price) params.set("min_price", filters.min_price);
    if (filters.max_price) params.set("max_price", filters.max_price);
    if (filters.category) params.set("category", filters.category);
    if (filters.name_query) params.set("name_query", filters.name_query);
    if (filters.external_id) params.set("external_id", filters.external_id);
    if (filters.currency) params.set("currency", filters.currency);

    try {
      const res = await fetch(
        `${API_URL}/sessions/${sessionId}/results?${params.toString()}`,
      );
      if (!res.ok)
        throw new Error(`Не удалось загрузить результаты: ${res.status}`);
      const data = await res.json();
      setResults(data.items ?? []);
      setResultsTotal(data.total ?? 0);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingResults(false);
    }
  }

  useEffect(() => {
    loadSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [API_URL]);

  useEffect(() => {
    if (selectedSessionId) loadResults(selectedSessionId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSessionId]);

  function onFilterChange(key, value) {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div className="page">
      <header>
        <h1>Просмотр результатов</h1>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="layout">
        <section className="card sessions">
          <div className="space-between">
            <h2>
              Сессии <NumberBadge value={sessions.length} />
            </h2>
            <button onClick={loadSessions} disabled={loadingSessions}>
              {loadingSessions ? "Обновление..." : "Обновить"}
            </button>
          </div>

          {loadingSessions ? (
            <p>Загрузка сессий...</p>
          ) : sessions.length === 0 ? (
            <p>Сессии не найдены.</p>
          ) : (
            <ul>
              {sessions.map((s) => (
                <li
                  key={s.id}
                  className={Number(selectedSessionId) === s.id ? "active" : ""}
                >
                  <button onClick={() => setSelectedSessionId(s.id)}>
                    <strong>Сессия #{s.id}</strong>
                    <span>
                      Статус:{" "}
                      {s.status === "in_progress"
                        ? "В работе"
                        : s.status === "completed"
                          ? "Завершена"
                          : s.status === "failed"
                            ? "Ошибка"
                            : s.status}
                    </span>
                    <span>
                      Сайт: {s.site_id} | Пользователь: {s.user_id}
                    </span>
                    <span>Начало: {formatDate(s.started_at)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card results">
          <div className="results-header">
            <h2>
              Результаты{" "}
              {selectedSession && <span>для сессии #{selectedSession.id}</span>}{" "}
              <NumberBadge value={resultsTotal} />
            </h2>
            <button
              onClick={() => loadResults(selectedSessionId)}
              disabled={loadingResults || !selectedSessionId}
            >
              {loadingResults ? "Загрузка..." : "Обновить результаты"}
            </button>
          </div>

          <div className="filters">
            <label>
              В наличии
              <select
                value={filters.in_stock}
                onChange={(e) => onFilterChange("in_stock", e.target.value)}
              >
                <option value="">Любой</option>
                <option value="true">Да</option>
                <option value="false">Нет</option>
              </select>
            </label>
            <label>
              Мин. цена
              <input
                value={filters.min_price}
                onChange={(e) => onFilterChange("min_price", e.target.value)}
              />
            </label>
            <label>
              Макс. цена
              <input
                value={filters.max_price}
                onChange={(e) => onFilterChange("max_price", e.target.value)}
              />
            </label>
            <label>
              Категория
              <input
                value={filters.category}
                onChange={(e) => onFilterChange("category", e.target.value)}
              />
            </label>
            <label>
              Название содержит
              <input
                value={filters.name_query}
                onChange={(e) => onFilterChange("name_query", e.target.value)}
              />
            </label>
            <label>
              Внешний ID
              <input
                value={filters.external_id}
                onChange={(e) => onFilterChange("external_id", e.target.value)}
              />
            </label>
            <label>
              Валюта
              <input
                value={filters.currency}
                onChange={(e) => onFilterChange("currency", e.target.value)}
                placeholder="RUB"
              />
            </label>
            <button
              className="apply"
              onClick={() => loadResults(selectedSessionId)}
              disabled={!selectedSessionId || loadingResults}
            >
              Применить фильтры
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Сайт</th>
                  <th>Внешний ID</th>
                  <th>Название</th>
                  <th>Категория</th>
                  <th>Цена</th>
                  <th>Старая цена</th>
                  <th>Валюта</th>
                  <th>В наличии</th>
                  <th>Обновлено</th>
                </tr>
              </thead>
              <tbody>
                {results.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="empty">
                      Нет данных
                    </td>
                  </tr>
                ) : (
                  results.map((item) => (
                    <tr key={item.id}>
                      <td>{item.id}</td>
                      <td>{item.site_id}</td>
                      <td>{item.external_id ?? "—"}</td>
                      <td>{item.name}</td>
                      <td>{item.category ?? "—"}</td>
                      <td>{item.price}</td>
                      <td>{item.old_price ?? "—"}</td>
                      <td>{item.currency}</td>
                      <td>{item.in_stock ? "Да" : "Нет"}</td>
                      <td>{formatDate(item.updated_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
